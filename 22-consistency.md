# 22 原文與向量一致性：兩段文件一起更新

> **定位**：把模型計算放在交易外，進交易後鎖定並檢查版本，完整更新兩段文字、hash、向量與文件版本。

[上一節](21-filters-evaluation.md) · [下一節](23-integration.md)


## 學習目標

- 找出「文字已變、向量未變」及「只更新其中一段」的問題。
- 以 expected_version 搭配 SELECT FOR UPDATE 防止過期提交覆蓋新版本。
- 證明成功完整提交，失敗與 stale version 完整回滾。

## 範例程式碼

- [交易實作 update_document](vector_course.py)、[唯讀一致性 SQL](demo/22-consistency.sql)。
- [成功／失敗／還原測試](demo/24-acceptance.py)、[本節解答](workshop/22-consistency.md)。
- [模組作業](homework/22-search.md)。

---

## 情境

教師在 D001 加上操作紀錄與失敗回報要求。若只 UPDATE C001.text，搜尋仍可能使用舊向量；若 C001 已是版本 2、C002 還是版本 1，兩段內容不能再被視為同一份完整文件。你要更新的是整份 document，不是一個欄位。

先修 checkpoint：原始版本 1、16 個向量一致，Q01～Q08 baseline 評估已保存。artifact 有 D001 的兩段新原文與已實際 encode 的向量。請使用課堂隔離库，先在失敗注入測試後才做成功提交。

---

## 講解

### 1. 定義必須一起成立的條件

同一 document 的兩個 chunks 與各自 vectors 必須具有相同 source_version；chunk 的 `content_hash=SHA256(UTF-8 text)`，vector 的 content_hash 必須相同。模型 ID、revision、preprocessing_id 也不能混用。

這些條件是應用程式的交易不變條件，不會只靠外鍵自動成立。外鍵能保證 chunk 存在，卻不知道向量是不是對應新版文字。所有寫入入口應遵守同一更新协议；直接手改 SQL 可能破壞它，`check` 會拒絕後續檢索。

### 2. 慢計算在外，短交易在內

完整流程：

```text
讀取待編輯版本 1
準備兩段新全文 -> encode 兩個向量 -> 驗證維度與 norm
BEGIN
鎖定 document -> 核對目前版本仍是 expected_version=1
鎖定該文件所有 chunks -> 核對恰好包含兩段
更新 chunk1 + vector1
更新 chunk2 + vector2
更新 document version=2 -> 檢查不變條件
COMMIT；任一步失敗 ROLLBACK
```

把 encode 放進鎖定交易會讓其他編輯者等待模型下載或 CPU 計算，因此先算完。但在交易外查到的版本可能已過期，必須在取得鎖後重新核對：

```python
cursor.execute(
    "SELECT source_version FROM documents WHERE document_id=? FOR UPDATE",
    (document_id,))
row = cursor.fetchone()
if row is None or row[0] != expected_version:
    raise VersionConflict("document version changed or document does not exist")
```

不能把這個 SELECT 移到 BEGIN 前，也不能只在畫面顯示版本而不驗證。兩個編輯者都帶版本 1 時，先取得鎖且成功提交的人變成 2；後取得鎖的人讀到 2，整筆拒絕，重新讀新文件再編輯。

### 3. 先故意失敗，確認沒有半套資料

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/22-consistency.sql
python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --document D001 --expected-version 1 --fail-after-first
python vector_course.py check
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/22-consistency.sql
```

第二個指令應非零退出，原因為 `injected failure after first chunk/vector write`。這不是輸入驗證提早擋下：它確實已在交易內寫入第一段及第一個向量，才故意拋錯。前後兩段的文字、hash、向量 bytes 及全部版本應完全相同；只看 `check=true` 不足以證明內容沒被替換，驗收腳本會比對快照。

`course_db.connect()` 的 autocommit=True 不表示多句 SQL 自動是一個交易。程式明確 `conn.begin()`；在 except 中 rollback，成功才 commit。API 要求空閒的 autocommit 連線，避免無意間提交呼叫者未完成的工作。

### 4. 成功更新與 stale 拒絕

```bash
python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --document D001 --expected-version 1
python vector_course.py check
python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --document D001 --expected-version 1
```

第一次成功回傳 `source_version=2`、chunks C001／C002；第二次舊版本 1 必須 `VersionConflict`，不能把它當成「重跑成功」。成功後再執行第 21 節 evaluate 也應拒絕，因为 qrels 是 baseline 版本 1。

呼叫 Python API 可選擇即時 encode；下面完整示範的是明示預計算，務必只在版本 1 checkpoint 執行一次：

```python
from pathlib import Path
from course_db import connect
from embedding_course import load_artifact
from vector_course import update_document
a = load_artifact(Path.home() / "mariadb-vectors.json")
texts = {c["chunk_id"]: c["text"] for c in a["updates"]["D001"]["chunks"]}
conn = connect()
try:
    print(update_document(conn, "D001", 1, texts, prepared=a))
finally:
    conn.close()
```

新文字不在 artifact 時 prepared 模式明確拒絕；移除 `prepared=a` 並傳入 `encoder=Encoder(offline=True)` 才是重新 encode。恢復原文也要經同一交易，從版本 2 變成 3，不倒退成 1。可重用原文已記錄的向量，因模型與文字完全相同；新的來源版本仍是 3。

---

## Workshop

### 題目

前後快照 失敗及成功 stale 拒絕。

1. 在版本 1 注入寫入第一段後失敗，確認全部回滾。
2. 成功更新兩段，再用同一 expected_version=1 重送，確認拒絕且版本仍為 2。
3. 解釋若另一位同學在 encode 期間先提交，你的版本檢查為何仍有效。

### 預期輸出

```text
注入失敗後：D001/C001/C002/vector 的版本仍為 1，内容與 bytes 未變
成功後：以上版本全部為 2，兩段新文字與 hash 正確
stale 重送：VersionConflict，快照不變
```

只有印出例外、没有核對資料，不算通過。錯誤發生在連線或 artifact 讀取也不算交易 rollback 證據。

### 解答

[22 Workshop 解答](workshop/22-consistency.md)，以及 [Homework 22](homework/22-search.md)。24 的完整驗收需另用初始版本 1 checkpoint，不能直接在本節已更新的資料上重跑。

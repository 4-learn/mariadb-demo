# 23 串接 CLI：可追溯的候選檢索工具

> **定位**：把私人連線設定、模型或固定向量、SQL 篩選與原文輸出串成完整命令列，不把候選包裝成模型已確認的答案。

[上一節](22-consistency.md) · [下一節](24-acceptance.md)


## 學習目標

- 從輸入問題一路追蹤到 embedding、SQL、原文與版本。
- 正確選擇 live-model 或 recorded-query，不做隱藏 fallback。
- 處理私人設定、資源關閉、空結果與操作失敗。

## 範例程式碼

- [小型完整 CLI](demo/23-integration.py)、[功能完整 CLI](vector_course.py)。
- [模型／artifact 程式](embedding_course.py)、[本節解答](workshop/23-integration.md)。

---

## 情境

你已能手動查 SQL，現在要讓同學輸入問題就看到合格 SOP 候選。工具必須說清楚資料從哪裡來、對應哪版原文；如果沒有符合文件，不能假装正在「思考」後生成設備操作。

先修 checkpoint：Python 能用私人 JSON 連線到 workshop，`check` 通過。可在 22 更新後的版本 2 或恢復版本 3 檢索，但 baseline evaluate 僅可在版本 1 執行。query 的固定向量可以重用，qrels 的有效性不可混為一談。

---

## 講解

### 1. 輸入、處理、輸出的邊界

```text
recorded case ID -> 驗 artifact metadata/hash -> 固定 query 向量
新 query 原文 -> 固定 revision 的真實 encode -> 新 query 向量
向量 + category + k -> 驗 DB 一致性 -> 合格集合 -> 精確距離排序
chunk_id/document_id/source_version/text/distance -> JSON 候選輸出
```

程式不載入生成式 LLM，不產生摘要、不推薦真實設備操作。輸出的 distance 是檢索訊號，使用者仍要檢查產品型號、版本、否定與實際需求。P010 沒 SOP，即使找出 C001，也不能據此回答感測器 H 的步驟。

### 2. 私人連線檔不進命令列密碼

前面建立的 app JSON 具有 user、password、database、unix_socket，權限 0600。database 固定 `mariadb_workshop_2026`，只走實際本機 socket，不改成公開 TCP。預設 `course_db.connect()` 讀 `COURSE_DB_CONFIG` 或 `~/mariadb-course-app.json`。

```bash
python vector_course.py --config "$HOME/mariadb-course-app.json" check
python demo/23-integration.py --config "$HOME/mariadb-course-app.json" --artifact "$HOME/mariadb-vectors.json" --case Q01
```

主 CLI 的全域 `--config` 放在子命令前；demo 是單一命令，位置不同。不要把 JSON 內容、完整連線例外或密碼貼進作業。需要分享錯誤時只保留操作、必要錯誤類型與不敏感的狀態。

### 3. 小程式如何組合既有功能

```python
from pathlib import Path
from course_db import connect
from embedding_course import load_artifact
from vector_course import recorded_query, search
a = load_artifact(Path.home() / "mariadb-vectors.json")
case, vector = recorded_query(a, "Q01")
conn = connect()
try:
    rows = search(conn, vector, k=3, category_id=case["category_id"])
    for row in rows:
        print(row["chunk_id"], row["source_version"], row["distance"])
        print(row["text"])
finally:
    conn.close()
```

`load_artifact` 先驗來源、模型、hash 與維度；`recorded_query` 只接受存在的 case ID；`search` 驗證資料庫一致性，使用參數化 SQL。`finally` 確保即使查詢拋例外也關閉連線。

CLI 回傳 JSON 包含 embedding mode 與 metadata，讓教師分辨這次有沒有跑模型。它不是從文字看起來像 Q01 就偷用 Q01 向量。不存在的 Q99 必須失敗，而不是抓第一筆固定向量。

### 4. 新問題與無答案

```bash
python vector_course.py search --query '教學感測器 G 上傳逾時時應先查什麼？' --offline --category 1 --k 3
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q03 --k 3
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q08 --k 3
```

第一句真實 encode 新 query；離線快取不完整就失敗，不換模型。第二句的分類 2 有兩段否定 5 GHz 支援的候選，不能把它們變成肯定答案。第三句 category 999 無合格文件，輸出 rows 為空。

可用 `--category 3` 覆寫 recorded query 的分類做練習，輸出會顯示實際 filter；但這時不得再用原 qrels 算分。模型向量表示同一問題，業務篩選改變了可用集合，人工標註也要跟著重新檢查。

預設 `--mode exact`；ANN 是第 20 節顯式選項。`--explain` 回的是計畫，不是原文 rows，介面不能把 EXPLAIN 裡的 table 欄位顯示成搜尋命中。

---

## Workshop

### 題目

固定模式 新問題或離線拒絕 空結果／型號檢查。

1. 執行 demo Q01，核對 metadata、原文與版本。
2. 有模型快取者執行新 query；沒有者明示只能完成固定模式，保留不可偽裝 live-model 的說明。
3. 執行 Q05 與 Q08，分別說明「有候選但沒有適用型號答案」及「篩選後零候選」。
4. 嘗試 `--case Q99`，確認明確拒絕，沒有產生查詢結果。

### 預期輸出

```text
recorded-query：顯示真實 case 原文與 artifact 來源
live-model：只有實際 encode 才可標記
Q08：rows=[]
Q99：unknown case ID；非零退出
所有候選均附 chunk_id/document_id/source_version/text/distance
```

### 解答

[23 Workshop 解答](workshop/23-integration.md)。API 正常回傳只代表串接完成；不代表模型品質、拒答能力或真实设备安全已驗證。

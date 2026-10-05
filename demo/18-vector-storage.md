# 18 向量入庫：原文與座標必須能對得起來

> **定位**：用 `VECTOR(512)` 儲存真實向量，透過參數化 `VEC_FromText` 與 metadata 阻止錯誤混入。

[上一節](17-embedding.md) · [下一節](19-vector-ranking.md)


## 學習目標

- 區分 JSON 傳輸形式與 MariaDB 的 VECTOR 欄位。
- 用主鍵／外鍵把每個 chunk 對應到一筆向量。
- 說明維度、模型版本、原文 hash 與來源版本各防止哪種錯誤。

## 範例程式碼

- [建表 SQL](demo/18-vector-storage.sql)、[入庫與檢查程式](vector_course.py)。
- [Artifact 驗證](embedding_course.py)、[本節解答](workshop/18-vector-storage.md)。

---

## 情境

你已計算 16 段 SOP 的向量。如果只把數字塞進一個 TEXT 欄位，之後找不到它來自哪段文字、哪個模型，原文更新時也不知道要重算哪筆。現在要把「向量」放回產品／文件／段落的關聯架構。

先修 checkpoint：MariaDB **11.8.9**、Connector/Python **1.1.14**；workshop 的 sop-v1 仍是 8 文件／16 段／版本 1，尚未有 chunk_vectors。第 17 節 artifact 已驗證；app 私人 JSON 可由 `course_db.connect()` 連 socket，autocommit=True。不使用 01～03 的 reader 庫。

---

## 講解

### 1. 一個 chunk 對一筆向量

```sql
CREATE TABLE chunk_vectors (
  chunk_id VARCHAR(16) PRIMARY KEY,
  source_version INT NOT NULL,
  content_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  model_id VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  model_revision CHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  preprocessing_id VARCHAR(80) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  embedding VECTOR(512) NOT NULL,
  FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
) ENGINE=InnoDB;
```

主鍵使 C001 不能有兩筆向量；外鍵阻止不存在的 chunk_id。`VECTOR(512)` 固定元素數，`NOT NULL` 排除尚未計算的空值。但資料型別不知道文字是否更新，或 512 維是不是別的模型產生，因此 metadata 不能省。

本課只支援一個固定模型集合，不實作多模型並存。若未來換模型，應設計完整重建／切換流程，而不是在同一欄位塞入新舊模型。

### 2. 建表與使用表的權限分開

建表用 editor；這段與上方概念建表二擇一，實際以配套 SQL 為準，不能重複建立：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/18-vector-storage.sql
```

執行前確認檔案 0600 與庫名。已有表就請教師核對 checkpoint，不加 `IF NOT EXISTS` 隱藏結構不符，也不要求 app 用 root。DDL 有隱含 commit，不能拿後面的 rollback 当成建表復原方案。此時刻意**尚不建向量索引**，先建立第 19 節精確對照。

### 3. JSON 是值，不是 SQL 字串拼接

Python list 不能直接當作 SQL 的 512 個欄位。我們將它序列化成一個 JSON array 字串，再讓 `VEC_FromText(?)` 轉成 VECTOR：

```python
import json
from course_db import connect
from embedding_course import load_artifact
a = load_artifact("/home/student/mariadb-vectors.json")
c = a["chunks"][0]
conn = connect()
cur = conn.cursor()
try:
    cur.execute("SELECT VEC_DISTANCE_COSINE(VEC_FromText(?), VEC_FromText(?))",
                (json.dumps(c["embedding"]), json.dumps(c["embedding"])))
    print(cur.fetchone())
finally:
    cur.close()
    conn.close()
```

把 `/home/student/...` 改為你自己的實際檔案；命令列例子可用 `$HOME`，Python 字串不自動展開 shell 變數。上例沒有寫入，只驗證同一個真實向量距離接近 0。正式 INSERT 的核心是：

```python
cur.execute("""INSERT INTO chunk_vectors
  (chunk_id,source_version,content_hash,model_id,model_revision,preprocessing_id,embedding)
  VALUES (?,?,?,?,?,?,VEC_FromText(?))""", values)
```

`values` 是七個值的 tuple，最後一項才是向量 JSON。完整可執行實作見 `_write_vector`；不以 f-string 將問題、原文或數字串入 SQL。Connector 1.1.14 使用 `?` 參數標记。

### 4. 先驗來源，再一次入庫

```bash
python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"
python vector_course.py check
```

`ingest` 在交易中鎖定文件及 chunks，比對 DB 的 title、status、text、版本、hash、產品關聯與 artifact 的完整 baseline。它也要求 chunk_vectors 為空。全部 16 筆成功才 commit，任何一步失敗都 rollback；重複執行不偷偷覆蓋。

`check` 逐段比對 document／chunk／vector 版本相同、SHA2(text,256) 與兩份 hash 一致、固定模型 metadata 一致，最後確認 16 筆。資料庫只存來源 hash，無法靠 hash 證明某向量確實由模型算出，因此 artifact 的信任來源與第 17 節 provenance 仍重要。

```sql
SELECT COUNT(*) AS vectors FROM chunk_vectors;
SELECT c.chunk_id,c.source_version,v.source_version,
       c.content_hash=SHA2(c.text,256) AS text_ok,
       BINARY c.content_hash=BINARY v.content_hash AS vector_source_ok
FROM chunks c JOIN chunk_vectors v ON v.chunk_id=c.chunk_id
ORDER BY c.chunk_id;
```

應有 16 列，各版本 1、兩個布林欄位皆 1。16 筆只是完整性條件，不代表排名品質已通過。

---

## Workshop

### 題目

建表核對 入庫 錯誤分類。

1. 用 editor 建表，用 app 入庫；記錄各自角色，不貼私人設定。
2. 核對 16 筆與 hash／version，解釋為何不能只有 `embedding` 一欄。
3. 再執行一次 ingest，確認被「非空 checkpoint」拒絕，筆數及 hash 未變。

### 預期輸出

```text
首次 ingest: inserted=16
check: consistent=true, chunks=16
再次 ingest: 拒絕覆蓋，原資料仍完整
```

維度 511、revision 不符或原文不同應在寫入前被拒絕。`ERROR 1142` 建表權限錯誤不等於維度驗收成功；找不到表也不等於安全拒絕。先修復正確 checkpoint，再重測指定條件。

### 解答

[18 Workshop 解答](workshop/18-vector-storage.md)。不要為了讓筆數通過而補假向量或跳過 provenance。

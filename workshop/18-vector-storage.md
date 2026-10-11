# 18 向量入庫 Workshop

## 情境

你要把 16 個已算好的向量與原文建立一對一關係，並證明重跑不覆蓋資料。

### 專案背景

前面已建立 documents／chunks；向量表由 editor 建立，app 只入庫。起點是版本 1，且 chunk_vectors 尚不存在。

### 使用者需求

> 「我不只要看到有 16 筆數字，也要知道每筆仍對應現在這段文字。」

### 你的任務

1.核對帳號／建表入庫重跑拒絕及說明。
2. 核對各版本、hash 與模型 metadata。
3. 用同一 artifact 重跑 ingest，確認沒有偷偷覆蓋。

### 技術需求

- `VECTOR(512) NOT NULL`、chunk_id PK／FK。
- JSON array 作一個參數交給 `VEC_FromText(?)`，不是 SQL 拼接。
- 不授予 app DDL 權限；不使用 root。

## 輸入資料格式

每個 artifact chunk 含 chunk_id、document_id、source_version、text、content_hash、embedding，模型 metadata 放在頂層。

## 輸出示例

```text
inserted: 16
consistent: true
第二次 ingest: chunk_vectors is not empty
```

## 你需要實作的功能

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/18-vector-storage.sql
python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"
python vector_course.py check
```

### 提示

只在乾淨起點建表一次。第二次 ingest 是預期失敗，分開執行，不用命令串忽略錯誤。DDL 本身不屬於 ingest 的 rollback 範圍。

## 解答

```sql
SELECT COUNT(*) AS n FROM chunk_vectors;
SELECT c.chunk_id
FROM chunks c JOIN chunk_vectors v ON v.chunk_id=c.chunk_id
JOIN documents d ON d.document_id=c.document_id
WHERE c.source_version<>d.source_version
   OR c.source_version<>v.source_version
   OR BINARY c.content_hash<>BINARY SHA2(c.text,256)
   OR BINARY c.content_hash<>BINARY v.content_hash;
```

第一句應 16，第二句零列。`vector_course.py check` 另外驗模型 metadata，不可只看 SQL 零列就認定模型相同。

维度錯誤由 `validate_vector` 擋下；存在但不是同一模型的 512 維向量，靠 metadata 契約擋下；原文被修改，靠 hash／baseline 比對擋下。外鍵只解決「段落是否存在」，不能代替這三件事。

重跑拒絕後再執行 check 和 SQL，應與原來相同。若重跑把某些向量改掉，即使最後仍 16 筆也失敗。

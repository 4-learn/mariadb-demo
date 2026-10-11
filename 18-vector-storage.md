# 18 向量入庫：原文與座標必須能對得起來

> 本章完全使用 MariaDB client 與 SQL，不需要 Python。教師提供預計算的 512 維向量，學生練習建表、入庫與驗證。

## 1. 建立 VECTOR 表

使用 editor 執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/18-vector-storage.sql
```

核心欄位：

```text
chunk_id、source_version、content_hash
model_id、model_revision、preprocessing_id
embedding VECTOR(512)
```

## 2. 載入教師預計算向量

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/18-vector-ingest.sql
```

檔案使用 `VEC_FromText` 將 JSON array 轉成 VECTOR。學生不需手動輸入 512 個數字。

## 3. 驗證原文與向量 metadata

```sql
SELECT COUNT(*) AS vector_count FROM chunk_vectors;

SELECT c.chunk_id,
       c.source_version,
       v.source_version,
       SHA2(c.text,256) = v.content_hash AS hash_ok,
       v.model_id, v.model_revision
FROM chunks AS c
JOIN chunk_vectors AS v ON v.chunk_id = c.chunk_id
ORDER BY c.chunk_id;
```

預期共有 16 筆，而且版本與 hash 對得上。

> 向量是教師課前預計算資料；MariaDB 本身不負責執行 embedding 模型。

## Workshop

1. 建立 `chunk_vectors`。
2. 載入 `demo/18-vector-ingest.sql`。
3. 確認 vector_count = 16。
4. 確認 `SHA2(text,256) = content_hash` 且 model metadata 一致。

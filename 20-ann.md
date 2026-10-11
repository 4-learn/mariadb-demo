# 20 ANN：向量索引是近似候選，不是正確答案

> 本章完全使用 MariaDB client 與 SQL，不需要 Python。學生建立 VECTOR INDEX，查看 EXPLAIN，並把 ANN 結果和 exact 結果比較。

## 學習目標

- 分辨 VECTOR INDEX 與一般 B-tree 索引。
- 建立 cosine 向量索引。
- 用 EXPLAIN 確認查詢是否採用向量索引。
- 知道 ANN 是近似候選，不保證等於完整精確排序。

## 1. 建立向量索引

確認 Ch18 已載入 16 筆 `chunk_vectors`，使用 editor 執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/20-ann.sql
```

SQL 會執行：

```sql
ALTER TABLE chunk_vectors
    ADD VECTOR INDEX vector_idx (embedding) M=6 DISTANCE=cosine;
SHOW INDEX FROM chunk_vectors;
```

這是 DDL，會產生 implicit commit；索引已存在時不要重複執行。

## 2. 用 Q01 查詢向量觀察 ANN

Q01 是教師預先產生的 query vector。SQL 會把它放入 `@q`，再執行：

```sql
EXPLAIN
SELECT chunk_id, VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors FORCE INDEX (vector_idx)
ORDER BY distance ASC LIMIT 3;
```

`FORCE INDEX` 只是在本次實驗要求使用指定索引；是否真的採用，要看 EXPLAIN 的 `key`。不要把它當成正式系統必加的語法。

## 3. 和 exact 結果比較

精確查詢要繞過向量索引，並保存兩組 `chunk_id`：

```sql
SET @q = (SELECT embedding FROM query_vectors WHERE case_id='Q01');
SELECT chunk_id, VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors IGNORE INDEX (vector_idx)
ORDER BY distance ASC, chunk_id ASC LIMIT 3;
```

兩組結果相同，只能說明這個 checkpoint、這個 Q01、這個 k 的候選相同；不能宣稱 ANN 一定正確或一定更快。

## Workshop

1. 建立 `vector_idx`，保存 `SHOW INDEX`。
2. 執行 `demo/20-ann.sql`，保存 ANN 的 EXPLAIN 與前三筆結果。
3. 執行 exact 查詢，保存前三筆結果。
4. 比較兩組 `chunk_id` 的交集。
5. 說明小資料集不能證明正式效能。

本章不執行 Python，也不在資料庫內產生新的 embedding。

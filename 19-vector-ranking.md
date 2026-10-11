# 19 精確 Top-K：先把每一筆距離算清楚

> 本章完全使用 MariaDB client 與 SQL，建立精確 cosine distance 查詢，作為後續 ANN 的基準。

## 1. 自我查詢與距離

執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/19-vector-ranking.sql
```

查詢使用教師預計算的 Q01 向量：

```sql
SET @q = (SELECT embedding FROM query_vectors WHERE case_id = 'Q01');
```

距離越小越相似：

```sql
VEC_DISTANCE_COSINE(v.embedding, @q)
```

排序使用：

```sql
ORDER BY distance ASC, chunk_id ASC
```

第一排序鍵是距離；第二排序鍵確保同距離時順序穩定。

## 2. 加入資格條件

查詢只保留 active 文件、active 產品與指定分類，並用 `EXISTS` 避免同一段落因多個產品重複出現。

```text
先過濾合格集合，再排序取前三筆
```

## 3. EXPLAIN

檔案也會輸出 `EXPLAIN`。它描述 MariaDB 預計如何執行查詢，不是實際查詢結果。

## Workshop

1. 執行 `demo/19-vector-ranking.sql`。
2. 保存前三筆結果與 distance。
3. 說明為什麼距離要升冪排序。
4. 說明為什麼需要 `chunk_id` 作為第二排序鍵。
5. 查看 EXPLAIN，區分執行計畫與查詢結果。

本章只查固定的 Q01；新的自然語言問題需要教師先產生並審核新的預計算向量。

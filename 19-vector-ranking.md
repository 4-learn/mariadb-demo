# 19 精確 Top-K：先把每一筆距離算清楚

> **定位**：以 Ch5–9 的 SELECT、WHERE、ORDER BY、LIMIT，加上 18 的向量表，建立可重現的精確基準；ANN 尚未是本章答案。

[上一節](18-vector-storage.md) · [下一節](20-ann.md)

## 學習目標

- 分辨 cosine distance（小較近）與 similarity（大較近）。
- 先形成合格集合，再以 distance ASC、chunk_id ASC 排序。
- 保存實際 EXPLAIN，不能用 ANN 結果冒充精確基準。

## 1. 先用 SQL 驗證排序方向

```sql
SET @q=(SELECT embedding FROM chunk_vectors WHERE chunk_id='C001');
SELECT chunk_id, VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors
ORDER BY distance ASC, chunk_id ASC LIMIT 3;
```

C001 自我查詢距離應接近 0；這不是把 C001 假裝成使用者問題。SQL 沒有 ORDER BY 時不保證順序。

## 2. Code section：完成精確查詢（Python 可選）

```python
from course_db import connect
from embedding_course import load_artifact, recorded_query

artifact = load_artifact("$HOME/mariadb-vectors.json")
case, query_vector = recorded_query(artifact, "Q01")
# TODO 1：以 query_vector 執行課程的 exact search，category 與 k 固定。
rows = None
# TODO 2：列出每列的 chunk_id、distance，並確認排序鍵。
for row in rows:
    print(row["chunk_id"], row["distance"])
```

提示：使用 `vector_course.search(..., mode='exact', category_id=case['category_id'], k=3)`；正式 SQL 需 active document/product 的 EXISTS 條件，不能只算所有向量。

## 3. 執行、驗證、交付

```bash
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode exact --k 3 --explain
```

驗證每列為合格且不重複，排序為 `(distance ASC, chunk_id ASC)`；EXPLAIN 不得使用 `vector_idx`（若已存在，程式應用 `IGNORE INDEX`）。top-k 只是候選，不代表答案正確。

## 交件

交付 SQL 自我查詢、code section、Q01 實際 IDs／距離／原文、EXPLAIN 與對「距離不是正確率」的說明。不手動重排或修改 qrels。

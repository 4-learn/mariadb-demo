# 19 精確 Top-K：先把每一筆距離算清楚

> **概念**：計算查詢向量與文件向量的 cosine distance，依距離由近到遠找出精確 Top-K。

[上一節](18-vector-storage.md) · [下一節](20-ann.md)

## 1. SQL 自我檢查

```sql
SET @q=(SELECT embedding FROM chunk_vectors WHERE chunk_id='C001');
SELECT chunk_id, VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors ORDER BY distance ASC, chunk_id ASC LIMIT 3;
```

C001 自我距離應接近 0，且排序鍵明確。

## 2. 完整可執行 code section

```python
import os
from pathlib import Path
from embedding_course import load_artifact
from course_db import connect
from vector_course import recorded_query, search

artifact = load_artifact(Path(os.environ.get("VECTOR_ARTIFACT", str(Path.home()/"mariadb-vectors.json"))))
case, query_vector = recorded_query(artifact, "Q01")
with connect() as conn:
    rows = search(conn, query_vector, k=3, category_id=case["category_id"], mode="exact", explain=False)
for row in rows:
    print(row["chunk_id"], row["distance"])
assert len({row["chunk_id"] for row in rows}) == len(rows)
assert all(rows[i]["distance"] <= rows[i+1]["distance"] for i in range(len(rows)-1))
```

## 3. 固定 Agent prompt

> 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，把完整程式寫入 `/tmp/ch19_ranking.py` 後執行；不得 placeholders、手動重排、改 qrels 或讀 HackMD/repos。回報實際輸出與 exit code。

## 4. 執行、EXPLAIN 與驗收

```bash
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch19_ranking.py; rc=$?; echo "exit_code=$rc"
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode exact --k 3 --explain; rc=$?; echo "exit_code=$rc"
```

保留 EXPLAIN；exact 不得以 `vector_idx` 冒充 ANN。交件附 SQL 自我查詢、Q01 實際 IDs／距離／原文、plan 與 exit code，並說明 distance 不等於答案正確率。

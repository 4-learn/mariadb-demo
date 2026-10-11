# 20 ANN：索引是近似候選，不是正確答案

> **概念**：B-tree 做條件查找，VECTOR INDEX 做近似鄰近搜尋。ANN 必須以 exact 結果作對照；16 筆資料不能宣稱效能優勢。

[上一節](19-vector-ranking.md) · [下一節](21-filters-evaluation.md)

## 1. 建索引並核對

```sql
ALTER TABLE chunk_vectors ADD VECTOR INDEX vector_idx (embedding) M=6 DISTANCE=cosine;
SHOW INDEX FROM chunk_vectors;
```

只在乾淨 checkpoint 建一次；DDL 會 commit。已存在或失敗時停下記錄，不刪建重來。

## 2. 完整可執行 code section

```python
import os
from pathlib import Path
from embedding_course import load_artifact, recorded_query
from course_db import connect
from vector_course import search

artifact = load_artifact(Path(os.environ.get("VECTOR_ARTIFACT", str(Path.home()/"mariadb-vectors.json"))))
case, vector = recorded_query(artifact, "Q01")
with connect() as conn:
    exact = search(conn, vector, k=3, category_id=case["category_id"], mode="exact", explain=True)
    ann = search(conn, vector, k=3, category_id=case["category_id"], mode="ann", explain=True)
print("exact =", [r["chunk_id"] for r in exact])
print("ann =", [r["chunk_id"] for r in ann])
exact_ids = {r["chunk_id"] for r in exact}
print("intersection_fraction =", len(exact_ids & {r["chunk_id"] for r in ann}) / len(exact_ids) if exact_ids else None)
```

## 3. 固定 Agent prompt

> 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，將完整程式存為 `/tmp/ch20_ann.py` 並執行；不得 placeholders、改 query/k、捏造 plan 或讀 HackMD/repos。回報兩組 stdout、stderr 與 exit code。

## 4. 執行與驗收

```bash
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch20_ann.py; rc=$?; echo "exit_code=$rc"
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode exact --k 3 --explain; rc=$?; echo "exact_exit_code=$rc"
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode ann --k 3 --explain; rc=$?; echo "ann_exit_code=$rc"
```

```sql
SHOW INDEX FROM chunk_vectors WHERE Key_name='vector_idx';
```

ANN plan 必須實際顯示 `key=vector_idx`，exact 不應使用它。交件附 SQL index、兩組 IDs/plans、交集計算和實際 exit codes；相同交集只代表本次 checkpoint。

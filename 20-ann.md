# 20 ANN：索引是近似候選，不是正確答案

> **概念**：VECTOR INDEX 可以提供 ANN 近似搜尋，但必須和 exact 結果及 EXPLAIN plan 對照；16 筆資料不能宣稱效能優勢。

[上一節](19-vector-ranking.md) · [下一節](21-filters-evaluation.md)

![Ch20 流程圖](diagrams/mariadb/ch20.svg)

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
from embedding_course import load_artifact
from course_db import connect
from vector_course import recorded_query, search

artifact = load_artifact(Path(os.environ.get("VECTOR_ARTIFACT", str(Path.home()/"mariadb-vectors.json"))))
case, vector = recorded_query(artifact, "Q01")
with connect() as conn:
    exact = search(conn, vector, k=3, category_id=case["category_id"], mode="exact", explain=False)
    ann = search(conn, vector, k=3, category_id=case["category_id"], mode="ann", explain=False)
print("exact =", [(r["chunk_id"], r["distance"]) for r in exact])
print("ann =", [(r["chunk_id"], r["distance"]) for r in ann])
exact_ids = {r["chunk_id"] for r in exact}
print("intersection_fraction =", len(exact_ids & {r["chunk_id"] for r in ann}) / len(exact_ids) if exact_ids else None)
```

## 3. 固定 Agent prompt

> 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，將完整程式原樣存為 `/tmp/ch20_ann.py` 並執行。程式中的 `explain=False` 用來取得 exact/ANN 實際結果；另外執行下方兩個 `search --explain` 命令取得 plans，確認 ANN 的 `key=vector_idx`、exact 不使用 `vector_idx`（exact 的 plan 可能使用 `document_id`）。不得 placeholders、改 query/k、手動捏造 plan 或讀 HackMD/repos。回報每一步的 stdout、stderr 與實際 exit code。

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

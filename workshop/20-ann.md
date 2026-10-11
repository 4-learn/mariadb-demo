# 20 ANN Workshop

## 概念
VECTOR INDEX 是近似候選；exact 是基準。ANN 必須由 EXPLAIN 證明使用 `vector_idx`。

## 完整程式 `/tmp/ch20_ann.py`
```python
import os
from pathlib import Path
from embedding_course import load_artifact,recorded_query
from course_db import connect
from vector_course import search
a=load_artifact(Path(os.environ.get("VECTOR_ARTIFACT",str(Path.home()/"mariadb-vectors.json"))))
case,v=recorded_query(a,"Q01")
with connect() as conn:
 exact=search(conn,v,k=3,category_id=case["category_id"],mode="exact",explain=True)
 ann=search(conn,v,k=3,category_id=case["category_id"],mode="ann",explain=True)
print("exact =",[r["chunk_id"] for r in exact]); print("ann =",[r["chunk_id"] for r in ann])
e={r["chunk_id"] for r in exact}; n={r["chunk_id"] for r in ann}; print("intersection_fraction =",len(e&n)/len(e) if e else None)
```

## Agent prompt
> 使用 `/usr/bin/python3`、`PYTHONPATH="$PWD"` 執行 `/tmp/ch20_ann.py`；不得 TODO、捏造 plan、改 query/k 或讀 HackMD/repos。回報兩組 exit code。

```bash
PYTHONPATH="$PWD" /usr/bin/python3 /tmp/ch20_ann.py; rc=$?; echo "exit_code=$rc"
mariadb mariadb_workshop_2026 -e "SHOW INDEX FROM chunk_vectors WHERE Key_name='vector_idx';"
```
保留 plans、IDs、交集及 SQL；小資料不可宣稱效能。

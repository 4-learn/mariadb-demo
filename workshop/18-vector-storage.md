# 18 向量入庫 Workshop

## 概念
`VECTOR(512)` 由參數化 `VEC_FromText(?)` 解析；FK 仍須搭配 version/hash/metadata。

## 完整程式 `/tmp/ch18_storage.py`
```python
import os,json
from pathlib import Path
from course_db import connect
from embedding_course import load_artifact
a=load_artifact(Path(os.environ.get("VECTOR_ARTIFACT",str(Path.home()/"mariadb-vectors.json"))))
v=json.dumps(a["chunks"][0]["embedding"],separators=(",",":"))
with connect() as conn:
 with conn.cursor() as cur:
  cur.execute("SELECT VEC_DISTANCE_COSINE(VEC_FromText(?),VEC_FromText(?))",(v,v)); print("self_distance =",cur.fetchone()[0])
```

## Agent prompt
> 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，寫入並執行 `/tmp/ch18_storage.py`；不可 placeholders、拼 SQL、讀 HackMD/repos。回報 stdout/stderr/實際 exit code。

```bash
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch18_storage.py; rc=$?; echo "code_exit_code=$rc"
python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"; rc=$?; echo "ingest_exit_code=$rc"
python vector_course.py check; rc=$?; echo "check_exit_code=$rc"
mariadb mariadb_workshop_2026 -e "SELECT COUNT(*) FROM chunk_vectors; SELECT COUNT(*) FROM chunks c JOIN chunk_vectors v USING(chunk_id) WHERE c.source_version<>v.source_version OR BINARY c.content_hash<>BINARY v.content_hash;"
```

預期 16、0、check 0；重跑 ingest 應非零且資料不變。附 SQL、stdout/stderr 與 exit code。

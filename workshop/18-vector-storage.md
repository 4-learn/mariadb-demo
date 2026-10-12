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
> 你現在在 `~/workspace/mariadb-demo`。請一氣呵成完成 Ch18 Workshop，最後只回報 PASS 或 FAIL 與證據。
> 1. 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，將完整 code section 原樣寫入 `/tmp/ch18_storage.py` 並執行。
> 2. 先用 `course_editor.cnf` 檢查 `chunk_vectors`：若不存在，執行 `demo/18-vector-storage.sql` 建表，再用課程 venv 執行 `vector_course.py ingest`；若已存在，不要 DROP、不要重跑 DDL、不要重跑 ingest。
> 3. 不論哪一種情況，都執行 `vector_course.py check`。
> 4. 用實際存在的 `course_editor.cnf` 執行 SQL，取得 `vector_count` 與 `mismatches`。
> 5. 只有同時符合 `code_exit_code=0`、`check_exit_code=0`、`sql_exit_code=0`、`vector_count=16`、`mismatches=0` 才回報 `PASS`；否則回報 `FAIL`、失敗步驟與真實錯誤。
> 不得 DROP、修改 artifact、拼接 SQL、讀 HackMD/repos 或讀取秘密。每一步回報實際命令、stdout、stderr、exit code；但不要因為已存在且一致而停下。

```bash
# 1. code section
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch18_storage.py; rc=$?; echo "code_exit_code=$rc"
# 2. 只有 chunk_vectors 不存在時才建表與 ingest；已存在時跳過。
if mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 -N -e "SHOW TABLES LIKE 'chunk_vectors';" | grep -qx chunk_vectors; then
  echo "chunk_vectors exists; skip DDL and ingest"
else
  mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/18-vector-storage.sql; rc=$?; echo "ddl_exit_code=$rc"
  PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"; rc=$?; echo "ingest_exit_code=$rc"
fi
# 3. 不論是否已存在，都執行完整性檢查
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py check; rc=$?; echo "check_exit_code=$rc"
# 4. SQL 交叉驗證
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 -e "SELECT COUNT(*) AS vector_count FROM chunk_vectors; SELECT COUNT(*) AS mismatches FROM chunks c JOIN chunk_vectors v USING(chunk_id) WHERE c.source_version<>v.source_version OR BINARY c.content_hash<>BINARY v.content_hash;"; rc=$?; echo "sql_exit_code=$rc"
```

預期 16、0、check 0；重跑 ingest 應非零且資料不變。附 SQL、stdout/stderr 與 exit code。

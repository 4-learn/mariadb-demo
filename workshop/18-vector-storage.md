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
> 你現在在 `~/workspace/mariadb-demo`。請完成整個 Ch18 Workshop，不要只執行第一段 Python：
> 1. 先檢查 `chunk_vectors` 是否已存在；若存在，先停下並回報，不要自行 DROP。只有教師確認後，才可用 `course_editor` 清理練習表，再執行 `demo/18-vector-storage.sql`。
> 2. 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，將完整 code section 原樣寫入 `/tmp/ch18_storage.py` 並執行。
> 3. 依序執行 `vector_course.py ingest`、`vector_course.py check`，兩者都使用同一個課程 venv。
> 4. 使用實際存在且教師指定的 `.cnf` 執行 SQL；不要猜測 `mariadb-course-app.cnf`。
> 5. 確認 `vector_count=16`、`mismatches=0`。
> 不得加 placeholders、拼接 SQL、修改 artifact 或讀 HackMD/repos。每一步都回報實際命令、stdout、stderr、exit code；任何一步失敗都保留真實錯誤，不要假裝成功。

```bash
# 0. 先確認練習表；若已存在，停止並請教師確認，不可自行 DROP。
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 -e "SHOW TABLES LIKE 'chunk_vectors';"
# 教師確認乾淨後才建立向量表（使用 course_editor）。
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/18-vector-storage.sql; rc=$?; echo "ddl_exit_code=$rc"
# 1. code section
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch18_storage.py; rc=$?; echo "code_exit_code=$rc"
# 2. 寫入 artifact（使用課程 venv）
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"; rc=$?; echo "ingest_exit_code=$rc"
# 4. 執行完整性檢查
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py check; rc=$?; echo "check_exit_code=$rc"
# 5. SQL 交叉驗證
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 -e "SELECT COUNT(*) AS vector_count FROM chunk_vectors; SELECT COUNT(*) AS mismatches FROM chunks c JOIN chunk_vectors v USING(chunk_id) WHERE c.source_version<>v.source_version OR BINARY c.content_hash<>BINARY v.content_hash;"; rc=$?; echo "sql_exit_code=$rc"
```

預期 16、0、check 0；重跑 ingest 應非零且資料不變。附 SQL、stdout/stderr 與 exit code。

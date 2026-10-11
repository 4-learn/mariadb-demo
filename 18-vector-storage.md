# 18 向量入庫：原文、版本與座標對得起來

> **概念**：`VECTOR(512)` 是資料庫欄位，不是任意 JSON。PK/FK 只保證關聯；source version、content hash、model metadata 才能證明向量對應目前原文。DDL 與 ingest 權限、交易邊界要分開。

[上一節](17-embedding.md) · [下一節](19-vector-ranking.md)

## 1. SQL checkpoint 與結構

```sql
SELECT DATABASE(), CURRENT_USER();
SELECT COUNT(*) AS chunks FROM chunks;
SELECT COUNT(*) AS vectors FROM information_schema.tables
 WHERE table_schema=DATABASE() AND table_name='chunk_vectors';
```

乾淨起點為 16 chunks 且 `chunk_vectors` 尚不存在。若上一輪練習已留下這張**練習表**，先用 `course_editor` 明確刪除後重建；不要刪除任何正式表。editor 建表、app 入庫，不使用 root。`VEC_FromText(?)` 的向量 JSON 必須是參數。

## 2. 完整可執行 code section（唯讀解析）

```python
import json, os
from pathlib import Path
from course_db import connect
from embedding_course import load_artifact

artifact = load_artifact(Path(os.environ.get("VECTOR_ARTIFACT", str(Path.home()/"mariadb-vectors.json"))))
vector_json = json.dumps(artifact["chunks"][0]["embedding"], separators=(",", ":"))
with connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT VEC_DISTANCE_COSINE(VEC_FromText(?), VEC_FromText(?))", (vector_json, vector_json))
        distance = cur.fetchone()[0]
        print("self_distance =", distance)
        print("dimension =", len(artifact["chunks"][0]["embedding"]))
```

正式寫入使用既有 `vector_course.py ingest`，同樣參數化並在單一 transaction 中寫入 16 筆。

## 3. 固定 Agent prompt

> 你現在在 `~/workspace/mariadb-demo`。請完成整個 Ch18 Workshop，不要只執行第一段 Python：\n> 1. 先檢查 `chunk_vectors` 是否已存在；若存在，請先停下並回報，不要自行 DROP。只有教師確認後，才可使用 `course_editor` 執行 `DROP TABLE chunk_vectors`，再執行 `demo/18-vector-storage.sql` 建立練習表。\n> 2. 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，將完整 code section 原樣寫入 `/tmp/ch18_storage.py` 並執行。\n> 3. 依序執行 `vector_course.py ingest`、`vector_course.py check`，兩者都必須使用同一個課程 venv。\n> 4. 使用實際存在且教師指定的 `.cnf` 執行下方 SQL；不要猜測 `mariadb-course-app.cnf`。\n> 5. 確認 `vector_count=16`、`mismatches=0`。\n> 不得加 placeholders、拼接 SQL、修改 artifact 或讀 HackMD/repos。每一步都回報實際命令、stdout、stderr、exit code；任何一步失敗都保留真實錯誤，不要假裝成功。

## 4. 執行與 SQL 驗證

```bash
# 建表前先確認是否已有練習表；已有時停止並請教師確認是否清理。
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 -e "SHOW TABLES LIKE 'chunk_vectors';"

# 教師確認乾淨後才建立練習表。
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/18-vector-storage.sql; rc=$?; echo "ddl_exit_code=$rc"

PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"; rc=$?; echo "ingest_exit_code=$rc"
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py check; rc=$?; echo "check_exit_code=$rc"
```

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 -e "SELECT COUNT(*) AS vector_count FROM chunk_vectors; SELECT COUNT(*) AS mismatches FROM chunks c JOIN chunk_vectors v USING (chunk_id) WHERE c.source_version<>v.source_version OR BINARY c.content_hash<>BINARY v.content_hash;"; rc=$?; echo "sql_exit_code=$rc"
```

```sql
SELECT COUNT(*) AS vector_count FROM chunk_vectors;
SELECT COUNT(*) AS mismatches
FROM chunks c JOIN chunk_vectors v USING (chunk_id)
WHERE c.source_version<>v.source_version OR BINARY c.content_hash<>BINARY v.content_hash;
```

成功為 16、0、check exit 0。再次 ingest 應非零且資料仍 16 筆；維度、revision 或 hash 不符必須在寫入前拒絕。交件附角色、命令、實際 exit code 與 SQL 結果，不交 cnf。

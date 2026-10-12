# 18 向量入庫：原文、版本與座標對得起來

> **概念**：把文字、版本、hash、模型資訊與向量一起存入 MariaDB，保留原文和向量的可追溯關係。

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

### 重要片段怎麼看？

| 程式片段 | 這一章要理解什麼 |
|---|---|
| `json.dumps(..., separators=(",", ":"))` | 把向量整理成 MariaDB 可以解析的 JSON 文字；不是手動修改向量。 |
| `VEC_FromText(?)` | 把參數傳入的 JSON 文字轉成 MariaDB 的向量值。 |
| `cur.execute(sql, (vector_json, vector_json))` | 用參數傳值，讓 SQL 與資料分開；兩個參數各代表一個向量。 |
| `fetchone()[0]` | 取回這次距離計算的唯一結果。 |
| `self_distance` | 同一個向量和自己比較，應接近 `0`，用來確認向量格式可被資料庫解析。 |

正式寫入使用既有 `vector_course.py ingest`，同樣參數化並在單一 transaction 中寫入 16 筆。

## 3. 固定 Agent prompt

> 你現在在 `~/workspace/mariadb-demo`。請一氣呵成完成 Ch18 Workshop，最後只回報 PASS 或 FAIL 與證據。
> 1. 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，將完整 code section 原樣寫入 `/tmp/ch18_storage.py` 並執行。
> 2. 先用 `course_editor.cnf` 檢查 `chunk_vectors`：若不存在，執行 `demo/18-vector-storage.sql` 建表，再用課程 venv 執行 `vector_course.py ingest`；若已存在，不要 DROP、不要重跑 DDL、不要重跑 ingest。
> 3. 不論哪一種情況，都執行 `vector_course.py check`。
> 4. 用實際存在的 `course_editor.cnf` 執行 SQL，取得 `vector_count` 與 `mismatches`。
> 5. 只有同時符合 `code_exit_code=0`、`check_exit_code=0`、`sql_exit_code=0`、`vector_count=16`、`mismatches=0` 才回報 `PASS`；否則回報 `FAIL`、失敗步驟與真實錯誤。
> 不得 DROP、修改 artifact、拼接 SQL、讀 HackMD/repos 或讀取秘密。每一步回報實際命令、stdout、stderr、exit code；但不要因為已存在且一致而停下。

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

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

乾淨起點為 16 chunks 且 `chunk_vectors` 尚不存在。editor 建表、app 入庫，不使用 root。`VEC_FromText(?)` 的向量 JSON 必須是參數。

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

> 使用 `/usr/bin/python3`、`PYTHONPATH="$PWD"`，將上述完整程式寫入 `/tmp/ch18_storage.py` 並執行；不得加 TODO、拼接 SQL、修改 artifact 或讀 HackMD/repos。回報 stdout、stderr、實際 exit code。

## 4. 執行與 SQL 驗證

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/18-vector-storage.sql; rc=$?; echo "exit_code=$rc"
python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"; rc=$?; echo "exit_code=$rc"
python vector_course.py check; rc=$?; echo "exit_code=$rc"
```

```sql
SELECT COUNT(*) AS vector_count FROM chunk_vectors;
SELECT COUNT(*) AS mismatches
FROM chunks c JOIN chunk_vectors v USING (chunk_id)
WHERE c.source_version<>v.source_version OR BINARY c.content_hash<>BINARY v.content_hash;
```

成功為 16、0、check exit 0。再次 ingest 應非零且資料仍 16 筆；維度、revision 或 hash 不符必須在寫入前拒絕。交件附角色、命令、實際 exit code 與 SQL 結果，不交 cnf。

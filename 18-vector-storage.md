# 18 向量入庫：原文、版本與座標對得起來

> **定位**：沿用 Ch5–16 的 PK/FK、DDL、參數化與交易驗證，把真實向量安全放回 chunk 關聯；Python 只負責可選的入庫實作。

[上一節](17-embedding.md) · [下一節](19-vector-ranking.md)

## 學習目標

- 區分 JSON 傳輸值與 MariaDB `VECTOR(512)` 欄位。
- 用 PK/FK、版本、content hash、模型 metadata 防止錯配。
- 知道 DDL 與 DML 的權限和交易邊界。

## 1. 先確認 SQL checkpoint

```sql
SELECT DATABASE(), CURRENT_USER();
SELECT COUNT(*) AS chunks FROM chunks;
SELECT COUNT(*) AS vectors FROM information_schema.tables
 WHERE table_schema=DATABASE() AND table_name='chunk_vectors';
```

乾淨起點應有 16 chunks 且尚無 `chunk_vectors`。不要在錯誤 checkpoint 上用 `IF NOT EXISTS` 掩蓋問題。

## 2. 結構與安全概念

`chunk_vectors(chunk_id PK, source_version, content_hash, model_id, model_revision, preprocessing_id, embedding VECTOR(512) NOT NULL, FK chunk_id→chunks)` 讓一個 chunk 對一筆向量；但 FK 不會證明原文未變，仍須 hash／metadata 驗證。editor 建表，app 只入庫；不使用 root。

向量 JSON 必須作一個參數交給 `VEC_FromText(?)`，不可拼接 SQL。DDL 有隱含 commit，不把建表當作後續 ingest rollback。

## 3. Code section：完成最小唯讀核對（Python 可選）

Workshop 與本章使用同一段；它先驗證真實向量能被 MariaDB 解析，不會寫入資料：

```python
import json
from course_db import connect
from embedding_course import load_artifact

artifact = load_artifact("$HOME/mariadb-vectors.json")
# TODO 1：取第一個 chunk 的 embedding，序列化成 JSON array。
vector_json = json.dumps(artifact["chunks"][0]["embedding"])
with connect() as conn:
    with conn.cursor() as cur:
        # TODO 2：以兩個參數查同一向量的 cosine distance。
        cur.execute("SELECT VEC_DISTANCE_COSINE(VEC_FromText(?), VEC_FromText(?))", (vector_json, vector_json))
        print(cur.fetchone())
```

正式 `INSERT` 也必須參數化，並在 transaction 中一次成功 16 筆；完整實作為 `vector_course.py ingest`。

## 4. 執行、驗證、交付

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/18-vector-storage.sql
python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"
python vector_course.py check
```

SQL 交叉驗證：

```sql
SELECT COUNT(*) FROM chunk_vectors;
SELECT c.chunk_id, c.source_version=v.source_version AS version_ok,
       BINARY c.content_hash=BINARY v.content_hash AS hash_ok
FROM chunks c JOIN chunk_vectors v USING (chunk_id) ORDER BY c.chunk_id;
```

預期 16 筆且全部為 1。再次 ingest 應拒絕且資料不變；維度、revision、原文 hash 不符應在寫入前失敗。

## 交件

交付角色與權限、code section、ingest/check 輸出、SQL 16 筆與 hash/version 結果，以及重跑拒絕的退出碼。不要交私人 cnf。

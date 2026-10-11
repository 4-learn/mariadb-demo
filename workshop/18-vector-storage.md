# 18 向量入庫 Workshop

## 任務

先核對 SQL checkpoint，再完成主課同一個 code section。可自己完成或請 Agent 補 TODO；Agent 不得取得私人 cnf，執行與驗收由你完成。

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

## 執行與驗收

1. editor 執行 `demo/18-vector-storage.sql`，記錄帳號，不用 root。
2. 執行 code section，距離應接近 0；這只是解析核對，不是入庫成功證明。
3. 執行 `vector_course.py ingest`、`check`，確認 16 筆、版本/hash/metadata 一致。
4. 再次 ingest 必須非零退出，且筆數與內容未變。

若只有 `embedding` 沒有 chunk_id、hash、版本或模型 revision，不算通過；外鍵也不能代替這些檢查。

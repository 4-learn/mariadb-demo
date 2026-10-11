# 19 精確排名 Workshop

## 任務

使用主課同一 code section；可自己補 TODO，或請 Agent 只補 TODO 後由你執行與驗證。

```python
from course_db import connect
from embedding_course import load_artifact, recorded_query

artifact = load_artifact("$HOME/mariadb-vectors.json")
case, query_vector = recorded_query(artifact, "Q01")
# TODO 1：以 query_vector 執行課程的 exact search，category 與 k 固定。
rows = None
# TODO 2：列出每列的 chunk_id、distance，並確認排序鍵。
for row in rows:
    print(row["chunk_id"], row["distance"])
```

## 執行與驗收

先用 C001 自我查詢驗證 distance 接近 0，再執行 Q01 exact `--explain`。保存實際 chunk_id、distance、source_version、原文與 plan；確認同分以 chunk_id 升冪、沒有 vector_idx。不得用人工預期調整排名，也不得把 top-k 當答案正確率。

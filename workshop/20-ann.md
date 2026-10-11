# 20 ANN Workshop

## 任務

用主課同一段 code section；你可自行完成或請 Agent 補 TODO，但必須自己保留兩份 plan。

```python
from course_db import connect
from embedding_course import load_artifact, recorded_query
from vector_course import search

artifact = load_artifact("$HOME/mariadb-vectors.json")
case, query_vector = recorded_query(artifact, "Q01")
# TODO 1：用同一 query、category=1、k=3 執行 exact。
exact = None
# TODO 2：用同一輸入執行 ann，分別保留兩組 chunk_id。
ann = None
print("exact =", [r["chunk_id"] for r in exact])
print("ann =", [r["chunk_id"] for r in ann])
```

## 執行與驗收

先用 editor 建立 `vector_idx`（cosine、M=6），再以完全相同 Q01/category 1/k=3 執行 exact 與 ann 並加 `--explain`。exact 不得使用 vector_idx；ANN 沒有實際 `key=vector_idx` 就記為未驗證。填實際交集與分母；不要預填 3/3、不要把交集當人工語意 recall。

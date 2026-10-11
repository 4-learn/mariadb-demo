# 20 ANN：索引是近似候選，不是正確答案

> **定位**：沿用 Ch5–19 的索引、EXPLAIN、ORDER BY 與可重算驗證，對照 exact 與 ANN；不以 16 筆資料宣稱效能。

[上一節](19-vector-ranking.md) · [下一節](21-filters-evaluation.md)

## 學習目標

- 分辨 VECTOR INDEX 與 B-tree 的用途。
- 核對 cosine、M=6、實際 `key=vector_idx`。
- 以 exact 結果作候選交集基準，不混淆語意 recall。

## 1. 先用 SQL 建立並檢查索引

```sql
ALTER TABLE chunk_vectors
  ADD VECTOR INDEX vector_idx (embedding) M=6 DISTANCE=cosine;
SHOW INDEX FROM chunk_vectors;
```

只在乾淨 checkpoint 建一次；DDL 有隱含 commit。建立失敗或已存在時先停下核對，不重複刪建。

## 2. Code section：完成 exact／ANN 對照（Python 可選）

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

提示：用 `search(..., mode='exact'/'ann', explain=True)`，不要自行改 SQL 排序形狀。

## 3. 執行、驗證、交付

保留兩組 EXPLAIN：exact 應不選 vector_idx，ANN 必須實際顯示 `key=vector_idx` 才能宣稱索引已使用。計算 `|A∩E|/|E|`；E 為空則 null。交集相同只代表此 query、k、checkpoint 相同，不代表 ANN 永遠精確或更快。

## 交件

交付 DDL、index 設定、同一 query 的兩組 plan／IDs／交集計算與限制說明。不要拿單次小資料耗時當 benchmark。

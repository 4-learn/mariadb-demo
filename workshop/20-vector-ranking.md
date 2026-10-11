# 20 精確排名 Workshop

## 情境

你要建立能重現的精確搜尋，供 ANN 比較。不要先追求快，先確認距離方向、資格與排序。

### 專案背景

16 個真實向量已入庫。未建 vector_idx 時可執行 raw SQL；建過時用 API 自動 IGNORE INDEX。

### 使用者需求

> 「同一個問題和同一份資料，至少同分順序要能說明。」

### 你的任務

1.自我距離 Q01 排名計畫與解釋。
2. 列出實際 ID／距離，不依照人工預期調整結果。
3. 保存精確路徑 EXPLAIN。

### 技術需求

- `VEC_DISTANCE_COSINE`，distance ASC，再 chunk_id ASC。
- 固定 Q01 或真實 encode；不可用 C001 文件向量假裝 query。

## 輸入資料格式

```text
case=Q01, category=1, k=3, mode=exact
```

## 輸出示例

最多三筆唯一候選，每筆含 chunk_id、document_id、source_version、text、distance。排名與小數依實際執行保存，不在解答預填。

## 你需要實作的功能

```bash
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode exact --k 3
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode exact --k 3 --explain
```

### 提示

文件向量自我查詢應接近 0；Q01 的 query 與 C001 不是同一文字，也有 query 前綴，不應期待距離為 0。

## 解答

```python
from pathlib import Path
from course_db import connect
from embedding_course import load_artifact
from vector_course import recorded_query, search
a = load_artifact(Path.home() / "mariadb-vectors.json")
case, q = recorded_query(a, "Q01")
conn = connect()
try:
    rows = search(conn, q, k=3, category_id=case["category_id"])
    keys = [(r["distance"], r["chunk_id"]) for r in rows]
    assert keys == sorted(keys)
    assert len({r["chunk_id"] for r in rows}) == len(rows)
    print(keys)
    print(search(conn, q, k=3, category_id=1, explain=True))
finally:
    conn.close()
```

LIMIT 只是截取最靠近的 k 筆，沒有判斷它們是否真的回答問題；必須另對照原文與人工相關集合。改 DESC 是方向錯誤；用 ANN plan 當 exact 或只在結果出來後去重都不能通過。


## Agent 操作與驗證

請先要求 Agent 說明命令與預期變更，確認後才執行；完成後自行核對 exit code、實際輸出與資料庫證據。

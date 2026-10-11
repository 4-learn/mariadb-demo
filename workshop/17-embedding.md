# 17 Embedding Workshop

## 任務

先完成主課同一個 code section，再用 SQL 與 metadata 驗證。你可以：

- **自己完成**：補 TODO、執行並記錄真實輸出。
- **Agent 完成**：把同一段 code section 與錯誤訊息交給 Agent，只要求補 TODO；你仍須執行與核對。

```python
from embedding_course import load_artifact, validate_vector

# TODO 1：載入教師提供或自己生成的 artifact。
artifact = load_artifact("$HOME/mariadb-vectors.json")
# TODO 2：驗證第一筆 chunk 向量，並印出維度與平方範數。
vector = artifact["chunks"][0]["embedding"]
validate_vector(vector)
print("dimension =", len(vector))
print("squared_norm =", sum(x * x for x in vector))
print("chunks =", len(artifact["chunks"]), "queries =", len(artifact["queries"]))
print("model_revision =", artifact["metadata"]["model_revision"])
```

## 操作與驗收

1. 先執行 `SELECT COUNT(*) FROM documents/chunks`，確認 8／16、版本 1。
2. 執行 `python embedding_course.py validate --artifact "$HOME/mariadb-vectors.json"`。
3. 執行 code section；若使用預計算，明示「預計算」，不可冒充本機 encode。
4. 記錄 dimension=512、平方範數接近 1、revision、16／8／2 數量。

離線缺檔、hash 不符、模型 revision 不同或 artifact 已存在時，記錄非零退出與錯誤類型，不改成成功。解釋為何新問題不能拿 Q01 向量代替，以及為何相似度不等於安全答案。

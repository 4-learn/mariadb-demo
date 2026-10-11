# 17 Embedding：把文字變成可追溯的向量

> **概念**：embedding 是固定模型把文字映射成數字；它不是答案，也不能跨模型混用。本節固定 `BAAI/bge-small-zh-v1.5` revision `7999e1d3359715c523056ef9478215996d62a620`、512 維、文件不加 instruction、query 使用模型卡 instruction，並做 L2 normalization。

[上一節](16-import-quality.md) · [下一節](18-vector-storage.md)

## 1. SQL checkpoint

```sql
SELECT DATABASE(), CURRENT_USER();
SELECT COUNT(*) AS documents FROM documents;
SELECT COUNT(*) AS chunks FROM chunks;
SELECT MIN(source_version) AS min_version, MAX(source_version) AS max_version FROM chunks;
```

預期資料庫 `mariadb_workshop_2026`、8 documents、16 chunks、版本 1。若不同，先停下並記錄實際結果。

## 2. 完整可執行 code section

把下列程式存成 `/tmp/ch17_embedding.py`；它不含 TODO，使用教師提供的 artifact 並驗證每筆向量。

```python
import os
from pathlib import Path
from embedding_course import load_artifact, validate_vector

path = Path(os.environ.get("VECTOR_ARTIFACT", str(Path.home() / "mariadb-vectors.json")))
artifact = load_artifact(path)
for item in artifact["chunks"]:
    vector = item["embedding"]
    validate_vector(vector)
assert all(len(item["embedding"]) == 512 for item in artifact["chunks"])
print("dimension =", len(artifact["chunks"][0]["embedding"]))
print("squared_norm =", sum(x*x for x in artifact["chunks"][0]["embedding"]))
print("chunks =", len(artifact["chunks"]), "queries =", len(artifact["queries"]))
print("model_revision =", artifact["metadata"]["model_revision"])
print("embedding_mode = recorded-artifact")
```

## 3. 固定 Agent prompt（可選）

> 使用 `/usr/bin/python3`，設定 `PYTHONPATH="$PWD"`，把完整程式寫入 `/tmp/ch17_embedding.py` 後執行；不可新增 TODO、不可改模型 revision、不可讀取 HackMD 或 repos。命令：`PYTHONPATH="$PWD" /usr/bin/python3 /tmp/ch17_embedding.py`。回報實際 stdout、stderr 與 exit code。

## 4. 執行與驗收

```bash
PYTHONPATH="$PWD" /usr/bin/python3 /tmp/ch17_embedding.py; rc=$?; echo "exit_code=$rc"
python embedding_course.py validate --artifact "$HOME/mariadb-vectors.json"; rc=$?; echo "exit_code=$rc"
```

成功證據應為 exit code 0、dimension 512、平方範數接近 1、16 chunks／8 queries／2 updated chunks，以及完整 revision。另以 SQL checkpoint 驗證 8／16／1。若 artifact 缺檔、hash 不符或 revision 不符，保留非零 exit code，不把預計算資料稱為 live encode。

## 交件

提交 SQL 結果、完整 code、兩個命令的實際輸出與 exit code，並說明相似度仍須回查原文及業務條件。

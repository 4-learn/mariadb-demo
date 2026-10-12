# 17 Embedding：把文字變成可追溯的向量

> **概念**：把文字轉成固定維度的向量，讓電腦能用數值表示文字意義。本節固定 `BAAI/bge-small-zh-v1.5` revision `7999e1d3359715c523056ef9478215996d62a620`、512 維、文件不加 instruction、query 使用模型卡 instruction，並做 L2 normalization。

[上一節](16-import-quality.md) · [下一節](18-vector-storage.md)

## 1. SQL checkpoint

```sql
SELECT DATABASE(), CURRENT_USER();
SELECT COUNT(*) AS documents FROM documents;
SELECT COUNT(*) AS chunks FROM chunks;
SELECT MIN(source_version) AS min_version, MAX(source_version) AS max_version FROM chunks;
```

預期資料庫 `mariadb_workshop_2026`、8 documents、16 chunks、版本 1。若不同，先停下並記錄實際結果。

### SQL 欄位怎麼看？

| 欄位 | 簡單說明 | 預期 |
|---|---|---|
| `DATABASE()` | 目前使用哪個資料庫 | `mariadb_workshop_2026` |
| `CURRENT_USER()` | MariaDB 用哪個帳號驗證 | 依課程帳號 |
| `documents` | 文件有幾份 | `8` |
| `chunks` | 文字切成幾段 | `16` |
| `min_version` / `max_version` | 文字版本範圍 | 都是 `1` |

`squared_norm` 不用自己算：把它想成「向量大小的檢查數字」；本課程接近 `1` 就表示格式正常。

## 2. 完整可執行 code section

把下列程式存成 `/tmp/ch17_embedding.py`；它不含 placeholders，使用教師提供的 artifact 並驗證每筆向量。

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

### 重要片段怎麼看？

| 程式片段 | 這一章要理解什麼 |
|---|---|
| `load_artifact(path)` | 讀取教師預先產生的向量 artifact；本章不是即時訓練模型。 |
| `for item in artifact["chunks"]` | 逐一檢查每個文字片段的向量。 |
| `validate_vector(vector)` | 確認向量格式、數值與維度符合課程規則。 |
| `len(item["embedding"])` | 計算每個向量有幾個數字；本章應為 `512`。 |
| `squared_norm` | 檢查向量長度平方；接近 `1` 代表完成 L2 normalization。 |
| `model_revision` | 記錄產生向量的模型版本，讓結果可以追溯。 |

## 3. 固定 Agent prompt（可選）

> 使用 `/home/yillkid/mariadb-course-venv/bin/python`，設定 `PYTHONPATH="$PWD"`，把完整程式寫入 `/tmp/ch17_embedding.py` 後執行；不可新增 placeholders、不可改模型 revision、不可讀取 HackMD 或 repos。命令：`PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch17_embedding.py`。回報實際 stdout、stderr 與 exit code。

## 4. 執行與驗收

```bash
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch17_embedding.py; rc=$?; echo "exit_code=$rc"
python embedding_course.py validate --artifact "$HOME/mariadb-vectors.json"; rc=$?; echo "exit_code=$rc"
```

成功證據應為 exit code 0、dimension 512、平方範數接近 1、16 chunks／8 queries／2 updated chunks，以及完整 revision。另以 SQL checkpoint 驗證 8／16／1。若 artifact 缺檔、hash 不符或 revision 不符，保留非零 exit code，不把預計算資料稱為 live encode。

### Output 怎麼看？

| Output | 代表什麼 | 本次預期值 |
|---|---|---|
| `exit_code` | 程式是否成功結束；`0` 通常表示成功 | `0` |
| `dimension` | 每個向量有幾個數字 | `512` |
| `squared_norm` | 向量長度的平方；接近 `1` 代表已完成 L2 normalization | 接近 `1.0` |
| `chunks` | 被轉成向量的文字片段數量 | `16` |
| `queries` | 測試問題數量 | `8` |
| `model_revision` | 產生這批向量所使用的模型版本 | `7999e1d3359715c523056ef9478215996d62a620` |
| `embedding_mode` | 向量的產生方式；`recorded-artifact` 表示使用預先產生的 artifact | `recorded-artifact` |
| `sql_exit_code` | SQL checkpoint 是否執行成功 | `0` |

重點是：`dimension`、`chunks`、`queries` 是資料數量檢查；`squared_norm` 是向量格式檢查；`model_revision` 是版本追蹤；`exit_code` 則是這次命令是否成功。

## 交件

提交 SQL 結果、完整 code、兩個命令的實際輸出與 exit code，並說明相似度仍須回查原文及業務條件。

# 17 Embedding：把文字變成可追溯的向量

> **定位**：先用 Ch5–16 的資料、欄位與驗證思維確認輸入，再把 embedding 當成可比較的數字；Python 只是可選的實作工具，不是答案產生器。

[上一節](16-import-quality.md) · [下一節](18-vector-storage.md)

## 學習目標

- 說明向量不是文字、token 或產品編號，也不保證答案正確。
- 固定模型 revision、CLS pooling、L2 normalization 與 query instruction。
- 以維度、平方範數、來源 hash 和 artifact 數量驗證結果。

## 1. 先確認 SQL checkpoint

先用 MariaDB client 確認仍是課程資料，不要用另一份 corpus 掩蓋缺檔：

```sql
SELECT DATABASE(), CURRENT_USER();
SELECT COUNT(*) AS documents FROM documents;
SELECT COUNT(*) AS chunks FROM chunks;
SELECT MIN(source_version), MAX(source_version) FROM chunks;
```

預期為 `mariadb_workshop_2026`、8 documents、16 chunks、版本 1。查詢結果是後續驗證基準。

## 2. 固定計算契約

本課使用 `BAAI/bge-small-zh-v1.5` revision `7999e1d3359715c523056ef9478215996d62a620`，輸出 512 維；query 加模型卡指定 instruction，文件不加。向量做 L2 normalization，平方範數應接近 1。512 維不代表可以混用另一模型的 512 維。

模型下載與 venv 可依環境準備；若沒有模型快取，可誠實使用教師預計算 artifact，但不得宣稱本機剛完成 encode。

## 3. Code section：完成最小驗證（Python 可選）

這是本章唯一需要完成的 code section；Workshop 會用同一段。可自行完成，或請 Agent 只補 TODO，不提供私人設定檔：

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

實際 Python 字串不會展開 `$HOME`；請改成自己的路徑，或用 `Path.home()`。若選擇即時 encode，使用 `demo/17-embedding.py --offline`；首次缺模型時應失敗並記錄原因。

## 4. 執行、驗證、交付

```bash
python embedding_course.py validate --artifact "$HOME/mariadb-vectors.json"
python demo/17-embedding.py --offline
```

驗證：dimension=512、平方範數接近 1、artifact 為 16 chunks／8 queries／2 updated chunks，revision 完全相同。hash 是完整性檢查，不是數位簽章；輸入過長、revision 不符或輸出已存在都要保留失敗紀錄。

## 交件

提交 SQL checkpoint、code section、執行命令、實際輸出，以及一句話說明「向量相似度仍需回查原文與業務條件」。不要提交模型私有設定或密碼。

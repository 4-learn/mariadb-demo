# 17 向量來源：只驗證教師預計算 artifact

> 本章是 **SQL／Shell-only** 學生路徑：不安裝 Python、不下載模型、不在課堂即時 embedding。教師課前依固定模型產生向量；學生只載入並驗證固定資料。

## 學習目標

- 了解原文、向量、模型 revision、維度與 hash 的關係。
- 用 MariaDB client 檢查 artifact metadata。
- 知道固定 Q01～Q08 不是任意新問題的 live embedding。

## 觀念

MariaDB 能儲存及比較向量，但不會在 SQL 內執行 embedding 模型。教師提供 `data/vector_seed.sql`，其中的向量與 query 已預先產生；學生不得自行填隨機數、複製另一題向量或宣稱剛剛完成 encode。

固定來源包含：模型 `BAAI/bge-small-zh-v1.5`、revision、preprocessing、512 維、normalization 及 hash。換模型或原文就必須由教師重新產生、簽核新的 artifact；不能在資料庫內臨時混用。

## 操作

```bash
cd ~/workspace/mariadb-demo
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/17-vector-artifact.sql
```

> `demo/17-vector-artifact.sql` 對應現有 `demo/17-embedding.sql` 的固定 SQL fixture；若課程包使用原檔名，直接執行 `demo/17-embedding.sql`。

```sql
SELECT artifact_id, model_id, model_revision,
       preprocessing_id, dimension, normalized,
       source_hash, payload_hash
FROM embedding_artifact_meta;

SELECT COUNT(*) AS query_count FROM query_vectors;
```

預期 `dimension=512`、`normalized=1`、`query_count=8`。記錄輸出，不需要列印 512 個座標。

## Workshop

1. 執行 artifact SQL。
2. 記錄 model revision、preprocessing、dimension、normalized 與 hash。
3. 確認 query 數量為 8。
4. 用一句話說明：新問題不能拿固定 Q01 代替，也不能要求 MariaDB 即時產生 embedding。

通過條件是「驗證教師產物」；不是本機跑模型。教師預計算是備課工作，學生全程只使用 MariaDB client 與 Shell。


## 教師補充圖

![image](https://hackmd.io/_uploads/HkT-G9gsfl.png)
![image](https://hackmd.io/_uploads/SJpdf5xiMg.png)

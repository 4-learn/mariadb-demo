# 19 精確 Top-K：先把每一筆距離算清楚

> **定位**：建立距離升冪、同分以 chunk_id 排序的精確搜尋，作為後續 ANN 的可核對基準。

[上一節](18-vector-storage.md) · [下一節](20-ann.md)


## 學習目標

- 區分 cosine similarity 與 cosine distance，正確選擇升冪排序。
- 以真實問題向量查出 top-k，理解 LIMIT 不代表相關判斷。
- 讀取實際 EXPLAIN，避免把用了 ANN 的查詢當成精確標準答案。

## 範例程式碼

- [自我向量距離 SQL](demo/19-vector-ranking.sql)、[精確檢索 API](vector_course.py)。
- [固定查詢與 qrels](data/search_cases.json)、[本節解答](workshop/19-vector-ranking.md)。

---

## 情境

你要回答「同義詞找不到」的問題，先不用索引加速，而是把每個合格 chunk 與查詢的距離算出，再挑最小的幾筆。資料只有 16 段，很適合追蹤每一筆，卻不適合宣稱效能優勢。

先修 checkpoint：18 已入庫 16 個真實向量且 `check` 通過；預設尚未建立 vector_idx。如果教師已建索引，改用程式精確路徑，或明示 `IGNORE INDEX (vector_idx)`，不能盲跑「無索引」範例。

---

## 講解

### 1. 相似度大與距離小是不同方向

對單位向量 u、v，cosine similarity 為內積，cosine distance 為 `1 - similarity`。同一向量距離接近 0；距離越小越靠近。因此本課使用 `VEC_DISTANCE_COSINE` 並 `ASC`，不是 `DESC`。

不要把距離 0.2 解讀成「錯誤率 20%」或「答案正確率 80%」。模型座標沒有這種機率校準。即使兩個問句只有「不」字不同，向量仍可能非常接近，後面還要檢查否定和型號。

### 2. 自我查詢先驗證方向

```sql
SET @q=(SELECT embedding FROM chunk_vectors WHERE chunk_id='C001');
SELECT chunk_id,VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors
ORDER BY distance ASC,chunk_id ASC LIMIT 3;
```

C001 的距離應接近 0，不能要求跨平台剛好印出 `0.000000`。這裡拿 C001 文件向量作**自我查詢**，只是檢查函式與排序，不是把 C001 冒充「恢復出廠設定」的 query embedding。

`chunk_id` 是第二排序鍵。同分時輸出才有穩定順序，便於比較測試。不要依賴資料目前插入順序；SQL 沒有 ORDER BY 的順序不受保證。這份 raw SQL 包含所有向量，尚未套用 active 或分類，正式檢索用後面的 API。

### 3. 用真正問題向量查合格段落

```bash
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --k 3 --mode exact
```

這是明示的固定問題預計算模式；输出會列 query 原文、model metadata 與 source hash。若已快取模型，也可實際編碼新問題：

```bash
python vector_course.py search --query '教學感測器 A 如何恢復出廠設定？' --offline --category 1 --k 3
```

在程式內，向量透過 `VEC_FromText(?)` 接收，資料表先限定 document active、chunk 與 vector 的來源版本／hash 相同，再用 `EXISTS` 確認至少一個符合分類的 active 產品。

```sql
SELECT v.chunk_id,
       VEC_DISTANCE_COSINE(v.embedding,VEC_FromText(?)) AS distance
FROM chunk_vectors v
ORDER BY distance ASC,v.chunk_id ASC LIMIT ?;
```

上方是計算與排序核心，完整 eligibility SQL 在 `search`，不可省略後拿去當正式客服查詢。`k=3` 表示最多三筆；只有兩筆合格就回兩筆，空分類則零筆，不補入其他分類湊滿三筆。

### 4. 精確基準要可證明

```bash
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --k 3 --mode exact --explain
```

記錄每列 EXPLAIN 的 `table`、`type`、`key`、`rows`、`Extra`。`rows` 是最佳化器估計，不是實際計算次數；`Using filesort` 也不是資料必然寫到磁碟的證明。

第 20 節加入向量索引後，程式會把資料表寫成：

```sql
FROM chunk_vectors v IGNORE INDEX (vector_idx)
```

沒有索引時不能硬塞這個 hint，否則會因索引不存在而失敗。函式先查 SHOW INDEX，只有存在時才加入；精確結果需要看实际 plan 確認 `v` 沒有使用 vector_idx。**一次 ANN 結果剛好相同不能替代精確計畫證據。**

---

## Workshop

### 題目

自我距離 Q01 搜尋 plan 與說明。

1. 執行自我查詢，核對 C001 距離近零。
2. 執行 Q01 精確查詢，保留實際 chunk_id、distance、source_version 與原文。
3. 檢查距離升冪；同距離時 chunk_id 升冪。不能手動重排成你希望看到的答案。
4. 留下 EXPLAIN，解釋為何 top-3 中仍可能包含不相關段落。

### 預期輸出

```text
自我查詢：C001 距離接近 0
Q01：最多 3 個不重複、分類 1 的合格 chunk
順序：(distance ASC, chunk_id ASC)
精確 plan：不得使用 vector_idx
```

不規定 Q01 必須把 C001 排第一。若它沒進 top-3，是要記錄的模型檢索失誤，不應改 qrels 或挑另一個向量來讓結果「過關」。

### 解答

[19 Workshop 解答](workshop/19-vector-ranking.md)。第 21 節會把人工相關集合與實際排名分開計算品質。

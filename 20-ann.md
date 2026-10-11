# 20 ANN：索引是近似候選，不是正確答案保證

> **定位**：建立 MariaDB 向量索引，保留真實 EXPLAIN 與精確對照，觀察近似查詢的取捨。

[上一節](19-vector-ranking.md) · [下一節](21-filters-evaluation.md)


## 學習目標

- 辨認 VECTOR INDEX 與一般 B-tree 索引的用途差異。
- 用 cosine 向量索引搭配同一距離函式，實際查看查詢計畫。
- 比較 ANN 與精確候選交集，不以小資料或單次耗時宣稱加速。

## 範例程式碼

- [索引 DDL](demo/20-ann.sql)、[exact／ann 實作](vector_course.py)。
- [官方向量概述](https://mariadb.com/docs/server/reference/sql-structure/vectors/vector-overview)。
- [本節解答](workshop/20-ann.md)。

---

## 情境

每次計算所有段落很容易理解，但資料量很大時可能昂貴。MariaDB 的向量索引使用改良 HNSW 近似近鄰方法，讓搜尋沿向量圖挑候選。它不同於「找 category_id=1」的 B-tree，也不保證每次候選都等於完整精確排序。

先修 checkpoint：19 已留下同一組 artifact 與 query 的精確結果；16 個向量一致，vector_idx 尚未建立。教師使用 11.8.9 核對實際 plan；不套用新版本才有的監控表，也不更改主機 Docker 或伺服器全域設定。

---

## 講解

### 1. 近似的意思是必須有對照

ANN 的目標是用索引找靠近查詢的候選，不是替你讀懂 SOP。資料量、向量分布、索引參數、WHERE 篩選與 LIMIT 都影響结果。圖索引的 `M` 影響圖的連接與資源取捨，本課固定 M=6，不把微型 corpus 當成參數調優實驗。

精確結果 E 與 ANN 結果 A 都取最多 k 筆時，可計算 `|A ∩ E| / |E|`。這是「相對精確檢索的候選重合率」，不是人工語意相關的 recall；第 21 節另有 qrels 評估。若 E 為空，分母為零，記 `null`，不能寫 100%。

### 2. 使用 editor 一次建立 cosine 索引

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/20-ann.sql
```

核心 SQL：

```sql
ALTER TABLE chunk_vectors
  ADD VECTOR INDEX vector_idx (embedding) M=6 DISTANCE=cosine;
SHOW INDEX FROM chunk_vectors;
```

不要使用預設 euclidean 卻拿 cosine 計畫當同一組測試。DDL 隱含 commit，不放入文件更新交易；editor 具 INDEX／ALTER，app 只查詢與 DML。索引已存在時請先確認課程狀態，不重複建立或自行刪除。

### 3. 查詢形狀會影響是否使用索引

```bash
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode ann --k 3 --explain
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode ann --k 3
```

ANN 的核心是裸距離函式升冪加 LIMIT：

```sql
SELECT chunk_id,VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors FORCE INDEX (vector_idx)
ORDER BY distance ASC LIMIT 3;
```

`@q` 可以先設定為 C001 的真實向量做自我測試；正式問題向量由 CLI 綁定 JSON 參數。`FORCE INDEX` 是 MariaDB table index hint 語法，但寫了 hint 不代表已證明實際用了索引，必須保存 11.8.9 的 EXPLAIN，觀察向量表列的 `key=vector_idx`。若沒有使用，先記「ANN 未驗證」，交教師檢查 query／資料／版本，不宣稱測試通過。

不要將內層排序改成 `ORDER BY 1-distance DESC`，或加入第二個排序鍵後假設仍能走 ANN。程式在 DB 以單一 distance 取近似候選，再於 Python 對**已取得候選**以 `(distance, chunk_id)` 排序。這只能穩定候選內同分順序，不能保證候選邊界的全域 tie-break 等同精確搜尋。

正式查詢也帶 active 與分類限制。ANN 在選取候選與篩選時仍可能漏掉合格資料，甚至少於 k 筆；課程預設正式正確性用 exact 路徑，不將 ANN 當成「先完整篩選再精確取前 k」的同義詞。

### 4. 精確對照必須繞過向量索引

```bash
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode exact --k 3 --explain
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode exact --k 3
python vector_course.py evaluate --artifact "$HOME/mariadb-vectors.json" --k 3
```

程式精確路徑為 `IGNORE INDEX (vector_idx)`，排序保留第二鍵 chunk_id。精確 EXPLAIN 不得選 vector_idx；ANN 應選它。只看兩組排名一致不能知道兩個查詢是否實際走了同一個索引。

若本次交集是 3/3，結論只能是「這筆 query、這個 checkpoint、這個 k 的候選相同」。16 段資料常看不出近似差異；不要抄外部 benchmark 當本機成績，也不要為了作圖虛構查詢耗時。效能評估需要足夠資料量、重複測量、相同 cache 條件與資源紀錄，超出本節範圍。

---

## Workshop

### 題目

DDL 兩份 plan 比較候選。

1. 確認 cosine 索引已建立，保留 index 名稱與距離設定。
2. 以 Q01、相同 category 1、k=3 執行 exact／ann，各留 plan 和結果。
3. 寫出兩組 chunk_id 的交集及分母，說明這不是語意正確率。

### 預期輸出

```text
索引：vector_idx / cosine / M=6
exact plan：未選 vector_idx
ann plan：選 vector_idx，否則標示未驗證
候選交集：填實際集合與計算，不預設為 3/3
效能結論：本節不作速度保證
```

### 解答

[20 Workshop 解答](workshop/20-ann.md)。索引建立失敗、ANN 未用索引、拿 ANN 當精確標準，都是需要修正的驗收失敗。

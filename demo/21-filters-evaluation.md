# 21 篩選與評估：找到相似段落，還不等於可用答案

> **定位**：先形成不重複的合格 chunk 集合，再以人工相關標註檢查同義詞、否定、型號及無答案案例。

[上一節](20-ann.md) · [下一節](22-consistency.md)

時間：講解與示範 35 分鐘，Workshop 15 分鐘。

## 學習目標

- 用 EXISTS 避免多對多 JOIN 讓相同 chunk 占據 top-k。
- 同時檢查 document active、至少一個 active product 與分類條件。
- 計算 precision／recall 並區分空 qrels、空合格集合與自動拒答。

## 範例程式碼

- [合格集合 SQL](demo/21-filters-evaluation.sql)、[評估程式](vector_course.py)。
- [八題標註與理由](data/search_cases.json)、[本節解答](workshop/21-filters-evaluation.md)。

---

## 情境

一份重設 SOP 同時連到 P001 與 P002，直接 JOIN 後 C001 會出現兩次，`LIMIT 3` 可能只取得兩個不同段落。另一份文件已停用，卻可能因「電池」語意接近而排很前。你要先把業務規則落在 SQL，才有意義比較排名。

先修 checkpoint：原始 sop-v1 與 artifact 完全一致，所有版本仍為 1；18 的 `check` 通過。索引可有可無，exact 永遠保留可驗證基準。若已完成 22 更新或恢復成版本 3，先由教師提供新 baseline，不能套用版本 1 的 qrels。

---

## 講解

### 1. JOIN 的重複不是模型錯誤（8 分鐘）

```sql
SELECT c.chunk_id,p.product_id
FROM chunks c
JOIN product_documents pd ON pd.document_id=c.document_id
JOIN products p ON p.product_id=pd.product_id
WHERE c.document_id='D001' AND p.status='active'
ORDER BY c.chunk_id,p.product_id;
```

預期 C001、C002 各對 P001、P002，所以四列而非兩列。若先 LIMIT 再在 Python 去重，可能只剩不到 k 個 chunk；不是把 `k` 隨便加倍就能保證修好。

正確的業務需求是「是否至少存在一個符合條件的產品」，不是「每個產品都複製一列段落」，所以用 EXISTS。

### 2. 先決定哪些段落有資格（9 分鐘）

```sql
SET @category=1;
SELECT c.chunk_id,c.document_id
FROM chunks c JOIN documents d ON d.document_id=c.document_id
WHERE d.status='active' AND EXISTS (
  SELECT 1 FROM product_documents pd
  JOIN products p ON p.product_id=pd.product_id
  WHERE pd.document_id=d.document_id AND p.status='active'
    AND (@category IS NULL OR p.category_id=@category)
)
ORDER BY c.chunk_id;
```

分類 1 應有十個唯一 chunk：C001、C002、C007、C008、C009、C010、C011、C012、C015、C016。D004 雖連到 inactive 的 P006，仍有 active 的 P007，因此合格。D003 inactive，不能因關聯存在就回傳。分類 2 為 C003／C004，分類 3 為 C013／C014；999 為零筆。

exact 路徑把這個資格條件放在 WHERE，最後才依距離及 chunk_id 排序取 k。`category_id=None` 表示不限定分類，並不跳過 active 檢查。這不是完整產品型號解析器；P010 這種使用者文字中的編號仍需另外核對關聯。

### 3. 人工相關標註與模型排名必須分開（10 分鐘）

`data/search_cases.json` 提供八筆教材作者逐段判讀的 qrels，不是從模型排名反推。作者為 AI agent，檔案明示 `teacher_review_required`，不冒稱已有真人教師簽核。教師需檢查每題的 query、category、relevant_chunk_ids、rationale，確認需求定義後才作評分基準。

| 案例 | 重點 | 相關集合 |
| --- | --- | --- |
| Q01 | 恢復出廠設定／重設同義需求，category 1 | C001 |
| Q02 | 閘道器頻段與密碼排查，category 2 | C003、C004 |
| Q03 | 要求提供支援 5 GHz 的產品與設定 | 空集合 |
| Q04 | 詢問是不是不支援 5 GHz | C003、C004 |
| Q05 | P010／感測器 H 的專用 SOP | 空集合 |
| Q06 | P012／感測器 I 的 E01 修正 | C015 |
| Q07 | 配件角色與備註拒絕，category 3 | C013、C014 |
| Q08 | 不存在的 category 999 | 空集合 |

Q03 可以找出「不支援」段落作為限制說明，但不能用它滿足「提供支援的產品與設定」這個請求。Q04 問的是限制本身，所以相關集合不同。標註依需求而定，不是每個出現 5 GHz 的段落都算正確。

### 4. 算品質，保留失敗（8 分鐘）

```bash
python vector_course.py evaluate --artifact "$HOME/mariadb-vectors.json" --k 3
```

令 R 為人工 relevant IDs、S 為實際 top-k 唯一 IDs。`precision@k=|R∩S|/k`，本課分母固定 k，不足 k 時不偷偷改分母；`recall@k=|R∩S|/|R|`。例如 Q01 在三筆候選中有 C001，就為 1/3 與 1/1；這是**條件算例**，不是宣稱實測排名已命中。

若 R 為空，輸出 precision／recall 為 null，另外記錄 `returned_on_no_answer`。Q03 很可能仍回傳兩段閘道器文字；它說明 top-k 只會找相近候選，不會自動拒答。Q08 的 SQL 合格集合真的為空，應回零筆，這兩種「空答案」要分清。

有索引時還會回傳 `ann_overlap_with_exact`，它的分母是 exact 回傳數，不是人工 relevant 數。不要把這兩種 recall 混在同一個圖表。也不要看完這八題就選一個距離閾值，宣稱能處理所有無答案問題；要另有標註驗證集與拒答策略。

---

## Workshop

### 題目

15 分鐘：合格集合 5 分鐘、八題評估 6 分鐘、錯誤分析 4 分鐘。

1. 執行分類 1 的合格集合，核對十列且無重複。
2. 對 Q03、Q04 比較實際候選與不同的 qrels，圈出原文的否定。
3. 寫出 Q01 一次 precision／recall 計算，保留實際 IDs。
4. 執行 Q08，核對 rows 為空，不跨分類補滿。

### 預期輸出

```text
category 1: 10 unique chunks
Q03/Q05: 無人工相關答案，但檢索仍可能回傳候選
Q08: rows=[]
八題結果均保留；未命中也不得改標註掩蓋
```

### 解答

[21 Workshop 解答](workshop/21-filters-evaluation.md)。只有「功能回傳了文字」不算通過，必須能指出資格、相關性和使用限制。

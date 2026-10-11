# 21 篩選與評估：相似段落不等於可用答案

> **定位**：以 Ch5–9 的 JOIN、EXISTS、WHERE、NULL 與聚合，先定義合格集合，再用人工 qrels 評估；Python 只是執行工具。

[上一節](20-ann.md) · [下一節](22-consistency.md)

## 學習目標

- 用 EXISTS 避免多產品 JOIN 讓同一 chunk 重複占位。
- 同時檢查文件 active、產品 active、分類條件。
- 分清 precision／recall、空 qrels、空合格集合與拒答。

## 1. 先用 SQL 形成唯一合格集合

```sql
SET @category=1;
SELECT c.chunk_id,c.document_id
FROM chunks c JOIN documents d ON d.document_id=c.document_id
WHERE d.status='active' AND EXISTS (
  SELECT 1 FROM product_documents pd JOIN products p ON p.product_id=pd.product_id
  WHERE pd.document_id=d.document_id AND p.status='active'
    AND (@category IS NULL OR p.category_id=@category)
)
ORDER BY c.chunk_id;
```

分類 1 預期十個唯一 chunk；D003 因文件 inactive 排除，D004 因仍有 active P007 保留。直接 JOIN 會使 D001 的每個 chunk 出現兩列。

## 2. Code section：完成 Q01／Q08 評估（Python 可選）

```python
from pathlib import Path
from vector_course import evaluate, search

artifact_path = Path.home() / "mariadb-vectors.json"
# TODO 1：執行 Q01 的 exact top-k，保留實際唯一 IDs。
q01_rows = None
# TODO 2：執行 Q08，確認 category=999 不跨分類補滿。
q08_rows = None
print("Q01 =", [r["chunk_id"] for r in q01_rows])
print("Q08 =", [r["chunk_id"] for r in q08_rows])
```

提示：完整八題可用 `python vector_course.py evaluate --artifact ... --k 3`；qrels 是獨立人工標註，不能由排名反推。

## 3. 執行、驗證、交付

Q03 與 Q04 都可能含 5 GHz，但需求相反：Q03 的 relevant 集合空，Q04 可為 C003/C004。Q08 的 SQL 合格集合必須零列。若 R 非空，`precision@k=|R∩S|/k`、`recall@k=|R∩S|/|R|`；R 空時兩者 null，另記 returned_on_no_answer。未命中不修改 qrels。

## 交件

交付合格集合 SQL、code section、Q01/Q08 IDs、八題實際結果與一個 precision／recall 計算。說明相似度不能取代型號、否定與安全規則。

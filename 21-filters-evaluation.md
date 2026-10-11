# 21 篩選與評估：合格集合先於排名

> 本章完全使用 MariaDB client 與 SQL，不需要 Python。先建立不重複的合格 chunk 集合，再用固定 qrels 理解 precision／recall 與無答案案例。

## 1. 為什麼先用 EXISTS

同一份文件可能連到多個 active products。直接 JOIN 會讓同一個 chunk 重複；先用 `EXISTS` 才能讓一個 chunk 只出現一次。

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/21-filters-evaluation.sql
```

核心查詢：

```sql
SET @category = 1;
SELECT c.chunk_id,c.document_id
FROM chunks c JOIN documents d ON d.document_id=c.document_id
WHERE d.status='active' AND EXISTS (
  SELECT 1 FROM product_documents pd JOIN products p ON p.product_id=pd.product_id
  WHERE pd.document_id=d.document_id AND p.status='active'
    AND (@category IS NULL OR p.category_id=@category)
)
ORDER BY c.chunk_id;
```

分類 1 預期有 10 個唯一 chunk；分類 999 預期 0 筆。

## 2. 固定 qrels

`data/search_cases.json` 是教師審核用的標註來源；課堂使用 SQL 版固定標註，不執行 Python 評估程式。Q03、Q05、Q08 是空相關集合，不能為了湊滿 top-k 而自行補答案。

執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/21-evaluation-sql.sql
```

這個 SQL 會顯示合格集合與各案例的人工相關數量。它不宣稱模型排名已完成；排名結果要以第 19、20 章保存的 SQL 輸出為準。

## Workshop

1. 執行合格集合 SQL，確認分類 1 無重複且為 10 筆。
2. 執行 SQL evaluation，確認 Q01、Q02、Q04、Q06、Q07 有標註，Q03、Q05、Q08 可為空。
3. 說明空 qrels 與空合格集合的差異。
4. 不使用 Python，不把相似段落自動當成正確答案。

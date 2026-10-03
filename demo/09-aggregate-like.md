# 09 統計與 LIKE：先算對，再看搜尋漏了什麼

> **定位**：用 `GROUP BY`、`HAVING` 與正確的 `COUNT` 單位產生報表，並理解 `LIKE` 的搜尋限制。

## 學習目標

完成本節後，你應該能夠：

- 用 `COUNT`、`SUM`、`AVG` 與 `GROUP BY` 產生統計
- 分辨 `WHERE` 與 `HAVING` 的用途
- 在 `LEFT JOIN` 中選擇正確的 `COUNT` 寫法
- 說明 JOIN 後為什麼要重新確認統計單位
- 用 `LIKE` 找文字，但不把命中直接當成語意答案

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

---

## 情境

主管想知道各分類的販售中產品數量、庫存與平均價格；文件管理者想知道哪些產品沒有有效 SOP。客服又想搜尋「恢復出廠設定」與「支援 5 GHz」。

這些問題不能只看有沒有結果：

```text
統計要先確認一列代表什麼
LIKE 只做文字比對，不理解同義詞或否定
```

本節只讀取資料，不修改正式 checkpoint。

---

## 講解

### 1. WHERE、GROUP BY 與統計函式

在 Ubuntu shell 執行公開 demo，或登入後逐句執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  --default-character-set=utf8mb4 \
  mariadb_workshop_2026 < demo/09-aggregate-like.sql
```

依分類統計販售中的產品：

```sql
SELECT category_id,
       COUNT(*) AS product_count,
       SUM(stock) AS total_stock,
       ROUND(AVG(price), 2) AS average_price
FROM products
WHERE status = 'active'
GROUP BY category_id
ORDER BY category_id;
```

預期：

```text
category 1：7 / 67 / 1112.86
category 2：2 / 13 / 1275.00
category 3：1 / 30 / 900.00
```

執行順序可以先記成：

```text
WHERE：先篩選資料列
GROUP BY：再分組
COUNT／SUM／AVG：對每組計算
```

`AVG(price)` 是算術平均價格，不是營收，也不是依庫存加權的平均。

### 2. WHERE 與 HAVING

只保留至少有兩個販售中產品的分類：

```sql
SELECT category_id,
       COUNT(*) AS product_count,
       SUM(stock) AS total_stock,
       ROUND(AVG(price), 2) AS average_price
FROM products
WHERE status = 'active'
GROUP BY category_id
HAVING COUNT(*) >= 2
ORDER BY category_id;
```

預期只剩分類 1、2。

```text
WHERE：篩選單筆資料
HAVING：篩選分組後的結果
```

不能寫：

```sql
WHERE COUNT(*) >= 2
```

### 3. LEFT JOIN 中的 COUNT

查每個產品有幾份有效 SOP：

```sql
SELECT p.product_id,
       COUNT(d.document_id) AS active_sops
FROM products AS p
LEFT JOIN product_documents AS pd
  ON pd.product_id = p.product_id
LEFT JOIN documents AS d
  ON d.document_id = pd.document_id
 AND d.status = 'active'
GROUP BY p.product_id
ORDER BY p.product_id;
```

預期：

```text
P001 = 2
P003 = 0
P010 = 0
其他產品 = 1
```

P010 的 `LEFT JOIN` 補位列看起來像一列，但右側 `document_id` 是 `NULL`：

```sql
COUNT(*)              -- 會算補位列
COUNT(d.document_id)  -- 不會算 NULL
```

因此，這個需求應使用：

```sql
COUNT(d.document_id)
```

### 4. JOIN 後確認統計單位

```sql
SELECT pd.product_id,
       COUNT(*) AS joined_rows,
       COUNT(DISTINCT pd.document_id) AS documents
FROM product_documents AS pd
JOIN chunks AS ch
  ON ch.document_id = pd.document_id
WHERE pd.product_id = 'P001'
GROUP BY pd.product_id;
```

預期：

```text
joined_rows = 4
documents = 2
```

P001 有 2 份文件，每份文件有 2 個段落，所以 JOIN 後有 4 列。

```text
COUNT(*)                         → JOIN 後的列數
COUNT(DISTINCT document_id)      → 不同文件數
COUNT(DISTINCT chunk_id)         → 不同段落數
```

寫報表前先問：

> 一列代表產品、文件，還是段落？

不要用 `DISTINCT` 掩蓋錯誤的 JOIN；先確認 `ON` 條件與統計單位。

### 5. LIKE 是字串搜尋

```sql
SELECT chunk_id
FROM chunks
WHERE `text` LIKE '%重設%'
ORDER BY chunk_id;

SELECT chunk_id
FROM chunks
WHERE `text` LIKE '%恢復出廠設定%'
ORDER BY chunk_id;
```

預期：

```text
重設：C001
恢復出廠設定：Empty set
```

`LIKE` 只找文字中是否出現指定片語，不知道：

```text
重設 ≈ 恢復出廠設定
```

所以沒有命中只代表這個字串模式沒找到，不代表知識庫沒有相關概念。

### 6. 命中也不一定是答案

```sql
SELECT chunk_id, `text`
FROM chunks
WHERE `text` LIKE '%支援 5 GHz%'
ORDER BY chunk_id;
```

預期：

```text
C003
C004
```

但兩段原文都包含：

```text
不支援 5 GHz
```

所以：

```text
LIKE 命中 ≠ 正面支持
```

必須讀回原文，確認它是在支持、否定，還是有條件地支持。這裡不要只看命中筆數就回答「支援 5 GHz」。

最後可核對資料完整性：

```sql
SELECT COUNT(*) AS bad_hashes
FROM chunks
WHERE BINARY content_hash <> BINARY SHA2(`text`, 256);
```

預期：

```text
bad_hashes = 0
```

---

## Workshop

### 題目

在 `mariadb_workshop_2026` 完成以下唯讀查詢：

1. 輸出販售中產品的分類、產品數、總庫存與平均價格。
2. 用 `HAVING` 找至少有兩個販售中產品的分類。
3. 用 `LEFT JOIN` 找有效 SOP 數量為零的產品，並說明為何使用 `COUNT(d.document_id)`。
4. 對 P010 同時列出 `COUNT(*)` 與 `COUNT(d.document_id)`。
5. 依序搜尋「重設」、「恢復出廠設定」、「支援 5 GHz」，第三個查詢保存原文。
6. 核對 chunk hash，確認 `bad_hashes = 0`。

### 預期輸出

```text
category 1：7 / 67 / 1112.86
category 2：2 / 13 / 1275.00
zero active SOPs：P003 / 0、P010 / 0
P010：COUNT(*) = 1、COUNT(d.document_id) = 0
重設：C001
恢復出廠設定：zero rows
支援 5 GHz：C003、C004，原文都表示不支援
bad_hashes = 0
```

### 交件

提交：

- 統計查詢與結果
- `WHERE`／`GROUP BY`／`HAVING` 的說明
- `COUNT(*)` 與 `COUNT(d.document_id)` 的比較
- 三次 `LIKE` 查詢與第三次的原文
- 同義詞漏失與否定命中的各一句結論

本節為唯讀練習，不要修改資料或提交密碼。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

# 08 跨表查詢：保留沒有 SOP 的產品

> **定位**：用主鍵／外鍵跨表查詢，分辨 `INNER JOIN`、`LEFT JOIN`，並理解 `ON`、`WHERE` 與 `NULL` 的差異。

## 學習目標

完成本節後，你應該能夠：

- 用表別名與 `ON` 寫出跨表查詢
- 用 `INNER JOIN` 查有配對的資料
- 用 `LEFT JOIN` 保留沒有配對的產品
- 用 `IS NULL` 找完全沒有關聯的產品
- 說明條件放在 `ON` 或 `WHERE` 造成的結果差異
- 解釋 JOIN 後為什麼可能出現多列

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

---

## 情境

客服需要查詢「產品可以使用的 SOP」。文件管理者則需要看到「所有產品」，即使某個產品目前沒有 SOP 也不能消失。

兩種需求都會查詢 `products` 與 `documents`，但使用的 JOIN 不同：

```text
INNER JOIN：只保留有配對的資料
LEFT JOIN：保留左邊的所有資料
```

本節只讀取資料，不建立新表，也不修改正式 checkpoint。

---

## 講解

### 1. 用 JOIN 取得分類名稱

```sql
SELECT p.product_id,
       p.name,
       c.name AS category_name
FROM products AS p
INNER JOIN categories AS c
  ON c.category_id = p.category_id
WHERE p.product_id IN ('P001', 'P004', 'P011')
ORDER BY p.product_id;
```

`p`、`c` 是表別名：

```text
p.name → products.name
c.name → categories.name
```

`ON` 說明兩張表如何配對；`WHERE` 篩選配對後要留下的資料。

### 2. 經過關聯表查詢文件

產品和文件是多對多，必須經過 `product_documents`：

```sql
SELECT p.product_id,
       d.document_id,
       d.title
FROM products AS p
INNER JOIN product_documents AS pd
  ON pd.product_id = p.product_id
INNER JOIN documents AS d
  ON d.document_id = pd.document_id
WHERE p.product_id IN ('P001', 'P010')
ORDER BY p.product_id, d.document_id;
```

預期：

```text
P001 / D001
P001 / D005
```

P010 不會出現，因為它沒有 `product_documents` 配對。它不是不存在，而是 `INNER JOIN` 只保留能匹配的資料。

### 3. 用 LEFT JOIN 保留沒有文件的產品

```sql
SELECT p.product_id,
       d.document_id
FROM products AS p
LEFT JOIN product_documents AS pd
  ON pd.product_id = p.product_id
LEFT JOIN documents AS d
  ON d.document_id = pd.document_id
WHERE p.product_id IN ('P001', 'P010')
ORDER BY p.product_id, d.document_id;
```

預期：

```text
P001 / D001
P001 / D005
P010 / NULL
```

`P010 / NULL` 表示右側沒有匹配資料，不是一份「空文件」。左側的 `products` 被保留下來，右側欄位以 `NULL` 表示缺少配對。

### 4. 用 IS NULL 找完全沒有關聯的產品

```sql
SELECT p.product_id
FROM products AS p
LEFT JOIN product_documents AS pd
  ON pd.product_id = p.product_id
WHERE pd.document_id IS NULL
ORDER BY p.product_id;
```

預期：

```text
P010
```

不能寫：

```sql
WHERE pd.document_id = NULL
```

`NULL` 不是一般文字或數字，要使用：

```sql
IS NULL
```

注意：P003 有關聯，只是 D003 已停用，所以 P003 不是「完全沒有關聯」。

### 5. 條件放在 ON 或 WHERE

如果需求是「保留所有產品，但只顯示有效 SOP」，把文件狀態條件放在 `ON`：

```sql
SELECT p.product_id,
       d.document_id
FROM products AS p
LEFT JOIN product_documents AS pd
  ON pd.product_id = p.product_id
LEFT JOIN documents AS d
  ON d.document_id = pd.document_id
 AND d.status = 'active'
ORDER BY p.product_id, d.document_id;
```

預期共有 13 列，P003／NULL 與 P010／NULL 都保留。

如果改成：

```sql
LEFT JOIN documents AS d
  ON d.document_id = pd.document_id
WHERE d.status = 'active'
```

最後的 `WHERE` 會排除 `d.status` 為 `NULL` 的列，結果只剩 11 列，P003 與 P010 消失。

記法：

```text
ON：決定右表哪些資料可以配對
WHERE：JOIN 後再篩選結果
```

### 6. JOIN 後列數增加是正常的

```sql
SELECT p.product_id,
       d.document_id,
       ch.chunk_id
FROM products AS p
JOIN product_documents AS pd
  ON pd.product_id = p.product_id
JOIN documents AS d
  ON d.document_id = pd.document_id
JOIN chunks AS ch
  ON ch.document_id = d.document_id
WHERE p.product_id IN ('P001', 'P002')
ORDER BY p.product_id, d.document_id, ch.chunk_id;
```

此時一列代表：

```text
產品 + 文件 + 段落
```

P001 與 P002 合計會有 6 列，但只有 4 個不同的 `chunk_id`。這不是資料重複錯誤，而是 JOIN 展開了一對多關係。

不要先用 `DISTINCT` 掩蓋錯誤的 `ON`；先確認一列應該代表什麼。

---

## Workshop

### 題目

在 `mariadb_workshop_2026` 完成以下唯讀查詢：

1. 查販售中產品與有效 SOP，只輸出 `product_id`、`document_id`。
2. 查所有產品，只讓有效 SOP 配對，保留沒有有效 SOP 的產品。
3. 找完全沒有任何關聯的產品，使用 `IS NULL`。
4. 將第 2 題的文件狀態條件移到 `WHERE`，比較少了哪些產品。
5. 查 P001、P002 接上 chunks 後的列數，說明一列代表什麼。

### 預期輸出

```text
有效配對：10 組
所有產品 + 有效 SOP：13 列
完全沒有關聯：P010
狀態條件放 WHERE：11 列，P003、P010 消失
P001、P002 接 chunks：6 列，但只有 4 個不同 chunk_id
```

### 交件

提交：

- 五個查詢的 SQL 與結果
- `INNER JOIN` 與 `LEFT JOIN` 的差異說明
- `ON` 與 `WHERE` 版本的列數比較
- 一段說明：為什麼 P003 不是完全沒有關聯

本節為唯讀練習，不要修改資料或提交密碼。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

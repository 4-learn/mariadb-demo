# 14 索引與 EXPLAIN：理解查詢的存取路徑

> **定位**：在隔離練習表建立複合索引，用 `EXPLAIN` 看查詢路徑，並把路徑與結果正確性分開驗證。

## 學習目標

完成本節後，你應該能夠：

- 依等值、範圍與排序條件安排複合索引欄位
- 用 `EXPLAIN` 閱讀 `possible_keys`、`key`、`type` 與 `rows`
- 分辨索引可用和查詢一定變快是兩件事
- 理解最左前綴與索引的寫入維護成本
- 不用小資料表的一次耗時宣稱效能提升

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

本節索引 DDL 使用 `course_editor`；不要讓 `course_app` 建索引。

---

## 情境

客服要查詢：

```text
販售中的感測器
價格 700～1300
取最便宜三項
```

正式資料只有 12 筆，全表掃描也很快。因此本節練習的是：

```text
索引能提供什麼查詢路徑？
optimizer 是否選用它？
結果是否和不使用索引時相同？
```

不是用一次毫秒數宣稱「一定快十倍」。本節使用隔離的：

```text
practice_index_products
```

不修改正式 `products` 的索引或資料。

---

## 講解

### 1. 建立隔離練習表

在自己的 VM 執行公開 demo 檔案：

```text
demo/14-indexes.sql
```

```bash
cd ~/workspace/mariadb-demo
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/14-indexes.sql
```

這個檔案使用 `course_editor`，會建立並準備 `practice_index_products`，不會修改正式 `products`。

也可以先登入確認：

```sql
SELECT DATABASE(), CURRENT_USER();
```

應為：

```text
mariadb_workshop_2026
course_editor@localhost
```

`CREATE TABLE`、`CREATE INDEX` 是 DDL，可能隱含提交；不要期待外層 `ROLLBACK` 移除表或索引。

### 2. 依查詢需求建立複合索引

公開 demo 會建立：

```sql
CREATE INDEX IF NOT EXISTS idx_practice_category_status_price
ON practice_index_products(category_id, status, price, product_id);
```

欄位順序的想法是：

```text
category_id：等值條件
status：等值條件
price：範圍條件
product_id：同價時的排序鍵
```

查詢：

```sql
SELECT product_id, price
FROM practice_index_products
WHERE category_id = 1
  AND status = 'active'
  AND price BETWEEN 700 AND 1300
ORDER BY price, product_id
LIMIT 3;
```

結果應為：

```text
P001  800.00
P002  1200.00
P008  1250.00
```

SQL 條件寫在前或後，不會決定索引欄位順序；索引定義才會影響可用前綴。

### 3. 用 EXPLAIN 比較路徑

公開 demo 的 `demo/14-indexes.sql` 已包含不使用索引與 optimizer 自由選擇的 EXPLAIN：

```sql
EXPLAIN
SELECT product_id, price
FROM practice_index_products
IGNORE INDEX (idx_practice_category_status_price)
WHERE category_id = 1
  AND status = 'active'
  AND price BETWEEN 700 AND 1300
ORDER BY price, product_id
LIMIT 3;
```

以及：

```sql
EXPLAIN
SELECT product_id, price
FROM practice_index_products
WHERE category_id = 1
  AND status = 'active'
  AND price BETWEEN 700 AND 1300
ORDER BY price, product_id
LIMIT 3;
```

閱讀重點：

```text
possible_keys：可能考慮的索引，不代表實際使用
key：實際選中的索引，可能是 NULL
type：ALL、range、ref、index 等路徑
rows：optimizer 估計的列數，不是實際回傳筆數
Extra：額外篩選、排序或 covering 資訊
```

12 筆資料很少，optimizer 選全表掃描也可能是合理決定。自動 plan 沒選索引不等於索引壞掉。

### 4. FORCE INDEX 只用來教學

Workshop 檔案是：

```text
workshop/14-indexes.sql
```

其中會執行：

```sql
EXPLAIN
SELECT product_id, price
FROM practice_index_products
FORCE INDEX (idx_practice_category_status_price)
WHERE category_id = 1
  AND status = 'active'
  AND price BETWEEN 700 AND 1300
ORDER BY price, product_id
LIMIT 3;
```

`FORCE INDEX` 只證明這條索引能提供一條路徑，不是正式系統的優化建議。正式效能需要接近實際資料量、分布、並行量與快取狀態的重複測量。

### 5. 觀察最左前綴

Workshop 也會比較只用價格的查詢：

```sql
EXPLAIN
SELECT product_id, price
FROM practice_index_products
WHERE price BETWEEN 700 AND 1300
ORDER BY price, product_id
LIMIT 3;
```

索引第一欄是 `category_id`，省略它時就不是同樣的最左前綴查找。server 可能選全表或其他路徑；這不是索引損壞。

索引也有成本：

```text
佔用空間
INSERT 需要維護
UPDATE 可能維護
DELETE 也要維護
```

### 6. 驗證索引欄位順序與結果

```sql
SELECT INDEX_NAME, SEQ_IN_INDEX, COLUMN_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'practice_index_products'
  AND INDEX_NAME = 'idx_practice_category_status_price'
ORDER BY SEQ_IN_INDEX;
```

應看到：

```text
1 category_id
2 status
3 price
4 product_id
```

加不加索引都必須得到相同的前三筆資料。索引不能修補漏掉 `WHERE` 或錯誤的排序條件。

---

## Workshop

### 題目

在自己的 VM 完成：

1. 執行 `demo/14-indexes.sql`，建立隔離練習表與索引。
2. 執行 `workshop/14-indexes.sql`，保存 IGNORE、自由選擇與 FORCE 的實際 plan。
3. 比較三種 plan 的 `key`、`type`、`rows`。
4. 核對查詢前三筆相同，並列出索引四欄順序。
5. 閱讀只使用 `price` 的變形查詢，說明最左前綴限制。
6. 寫一句保守結論，不使用「有索引一定比較快」。

執行：

```bash
cd ~/workspace/mariadb-demo
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/14-indexes.sql
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < workshop/14-indexes.sql
```

### 預期輸出

```text
P001  800.00
P002  1200.00
P008  1250.00
```

索引順序：

```text
category_id, status, price, product_id
```

EXPLAIN 的 `rows` 依環境而定；要求保存實際值。IGNORE 不使用指定索引，FORCE 能使用指定索引，三種 SELECT 的結果語意相同。

### 交件

提交：

- 三種 EXPLAIN 的實際輸出
- 三種查詢的前三筆結果
- 索引欄位順序
- 只用 price 的 plan 說明
- 一句保守的效能結論

不要讓 `course_app` 建索引，不要修改正式 `products`，不要提交私人設定檔。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

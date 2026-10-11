# 14 索引與 EXPLAIN：理解查詢的存取路徑

> **定位**：在隔離練習表建立複合索引，用 `EXPLAIN` 看查詢路徑，並把路徑與結果正確性分開驗證。

## 學習目標

完成本節後，你應該能夠：

- 依等值、範圍與排序條件安排複合索引欄位
- 用 `EXPLAIN` 閱讀 `possible_keys`、`key`、`type` 與 `rows`
- 分辨索引可用和查詢一定變快是兩件事
- 比較索引與全表掃描的查詢路徑
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

公開 demo 的 `demo/14-indexes.sql` 已包含不使用索引與 optimizer 自由選擇的 `EXPLAIN`：

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

白話說，`EXPLAIN` 像是查詢的 dry run：它不會真的執行查詢，也不會修改資料，只先顯示 MariaDB 預計採用的執行方式。這不是查詢結果，也不是完整的執行 log。

它主要告訴你：

```text
要讀哪張表
要不要使用索引
預計掃描多少資料
需不需要額外排序
```

`EXPLAIN` 本身不會修改資料，也不是實際查詢結果；它是 MariaDB 對「將如何執行這個查詢」的說明。

#### 實際 EXPLAIN 輸出

```text
+------+-------------+-------------------------+------+---------------+------+---------+------+------+-----------------------------+
| id   | select_type | table                   | type | possible_keys | key  | key_len | ref  | rows | Extra                       |
+------+-------------+-------------------------+------+---------------+------+---------+------+------+-----------------------------+
|    1 | SIMPLE      | practice_index_products | ALL  | NULL          | NULL | NULL    | NULL | 12   | Using where; Using filesort |
+------+-------------+-------------------------+------+---------------+------+---------+------+------+-----------------------------+
```

`rows` 會依資料量與 optimizer 判斷而變動，請以自己的實際輸出為準。

#### 欄位解說

| 欄位 | 這次的值 | 意思 |
|---|---|---|
| `id` | `1` | 查詢區塊編號 |
| `select_type` | `SIMPLE` | 這是一個基本查詢，沒有包在另一個查詢裡。 |
| `table` | `practice_index_products` | 讀取的資料表 |
| `type` | `ALL` | 全表掃描 |
| `possible_keys` | `NULL` | 這次沒有可考慮使用的索引 |
| `key` | `NULL` | 實際沒有使用索引 |
| `key_len` | `NULL` | 沒有使用索引，因此沒有鍵長度 |
| `ref` | `NULL` | 沒有索引參照值 (JOIN ON) |
| `rows` | `12` | optimizer 預估查看的列數，不是實際回傳筆數 (代表 MariaDB 預估需要查看約 12 筆資料，不是說最後會回傳 12 筆。) |
| `Extra` | `Using where; Using filesort` | 用 WHERE 篩選，並需要額外排序 |

這份執行計畫表示：這次查詢沒有使用索引，會掃描整張練習表，再套用條件並排序。

接著移除 `IGNORE INDEX`，讓 MariaDB 自己選擇查詢路徑，再比較兩次 `EXPLAIN` 的 `key`、`type`、`rows` 與 `Extra` 是否不同：

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

![image](https://hackmd.io/_uploads/ryFnutdife.png)


比較:

![image](https://hackmd.io/_uploads/BkkndKOjzx.png)



#### 第二次 EXPLAIN 的實際輸出

```text
+------+-------------+-------------------------+-------+------------------------------------+------------------------------------+---------+------+------+--------------------------+
| id   | select_type | table                   | type  | possible_keys                      | key                                | key_len | ref  | rows | Extra                    |
+------+-------------+-------------------------+-------+------------------------------------+------------------------------------+---------+------+------+--------------------------+
|    1 | SIMPLE      | practice_index_products | range | idx_practice_category_status_price | idx_practice_category_status_price | 10      | NULL | 5    | Using where; Using index |
+------+-------------+-------------------------+-------+------------------------------------+------------------------------------+---------+------+------+--------------------------+
```

這次的欄位意思仍然相同；不同的是 MariaDB 自己選擇使用索引：

| 欄位 | 第二次的值 | 意思 |
|---|---|---|
| `id` | `1` | 查詢區塊編號 |
| `select_type` | `SIMPLE` | 這是一個基本查詢，沒有包在另一個查詢裡。 |
| `table` | `practice_index_products` | 讀取的資料表 |
| `type` | <span style="color:red">`range`</span> | <span style="color:red">使用索引範圍查找</span> |
| `possible_keys` | <span style="color:red">`idx_practice_category_status_price`</span> | <span style="color:red">這個索引可以用來協助查詢</span> |
| `key` | <span style="color:red">`idx_practice_category_status_price`</span> | <span style="color:red">實際選用的索引</span> |
| `key_len` | <span style="color:red">`10`</span> | <span style="color:red">使用到的索引鍵長度</span> |
| `ref` | `NULL` | 沒有使用索引參照值 |
| `rows` | <span style="color:red">`5`</span> | <span style="color:red">optimizer 預估查看 5 列，不是實際回傳筆數</span> |
| `Extra` | <span style="color:red">`Using where; Using index`</span> | <span style="color:red">用 WHERE 篩選，並可直接從索引取得查詢需要的欄位</span> |

#### 兩次執行計畫的差異

| 欄位 | 不使用索引 | MariaDB 自己選擇 |
|---|---|---|
| `type` | `ALL` | <span style="color:red">`range`</span> |
| `key` | `NULL` | <span style="color:red">`idx_practice_category_status_price`</span> |
| `rows` | `12` | <span style="color:red">`5`</span> |
| `Extra` | `Using where; Using filesort` | <span style="color:red">`Using where; Using index`</span> |

白話說：不使用索引時，MariaDB 估計要掃描整張表；讓 MariaDB 自己選擇時，改用索引範圍查找，估計只需查看較少的資料列，也不需要額外排序。實際 `rows` 會依資料量與 optimizer 判斷而變動，請以自己的輸出為準。

---

## Workshop

### 題目

在自己的 VM 完成：

1. 執行 `demo/14-indexes.sql`，建立隔離練習表與索引。
2. 執行 `workshop/14-indexes.sql`，保存 optimizer 自由選擇與查詢結果。
3. 比較兩種 plan 的 `key`、`type`、`rows`。
4. 核對查詢前三筆相同。
5. 寫一句保守結論，不使用「有索引一定比較快」。

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

EXPLAIN 的 `rows` 依環境而定；要求保存實際值。兩種 SELECT 的結果語意相同，但執行計畫可能不同。

### 交件

提交：

- 兩種 EXPLAIN 的實際輸出
- 兩種查詢的前三筆結果
- 一句保守的效能結論

不要讓 `course_app` 建索引，不要修改正式 `products`，不要提交私人設定檔。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

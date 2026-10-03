# 07 修改與刪除：讓 WHERE 保護操作範圍

> **定位**：先預覽，再用 `WHERE` 限縮 `UPDATE`／`DELETE`，最後核對影響筆數與回滾結果。

## 學習目標

完成本節後，你應該能夠：

- 把 `SELECT` 的條件帶入 `UPDATE` 與 `DELETE`
- 用 ID 與庫存條件保護修改範圍
- 用 `ROW_COUNT()` 判斷實際修改筆數
- 分辨停用資料與刪除資料
- 用 `ROLLBACK` 清除本次練習資料

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

---

## 情境

倉庫有一個練習感測器 P901，庫存 10 件；練習配件 P902，庫存 3 件。

客服要領出 4 件感測器，並停用不再使用的配件。你要避免：

- 沒有 `WHERE` 而修改整張表
- 庫存不足時扣成負數
- 把停用誤當成刪除
- 只看到 SQL 沒報錯，就以為業務動作成功

本節只修改 `practice_inventory_07`，不修改正式 `products`。

---

## 講解

### 1. 建立本節練習表

本節使用獨立的：

```text
practice_inventory_07
```

在 Ubuntu shell 執行公開 demo：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  --default-character-set=utf8mb4 \
  mariadb_workshop_2026 < demo/07-update-delete.sql
```

這個示範會建立練習表、加入 P901／P902、修改資料、查詢結果，最後回滾資料列。表結構會保留，正式 `products` 不會變動。

確認身分：

```sql
SELECT DATABASE() AS current_database,
       CURRENT_USER() AS account;
```

應是：

```text
mariadb_workshop_2026
course_editor@localhost
```

### 2. 先 SELECT 預覽，再 UPDATE

先確認要修改的資料：

```sql
SELECT product_id, stock
FROM practice_inventory_07
WHERE product_id = 'P901'
  AND stock >= 2;
```

再執行修改：

```sql
UPDATE practice_inventory_07
SET stock = stock - 2
WHERE product_id = 'P901'
  AND stock >= 2;
```

立刻查影響筆數：

```sql
SELECT ROW_COUNT() AS changed_rows;
```

預期：

```text
changed_rows = 1
```

`SET stock = stock - 2` 是從目前庫存扣 2，不是把庫存直接設定成 2。`WHERE` 同時保護產品 ID 與庫存條件。

### 3. 0 列不是語法錯誤

測試庫存不足：

```sql
UPDATE practice_inventory_07
SET stock = stock - 99
WHERE product_id = 'P901'
  AND stock >= 99;

SELECT ROW_COUNT() AS insufficient_stock_rows;
```

預期：

```text
insufficient_stock_rows = 0
```

SQL 語法合法，但沒有資料符合條件，所以沒有任何資料被修改。若程式只看「沒有 exception」就顯示成功，仍然是錯誤的業務判斷。

### 4. 停用和 DELETE 不同

先停用 P902：

```sql
UPDATE practice_inventory_07
SET status = 'inactive'
WHERE product_id = 'P902'
  AND status = 'active';

SELECT ROW_COUNT() AS deactivated_rows;

SELECT product_id, stock, status
FROM practice_inventory_07
ORDER BY product_id;
```

預期 P902 還存在，但狀態變成 `inactive`。

再刪除已停用的 P902：

```sql
DELETE FROM practice_inventory_07
WHERE product_id = 'P902'
  AND status = 'inactive';

SELECT ROW_COUNT() AS deleted_rows;
```

此時 P902 才真正從表中消失。

### 5. 重複 DELETE 與 ROLLBACK

再執行一次相同 DELETE：

```sql
DELETE FROM practice_inventory_07
WHERE product_id = 'P902'
  AND status = 'inactive';

SELECT ROW_COUNT() AS second_delete_rows;
```

預期：

```text
second_delete_rows = 0
```

最後回滾：

```sql
ROLLBACK;

SELECT COUNT(*) AS remaining_rows
FROM practice_inventory_07;

SELECT product_id, stock
FROM products
WHERE product_id IN ('P001', 'P002')
ORDER BY product_id;
```

預期：

```text
remaining_rows = 0
P001 / 10
P002 / 20
```

`ROLLBACK` 會清除本次交易新增與修改的練習資料；`practice_inventory_07` 表仍存在，正式 `products` 也不受影響。

---

## Workshop

### 題目

在 `mariadb_workshop_2026` 完成以下任務：

1. 用全新交易建立 P901／10 與 P902／3。
2. 先預覽 P901，再扣 4 件，保留 `ROW_COUNT()`。
3. 嘗試扣 99 件，確認為 0 列。
4. 將 P902 設為 `inactive`，確認它仍存在。
5. 用 ID 與 `inactive` 條件刪除 P902，再重複刪除一次。
6. `ROLLBACK` 後確認練習表為空，並確認正式 P001／P002 沒有改變。

### 預期輸出

```text
changed_rows = 1
insufficient_stock_rows = 0
deactivated_rows = 1
P901 / 6 / active
P902 / 3 / inactive
deleted_rows = 1
second_delete_rows = 0
remaining_rows = 0
P001 / 10
P002 / 20
```

### 交件

提交：

- 預覽 SQL 與實際結果
- UPDATE／DELETE 的 SQL 與 `ROW_COUNT()`
- ROLLBACK 後的資料筆數
- 一段說明：為什麼預覽不能取代 UPDATE 裡的條件

不要提交密碼或私人設定檔內容，也不要修改正式資料。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

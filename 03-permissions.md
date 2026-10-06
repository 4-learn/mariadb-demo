# 03 權限界線：可以讀，不代表可以改

> **定位**：用受限帳號確認「可以讀取、不能修改」，並留下資料沒有被改動的證據。

## 學習目標

完成本節後，你應該能夠：

- 分辨 Ubuntu 的 `sudo` 與 MariaDB 的帳號權限
- 查看目前帳號的授權摘要
- 辨認 `ERROR 1142` 的 UPDATE 權限拒絕
- 核對拒絕前後資料都沒有改變

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：本節使用的課程資料與示範程式。
- [本節 SQL 示範](demo/03-permissions.sql)：逐句執行，觀察每個結果。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

---

## 情境

客服查價工具只需要讀取產品，不應該更改庫存。

即使你在 Ubuntu VM 有 `sudo`，查價工具也不應該使用資料庫管理員帳號。這一節要證明：允許的讀取可以成功，不允許的修改會被拒絕。

---

## 講解

### 1. `sudo` 與 MariaDB 帳號不同

`sudo` 是 Ubuntu 的管理權限；MariaDB 則用資料庫帳號與授權控制讀取、修改及管理操作。

本課使用：

```text
course_reader@localhost
```

這是 MariaDB 帳號，不是 Ubuntu 使用者。查詢時不要加 `sudo`，也不要改用 root。

### 2. 登入並查看授權

如果尚未登入，在 Ubuntu shell 執行：

```bash
mariadb --no-defaults --default-character-set=utf8mb4 --protocol=socket --user=course_reader --password mariadb_course
```

![image](https://hackmd.io/_uploads/H1tpQLC5zg.png)

在 MariaDB prompt 執行：

```sql
SELECT VERSION() AS server_version,
       DATABASE() AS current_database,
       CURRENT_USER() AS account;

SELECT * FROM course_meta;
SHOW GRANTS FOR CURRENT_USER;
```

![image](https://hackmd.io/_uploads/ByEyEUC5fx.png)

應確認：

```text
current_database：mariadb_course
account：          course_reader@localhost
dataset_version：  products-v1
```

`SHOW GRANTS` 會列出目前帳號的授權語句。不要貼完整畫面或輸出；先用下表讀懂每一行：

| 輸出片段 | 意思 |
| --- | --- |
| `course_reader@localhost` | MariaDB 帳號名稱與登入來源；不是 Ubuntu 使用者名稱 |
| `GRANT USAGE ON *.*` | 帳號可以存在並登入；這一行本身沒有給資料表的讀取或修改權限 |
| `GRANT SELECT` | 可以執行 `SELECT` 查詢；不代表可以 `INSERT`、`UPDATE` 或 `DELETE` |
| `*.*` | 權限範圍的表示法：所有資料庫、所有資料表；實際還要看前面的權限種類 |
| ``mariadb_course`.*`` | `mariadb_course` 資料庫中的所有資料表 |
| `TO course_reader@localhost` | 這條授權是給哪個帳號 |
| `IDENTIFIED BY PASSWORD '...'` | MariaDB 顯示的密碼雜湊，不是明文密碼；不要公開貼出 |

你要從每一條授權確認三件事：

```text
可以做什麼：SELECT
在哪個物件：mariadb_course.*
哪個帳號：  course_reader@localhost
```

若看到 `UPDATE`、`ALL PRIVILEGES` 或 `GRANT OPTION`，先停止並請教師確認，不要自行修正權限。

### 3. 先確認資料，再測試拒絕

先查詢 P001 的庫存：

```sql
SELECT product_id, stock
FROM products
WHERE product_id = 'P001';
```

![image](https://hackmd.io/_uploads/BkbbELAqMg.png)

應看到：

```text
P001 / 10
```

如果查不到 P001、庫存不是 10，或 SELECT 失敗，不要繼續測試，先請教師確認資料起點。

接著執行以下 UPDATE 一次，不要修改條件：

```sql
UPDATE products
SET stock = stock + 1
WHERE product_id = 'P001';
```

這句 SQL 本身是有效的；本節期待它因為帳號沒有 UPDATE 權限而被拒絕：

![image](https://hackmd.io/_uploads/rJHdNU0qfe.png)

```text
ERROR 1142 ... UPDATE command denied ... products
```

### 4. 確認資料沒有變

再次執行：

```sql
SELECT product_id, stock
FROM products
WHERE product_id = 'P001';
```

![image](https://hackmd.io/_uploads/Hk_LE8Rqfl.png)

結果必須仍然是：

```text
P001 / 10
```

完整證據包含三部分：

1. SELECT 成功
2. 有效的 UPDATE 被 `ERROR 1142` 拒絕
3. 拒絕前後庫存都沒有改變

如果 UPDATE 顯示 `Query OK` 或庫存變成 11，立即停止，不要再試、不要自行減回 10、不要自行授權；請教師檢查並復原。

---

## Workshop

### 題目

在自己的 `mariadb_course` 完成以下任務：

1. 使用 socket 登入 `course_reader@localhost`。
2. 查詢目前資料庫、帳號與 `products-v1`。
3. 執行 `SHOW GRANTS FOR CURRENT_USER;`，只記錄權限、物件與帳號摘要。
4. 查詢 P001 的庫存，確認為 10。
5. 執行本節的 UPDATE 一次，確認得到 `ERROR 1142`。
6. 再查詢 P001，確認庫存仍為 10。

這是權限驗證，不要使用 root，不要修改 UPDATE 條件，也不要自行修正被拒絕的操作。

### 預期輸出

```text
account：course_reader@localhost
current_database：mariadb_course
dataset_version：products-v1
授權摘要：SELECT | mariadb_course.* | course_reader@localhost
操作前：P001 / stock=10
寫入結果：ERROR 1142 / UPDATE command denied / products
操作後：P001 / stock=10
判定：讀取允許，UPDATE 被權限拒絕，庫存未變
```

以上內容必須來自實際操作，不要直接複製預期輸出。不要提交密碼、完整 `SHOW GRANTS` 輸出或私人設定檔內容。

### 解答

- [本節解答與安全紀錄格式](https://hackmd.io/Bkvjep8YMg?type=view#answer-03)
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

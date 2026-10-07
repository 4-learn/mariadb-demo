# 05 建立資料表：把關係寫成 DDL

> **定位**：把 Ch4 的關聯設計寫成資料表，並用限制阻止不合法資料。
> DDL（Data Definition Language，資料定義語言）是用來定義、修改或刪除資料庫中各種「結構與物件」的 SQL 指令分類。

## 學習目標

完成本節後，你應該能夠：

- 用 `CREATE TABLE` 建立資料表
- 選擇 `VARCHAR`、`INT`、`ENUM` 等欄位型別
- 使用 `PRIMARY KEY`、`FOREIGN KEY`、`NOT NULL`、`DEFAULT` 與 `CHECK`
- 用 `ALTER TABLE` 增加欄位
- 用 `SHOW COLUMNS` 與 `SHOW CREATE TABLE` 檢查表結構
- 分辨 DDL 與資料列交易：`ROLLBACK` 不會撤銷建表

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

---

## 情境

你要建立一個 SOP 草稿區，讓同學練習新增文件與產品關聯，但不能改動正式的 `documents` 或 `product_documents`。

因此本節建立兩張練習表：

```text
practice_documents_05
practice_links_05
```

這是 Ch4 正式資料模型的縮小練習版。練習表可以建立與檢查，但正式資料保持不變。

---

## 講解

### 1. 進入 Workshop 資料庫

在 Ubuntu shell 執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  --default-character-set=utf8mb4 \
  mariadb_workshop_2026
```

確認目前身分：

```sql
SELECT DATABASE() AS current_database,
       CURRENT_USER() AS account;
```

![image](https://hackmd.io/_uploads/rkzUyYCqze.png)


應是：

```text
mariadb_workshop_2026
course_editor@localhost
```

### 2. 建立文件草稿表

```sql
CREATE TABLE IF NOT EXISTS practice_documents_05 (
    document_id VARCHAR(16) PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    source_version INT NOT NULL DEFAULT 1 CHECK (source_version >= 1),
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active'
) ENGINE=InnoDB;
```

![image](https://hackmd.io/_uploads/HkFPkKRcGx.png)

欄位限制：

- `PRIMARY KEY`：不可重複，也不可為 `NULL`
- `NOT NULL`：必須提供值，但空字串仍然是值
- `DEFAULT 1`：省略欄位時使用 1
- `CHECK`：拒絕小於 1 的版本
- `ENUM`：只接受 `active` 或 `inactive`

### 3. 建立產品／文件關聯表

```sql
CREATE TABLE IF NOT EXISTS practice_links_05 (
    product_id CHAR(4) NOT NULL,
    document_id VARCHAR(16) NOT NULL,
    PRIMARY KEY (product_id, document_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (document_id) REFERENCES practice_documents_05(document_id)
) ENGINE=InnoDB;
```

![image](https://hackmd.io/_uploads/Bk1iyYC5fe.png)

這裡延續 Ch4：

```text
product_id + document_id：複合主鍵
product_id：外鍵，連到既有 products
 document_id：外鍵，連到練習用 documents
```

注意：外鍵指向的是 `practice_documents_05`，不是正式的 `documents`。這樣練習不會污染正式 SOP。

### 4. 修改表結構並檢查定義

```sql
ALTER TABLE practice_documents_05
    ADD COLUMN IF NOT EXISTS note VARCHAR(200) NULL;

SHOW COLUMNS FROM practice_documents_05;
SHOW CREATE TABLE practice_documents_05;
SHOW CREATE TABLE practice_links_05;
```

```sql=
MariaDB [mariadb_workshop_2026]> SHOW COLUMNS FROM practice_documents_05;
+----------------+---------------------------+------+-----+---------+-------+
| Field          | Type                      | Null | Key | Default | Extra |
+----------------+---------------------------+------+-----+---------+-------+
| document_id    | varchar(16)               | NO   | PRI | NULL    |       |
| title          | varchar(120)              | NO   |     | NULL    |       |
| source_version | int(11)                   | NO   |     | 1       |       |
| status         | enum('active','inactive') | NO   |     | active  |       |
| note           | varchar(200)              | YES  |     | NULL    |       |
+----------------+---------------------------+------+-----+---------+-------+
5 rows in set (0.001 sec)

MariaDB [mariadb_workshop_2026]> SHOW CREATE TABLE practice_documents_05;
+-----------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Table                 | Create Table                                                                                                                                                                                                                                                                                                                                                                                    |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| practice_documents_05 | CREATE TABLE `practice_documents_05` (
  `document_id` varchar(16) NOT NULL,
  `title` varchar(120) NOT NULL,
  `source_version` int(11) NOT NULL DEFAULT 1 CHECK (`source_version` >= 1),
  `status` enum('active','inactive') NOT NULL DEFAULT 'active',
  `note` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
1 row in set (0.000 sec)

MariaDB [mariadb_workshop_2026]> SHOW CREATE TABLE practice_links_05;
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Table             | Create Table                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| practice_links_05 | CREATE TABLE `practice_links_05` (
  `product_id` char(4) NOT NULL,
  `document_id` varchar(16) NOT NULL,
  PRIMARY KEY (`product_id`,`document_id`),
  KEY `document_id` (`document_id`),
  CONSTRAINT `practice_links_05_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`),
  CONSTRAINT `practice_links_05_ibfk_2` FOREIGN KEY (`document_id`) REFERENCES `practice_documents_05` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci |
+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
1 row in set (0.000 sec)

MariaDB [mariadb_workshop_2026]>
```

![image](https://hackmd.io/_uploads/BkhbbtA9Gx.png)


`SHOW COLUMNS` 適合快速查看欄位；`SHOW CREATE TABLE` 可以確認主鍵、外鍵、`CHECK` 與儲存引擎。

`IF NOT EXISTS` 只避免同名欄位已存在時報錯，不會檢查既有欄位型別是否正確。

### 5. DDL 不會被 ROLLBACK 撤銷

`CREATE TABLE` 與 `ALTER TABLE` 是 DDL。本節只建立與修改表結構；資料列新增與交易會在 Ch6 說明。

這裡先記住：

```text
CREATE TABLE／ALTER TABLE → 修改表結構
INSERT → 新增資料列（Ch6）
ROLLBACK → 取消交易中的資料列異動（Ch6）
```


---

## Workshop

### 題目

在 `mariadb_workshop_2026` 完成以下任務：

1. 建立 `practice_documents_05` 與 `practice_links_05`。
2. 確認 `practice_links_05` 有複合主鍵與兩個正確外鍵。
3. 用 `ALTER TABLE` 加入可為 `NULL` 的 `note`。
4. 檢查兩張表的欄位、主鍵與外鍵結構。
5. 說明為什麼資料列新增與 `ROLLBACK` 會在 Ch6 練習。

不要修改正式的 `documents`、`product_documents` 或其他共用資料。

### 預期輸出

```text
```

結構仍應包含：

```text
practice_documents_05：5 欄，note 可為 NULL
practice_links_05：複合主鍵、兩個外鍵、InnoDB
```

### 交件

提交：

- `SHOW COLUMNS` 結果
- 兩張表的 `SHOW CREATE TABLE` 結果
- 兩張表的實際結構檢查結果
- 一段說明：本節為什麼只處理 DDL

不要提交密碼或私人設定檔內容。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

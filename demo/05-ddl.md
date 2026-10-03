# 05 建立資料表：把關係寫成 DDL

> **定位**：把 Ch4 的關聯設計寫成資料表，並用限制阻止不合法資料。

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

`SHOW COLUMNS` 適合快速查看欄位；`SHOW CREATE TABLE` 可以確認主鍵、外鍵、`CHECK` 與儲存引擎。

`IF NOT EXISTS` 只避免同名欄位已存在時報錯，不會檢查既有欄位型別是否正確。

### 5. NULL、空字串與預設值

```sql
START TRANSACTION;

INSERT INTO practice_documents_05 (document_id, title, note) VALUES
    ('D901', '課堂草稿', NULL),
    ('D902', '另一份草稿', '');

SELECT document_id,
       source_version,
       status,
       note,
       note IS NULL AS missing_note
FROM practice_documents_05
ORDER BY document_id;

ROLLBACK;

SELECT COUNT(*) AS remaining_rows
FROM practice_documents_05;
```

預期：

```text
D901：missing_note = 1
D902：missing_note = 0
兩列的 source_version = 1
兩列的 status = active
remaining_rows = 0
```

`NULL` 代表缺值；`''` 是長度為 0 的文字。判斷 `NULL` 要用：

```sql
note IS NULL
```

不要寫：

```sql
note = NULL
```

### 6. DDL 不會被 ROLLBACK 撤銷

`CREATE TABLE` 與 `ALTER TABLE` 是 DDL。完成 `ROLLBACK` 後：

```text
資料列消失
practice_documents_05 表仍存在
note 欄位仍存在
```

這就是本節要分辨的兩件事：資料列可以回滾，表結構不會因這次 `ROLLBACK` 消失。

---

## Workshop

### 題目

在 `mariadb_workshop_2026` 完成以下任務：

1. 建立 `practice_documents_05` 與 `practice_links_05`。
2. 確認 `practice_links_05` 有複合主鍵與兩個正確外鍵。
3. 用 `ALTER TABLE` 加入可為 `NULL` 的 `note`。
4. 新增 D901／D902，比較 `NULL` 與空字串。
5. 執行 `ROLLBACK`，確認資料列消失但表與欄位仍存在。

不要修改正式的 `documents`、`product_documents` 或其他共用資料。

### 預期輸出

```text
D901  source_version=1  status=active  missing_note=1
D902  source_version=1  status=active  missing_note=0
remaining_rows=0
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
- D901／D902 的實際查詢結果
- `ROLLBACK` 後的 `remaining_rows`
- 一段說明：為什麼資料列會回滾，但建表不會回滾

不要提交密碼或私人設定檔內容。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

# 06 新增資料：先有文件，再建立產品關聯

> **定位**：用 `INSERT` 新增資料，依父表與子表順序建立關聯，並辨認重複鍵與外鍵錯誤。

## 學習目標

完成本節後，你應該能夠：

- 用欄位清單新增單列與多列資料
- 理解 `DEFAULT` 如何補上省略的欄位
- 依父表、子表順序新增有外鍵的資料
- 使用 `ROW_COUNT()` 與 `SELECT` 核對結果
- 分辨 `ERROR 1062` 與 `ERROR 1452`
- 用 `ROLLBACK` 清除本次交易的資料列

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

---

## 情境

客服要先試填一份連線 SOP，讓兩個產品都能使用。

正確做法是：

1. 建立一個文件身份
2. 建立兩組產品／文件關聯
3. 查回資料確認結果
4. 回滾練習資料，不影響正式 checkpoint

不要把同一份文件新增兩次，也不要修改正式的 `products`、`documents` 或 `product_documents`。

---

## 講解

### 1. 建立本節專用練習表

本節使用新的表，不使用 Ch5 的資料表：

```text
practice_documents_06
practice_links_06
```

在 Ubuntu shell 執行公開 demo：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  --default-character-set=utf8mb4 \
  mariadb_workshop_2026 < demo/06-insert.sql
```

這段示範會建立表、開始交易、加入資料、查詢結果，最後回滾資料列。表結構會保留。

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

### 2. 先認識本節會出現的語法

本節第一次使用交易與新增資料的語法，先用流程和表格理解，再執行 SQL：

```text
START TRANSACTION → 開始一組可以一起確認或取消的資料操作
INSERT            → 新增資料
SELECT            → 查詢確認
COMMIT            → 正式保存；ROLLBACK → 取消
```

| 語法 | 簡單意思 |
| --- | --- |
| `START TRANSACTION` | 開始一組可以一起確認或取消的資料操作 |
| `INSERT INTO` | 新增資料到指定的表 |
| `VALUES` | 提供要新增的值 |
| `ROW_COUNT()` | 查看上一個命令影響幾列 |
| `SELECT` | 查詢資料，確認結果 |
| `ROLLBACK` | 取消這次交易中的資料異動 |
| `COMMIT` | 正式保存這次交易中的資料異動 |

可以把 transaction 想成資料庫的草稿區：

```text
START TRANSACTION → 開始編輯草稿
INSERT            → 填入資料
SELECT            → 檢查草稿
ROLLBACK          → 放棄草稿
COMMIT            → 確認並保存
```

本節使用 `ROLLBACK`，所以新增的練習資料列最後會消失；練習表本身仍然保留。

### 3. 用欄位清單新增文件

```sql
START TRANSACTION;

INSERT INTO practice_documents_06 (document_id, title)
VALUES ('D901', '課堂連線草稿');

SELECT ROW_COUNT() AS inserted_documents;
```

這裡只提供 `document_id` 與 `title`：`INSERT INTO` 後面的欄位清單說明要填哪些欄位，`VALUES` 後面的值依相同順序對應。

```text
source_version → DEFAULT 1
status         → DEFAULT active
```

`ROW_COUNT()` 要緊接在 `INSERT` 後面；它只表示上一個命令影響幾列，不代表內容一定正確。

再查回內容：

```sql
SELECT document_id, title, source_version, status
FROM practice_documents_06
ORDER BY document_id;
```

預期：

```text
D901 / 課堂連線草稿 / 1 / active
```

### 4. 依父表、子表順序建立關聯

文件表是父表，關聯表是子表。先有 D901，才能新增指向它的關聯：

```sql
INSERT INTO practice_links_06 (product_id, document_id)
VALUES
    ('P001', 'D901'),
    ('P002', 'D901');

SELECT ROW_COUNT() AS inserted_links;

SELECT product_id, document_id
FROM practice_links_06
ORDER BY product_id, document_id;
```

預期：

```text
inserted_links = 2
P001 / D901
P002 / D901
```

兩組括號代表兩列；每一組括號就是一筆資料。這就是一份文件被兩個產品使用的關聯。

### 5. 測試重複鍵：ERROR 1062

`practice_links_06` 的複合主鍵是：

```text
(product_id, document_id)
```

所以這組配對不能重複：

```text
P001 / D901
P001 / D901
```

重複時應看到：

```text
ERROR 1062
```

這不是 P001 不能重複，也不是 D901 不能重複；是同一組配對重複。

請使用獨立的錯誤測試檔，和成功路徑分開執行。遇到錯誤後，如果仍在互動式 MariaDB，輸入：

```sql
ROLLBACK;
```

### 6. 測試不存在的父資料：ERROR 1452

這組關聯中 P001 存在，但 D999 不存在：

```text
P001 / D999
```

因此外鍵應拒絕這筆資料，看到：

```text
ERROR 1452
```

不要關閉 `FOREIGN_KEY_CHECKS`，也不要使用 `INSERT IGNORE` 或 `REPLACE` 把錯誤藏起來。

### 7. 回滾練習資料

成功路徑最後執行：

```sql
ROLLBACK;

SELECT
    (SELECT COUNT(*) FROM practice_documents_06) AS documents_after,
    (SELECT COUNT(*) FROM practice_links_06) AS links_after;
```

預期：

```text
documents_after = 0
links_after = 0
```

資料列被清除，但：

```text
practice_documents_06 表仍存在
practice_links_06 表仍存在
```

這延續 Ch5：DDL 建立表；本節 DML 新增資料。`COMMIT` 雖然本節不執行，但在正式資料操作中代表「確認並保存」交易。

---

## Workshop

### 題目

在 `mariadb_workshop_2026` 完成以下任務：

1. 建立本節的 `practice_documents_06` 與 `practice_links_06`。
2. 在一個交易中新增 D901「課堂連線草稿」與 D902「課堂配對草稿」。
3. 新增 P001/D901、P002/D901、P001/D902 三組關聯。
4. 每次 `INSERT` 後立即執行 `ROW_COUNT()`，再用 `SELECT` 查回資料。
5. 分別執行重複配對與不存在父資料的錯誤測試。
6. 最後 `ROLLBACK`，確認練習資料列為 0。

### 預期輸出

```text
inserted_documents = 2
inserted_links = 3
D901 / 1 / active
D902 / 1 / active
P001 / D901
P001 / D902
P002 / D901
documents_after = 0
links_after = 0
duplicate: ERROR 1062
missing parent: ERROR 1452
```

### 交件

提交：

- 新增文件與關聯的 SQL
- `ROW_COUNT()` 與實際查詢結果
- `ERROR 1062` 與 `ERROR 1452` 的錯誤摘要
- `ROLLBACK` 後的資料筆數
- 一段說明：為什麼必須先新增父表資料

不要提交密碼或私人設定檔內容，也不要修改正式資料。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

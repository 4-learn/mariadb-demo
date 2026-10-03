# 04 產品與 SOP：用主鍵、外鍵表達關聯

> **定位**：用主鍵、外鍵與關聯表描述產品、分類和 SOP 之間的關係。

## 學習目標

完成本節後，你應該能夠：

- 說明主鍵與外鍵各自解決什麼問題
- 分辨一對多與多對多
- 用固定 ID 找到產品、文件與段落
- 說明為什麼不能把共用 SOP 複製到每個產品

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：本節示範 SQL。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

---

## 情境

客服發現感測器 A 有兩份 SOP，感測器 B 也使用其中一份。若把 SOP 文字直接複製到產品表，修改文件時就可能漏改其中一份。

另外，P010 已經是產品，但目前還沒有 SOP。資料庫要能分辨「沒有關聯」和「資料不存在」。

---

## 講解

### 1. 從基礎庫切換到 Workshop 資料庫

第 01～03 節使用 `mariadb_course`。本節開始使用教師準備的隔離資料庫 `mariadb_workshop_2026`，不會改動前面的基礎資料。

在 Ubuntu shell 執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" --default-character-set=utf8mb4 mariadb_workshop_2026
```

登入後確認資料：

```sql
SELECT DATABASE() AS current_database, CURRENT_USER() AS account;
SELECT dataset_version FROM course_meta ORDER BY dataset_version;
```

應看到：

```text
current_database：mariadb_workshop_2026
account：          course_editor@localhost
dataset_version：  products-v1、sop-v1
```

若找不到 editor 設定檔或 `sop-v1`，先請教師補好 Workshop checkpoint，不要把 SOP 匯入 `mariadb_course`。

### 2. 主鍵：每筆資料的固定身份

| 表 | 一列代表 | 主鍵 |
| --- | --- | --- |
| `categories` | 一個分類 | `category_id` |
| `products` | 一個產品 | `product_id` |
| `documents` | 一份 SOP | `document_id` |
| `product_documents` | 一組產品與 SOP 的關係 | `product_id + document_id` |
| `chunks` | SOP 中的一段文字 | `chunk_id` |

名稱可能修改或重複；固定 ID 才能辨認同一筆資料。主鍵不可重複，也不可為 `NULL`。

查看一組產品／SOP 關係的定義：

```sql
SHOW CREATE TABLE product_documents;
```

### 3. 一對多：一個上層資料對應多筆下層資料

```text
categories 1 ───< products
    一個分類有多個產品

documents 1 ───< chunks
    一份 SOP 有多個段落
```

產品用 `category_id` 指向分類；段落用 `document_id` 指向文件。這些欄位是外鍵，必須指向已存在的資料。

### 4. 多對多：使用關聯表

產品和 SOP 之間可能是多對多：一個產品有多份 SOP，一份 SOP 也能給多個產品使用。

```text
products >───< product_documents >───< documents
```

實際上，`product_documents` 的每一列只代表一組配對：

```sql
SELECT product_id, document_id
FROM product_documents
WHERE product_id = 'P001'
ORDER BY document_id;

SELECT product_id, document_id
FROM product_documents
WHERE document_id = 'D001'
ORDER BY product_id;
```

預期：

```text
P001 的文件：D001、D005
D001 的產品：P001、P002
```

同一個 P001 可以有兩份文件；同一個 D001 也可以連到兩個產品。只有同一組 `product_id + document_id` 不可重複。

### 5. 沒有關聯不等於資料不存在

```sql
SELECT product_id
FROM products
WHERE product_id = 'P010';

SELECT product_id, document_id
FROM product_documents
WHERE product_id = 'P010';

SELECT document_id, status
FROM documents
WHERE document_id = 'D003';
```

預期：

```text
P010：產品存在，但沒有關聯列
D003：文件存在，但 status 是 inactive
```

外鍵只確認資料存在，不會自動判斷產品是否販售中或文件是否有效；那些是查詢時的業務條件。

### 6. 文件與段落各有自己的 ID

```sql
SELECT chunk_id, document_id, source_version
FROM chunks
WHERE document_id = 'D002'
ORDER BY chunk_id;

SELECT COUNT(*) AS bad_hashes
FROM chunks
WHERE BINARY content_hash <> BINARY SHA2(`text`, 256);
```

預期 D002 有 C003、C004，版本都是 1；`bad_hashes` 是 0。

這一節先讀懂關係，不建立新表。第 05 節再把關係圖寫成 DDL，第 08 節才用 JOIN 組合資料。

---

## Workshop

### 題目

在 `mariadb_workshop_2026` 完成以下任務：

1. 寫出 `products`、`documents`、`product_documents`、`chunks` 各自的一列意義、主鍵與外鍵方向。
2. 查詢 P001 的所有文件，再反查 D001 的所有產品。
3. 用兩個查詢證明 P010「產品存在，但沒有文件關聯」。
4. 查詢 D002 的段落與版本，確認摘要沒有不一致。
5. 說明為什麼 P001/D005 合法，而重複的 P001/D001 與不存在的 P001/D999 不合法。

### 預期輸出

```text
P001 的文件：D001、D005
D001 的產品：P001、P002
P010：產品存在，關聯為 0 筆
D002 的段落：C003、C004，版本皆為 1
bad_hashes：0
```

### 交件

提交：

- 一張簡化關聯圖
- 主鍵與外鍵標記
- 查詢與實際結果
- 一段說明：為什麼 SOP 不應複製到每個產品

不要修改正式 products、documents 或 chunks 資料，也不要提交密碼。

### 解答

- [本節解答與關係說明](https://github.com/4-learn/mariadb-workshop/blob/main/04-relations.sql)
- [公開 demo SQL](https://github.com/4-learn/mariadb-demo/blob/main/demo/04-relations.sql)

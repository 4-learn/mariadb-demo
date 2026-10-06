# 04 產品與 SOP：用主鍵、外鍵表達關聯

> **定位**：用主鍵、外鍵與關聯表描述產品、分類和 SOP 之間的關係。

## 學習目標

完成本節後，你應該能夠：

- 說明主鍵與外鍵各自解決什麼問題
- 分辨一對多與多對多
- 用固定 ID 找到產品、文件與段落
- 說明為什麼不能把共用 SOP 複製到每個產品

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習環境。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

---

## 情境

客服發現感測器 A 有兩份 SOP，感測器 B 也使用其中一份。若把 SOP 文字直接複製到產品表，修改文件時就可能漏改其中一份。

另外，P010 已經是產品，但目前還沒有 SOP。資料庫要能分辨「沒有關聯」和「資料不存在」。

---

## 講解

### 1. 從基礎庫切換到 Workshop 資料庫

第 01～03 節使用 `mariadb_course`。本節開始使用教師準備的隔離資料庫 `mariadb_workshop_2026`，不會改動前面的基礎資料。

如果教師示範後，你的 VM 尚未建立 Ch4 練習環境，先在 `mariadb-demo` 目錄執行：

```bash
python3 prepare_workshop.py
```

這個初始化工具會在你的 VM 建立練習用的 `mariadb_workshop_2026`、`course_editor@localhost` 與 `course_app@localhost`。它不是考試答案；若資料庫、帳號或設定檔已存在，工具會停止，不要刪除資料後重跑。

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

![image](https://hackmd.io/_uploads/SJzzBdRqfx.png)

![image](https://hackmd.io/_uploads/ry8nUdRczx.png)



### 3. 一對多：一個上層資料對應多筆下層資料

![image](https://hackmd.io/_uploads/ByHOd_09Gg.png)


產品用 `category_id` 指向分類；段落用 `document_id` 指向文件。這些欄位是外鍵，必須指向已存在的資料。

查一個分類底下有哪些產品：

```sql
SELECT category_id, product_id, name
FROM products
WHERE category_id = 1
ORDER BY product_id;
```

![image](https://hackmd.io/_uploads/HJYY_dAqfe.png)


這會回傳分類 1 的多個產品。反過來看，一個產品只有一個 `category_id`：

```sql
SELECT product_id, name, category_id
FROM products
WHERE product_id IN ('P001', 'P002')
ORDER BY product_id;
```

![image](https://hackmd.io/_uploads/BJ-oOuRqGl.png)


同樣地，一份 SOP 可以有多個段落：

```sql
SELECT document_id, chunk_id, source_version
FROM chunks
WHERE document_id = 'D002'
ORDER BY chunk_id;
```

![image](https://hackmd.io/_uploads/S1xWFdRqzg.png)

預期 D002 對應 C003、C004。這些查詢是在讀取一對多的資料，不需要 `JOIN`。

### 4. 多對多：使用關聯表

產品和 SOP 之間可能是多對多：一個產品有多份 SOP，一份 SOP 也能給多個產品使用。

![image](https://hackmd.io/_uploads/HyGIYuRcGx.png)


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

![image](https://hackmd.io/_uploads/Sk-sY_R5Mg.png)

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

![image](https://hackmd.io/_uploads/Bys3YdA5Mg.png)


預期：

```text
P010：產品存在，但沒有關聯列
D003：文件存在，但 status 是 inactive
```

外鍵只確認資料存在，不會自動判斷產品是否販售中或文件是否有效；那些是查詢時的業務條件。

### 6. 文件與段落各有自己的 ID

`chunks` 表用來保存一份 SOP 被切開後的段落。一列代表一個段落：

| 欄位 | 意思 |
| --- | --- |
| `chunk_id` | 這個段落自己的固定 ID，例如 `C003` |
| `document_id` | 這個段落屬於哪一份文件，例如 `D002` |
| `source_version` | 這個段落所屬的文件版本 |
| `text` | 段落的實際文字內容 |
| `content_hash` | 由 `text` 計算出的 hash value，用來檢查內容是否一致 |

先記住這個關係：

```text
D002
├── C003
└── C004
```

也就是：

```text
一份文件（document）
→ 多個段落（chunks）
```

一份 SOP 文件可能會拆成多個段落。先查 D002 的段落：

```sql
SELECT chunk_id, document_id, source_version
FROM chunks
WHERE document_id = 'D002'
ORDER BY chunk_id;
```

![image](https://hackmd.io/_uploads/B1h6tO0czg.png)

這個查詢會告訴我們：

```text
D002
├── C003
└── C004
```

也就是：

```text
一份文件（document）
→ 多個段落（chunks）
```

為什麼要先確認這件事？因為後面的 Embedding 與向量檢索，會以 `chunk` 作為搜尋的資料單位，而不是直接把整份 SOP 當成一筆資料。未來的 LLM RAG 也會先找出相關 chunks，再把它們提供給 LLM 參考：

```text
問題
→ 找到相關 chunks
→ 提供給 LLM
→ LLM 根據這些內容產生回答
```

這裡的 RAG 是「檢索增強生成」：先檢索自己的資料，再讓 LLM 根據找到的內容生成回答。本課目前只先建立資料關係，不會在本節建立聊天機器人。

接著確認 D002 的段落版本：

```sql
SELECT chunk_id, document_id, source_version
FROM chunks
WHERE document_id = 'D002'
ORDER BY chunk_id;
```

預期 D002 對應 C003、C004，版本都是 1。

| SQL 語法 | 簡單意思 |
| --- | --- |
| `SELECT` | 要查看哪些欄位 |
| `FROM chunks` | 從 `chunks` 表查詢 |
| `WHERE` | 設定篩選條件 |
| `document_id = 'D002'` | 只查屬於 D002 的段落 |
| `ORDER BY chunk_id` | 按段落 ID 排序 |

最後，比對每個 chunk 的 hash value：

```sql
SELECT COUNT(*) AS bad_hashes
FROM chunks
WHERE BINARY content_hash <> BINARY SHA2(`text`, 256);
```

這是在比較：

```text
資料表原本保存的 content_hash
和目前 text 重新計算出的 SHA-256 hash
```

預期：

```text
bad_hashes：0
```

`0` 表示目前沒有發現 chunk 文字和保存的 hash value 不一致。這個檢查的理由是：未來產生 embedding 時，向量必須對應正確的原文；否則 RAG 可能找到舊文字的向量，卻顯示新版文字。

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

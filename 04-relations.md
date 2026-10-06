# 04 產品與 SOP：用主鍵、外鍵表達關聯

> **定位**：用主鍵、外鍵與關聯表描述產品、分類和 SOP 之間的關係，並為後面的 Embedding 與 LLM RAG 建立資料基礎。

## 學習目標

完成本節後，你應該能夠：

- 說明主鍵與外鍵各自解決什麼問題
- 分辨一對多與多對多
- 知道為什麼 SOP 要拆成可搜尋的 chunks
- 用固定 ID 找到產品、文件與段落
- 初步理解 chunks 和未來 LLM RAG 的關係
- 說明為什麼不能把共用 SOP 複製到每個產品

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習環境。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

---

## 情境：客服知識庫要找得到正確段落

客服問：

```text
感測器 A 如何恢復出廠設定？
```

系統不能只知道「這是一個問題」，還要找得到：

```text
哪個產品
哪一份 SOP
SOP 中哪一個段落
```

因此資料要保留這條關係：

```text
產品
  ↓
產品與文件的關聯
  ↓
SOP 文件
  ↓
SOP 段落 chunk
```

這會影響後面的 LLM RAG：

```text
先從資料庫找到相關 chunks
→ 把合格 chunks 提供給 LLM
→ LLM 根據這些內容產生回答
```

如果資料庫找錯產品、找錯版本或把段落重複計算，後面的 LLM 也可能根據錯誤內容回答。

另外，P010 已經是產品，但目前還沒有 SOP。資料庫要能分辨「沒有關聯」和「資料不存在」。

## 先認識 LLM RAG

RAG 是 **Retrieval-Augmented Generation**，中文可稱為「檢索增強生成」。

簡單說：

```text
R：Retrieval，先從自己的資料找相關內容
A：Augmented，把找到的內容放進問題上下文
G：Generation，再請 LLM 根據上下文產生文字
```

本課先做前半段：

```text
資料庫關聯
→ 找到合格 chunks
→ 後面轉成 embedding 並搜尋
```

本課不直接建立聊天機器人，也不把 LLM 的回答當成資料庫真相。後面的向量課程會讓系統找到候選段落；使用者仍要核對產品、版本、否定詞與原文。

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

### 2. 第一次看到 SQL 語法

之後的查詢會反覆使用這些 SQL 語法。先用表格認識它們：

| 語法 | 用途 | 本節例子 |
| --- | --- | --- |
| `SELECT` | 指定要看的欄位 | `SELECT product_id, name` |
| `FROM` | 指定從哪張表查 | `FROM products` |
| `WHERE` | 篩選符合條件的資料 | `WHERE product_id = 'P001'` |
| `ORDER BY` | 排序結果 | `ORDER BY chunk_id` |
| `COUNT(*)` | 計算資料列數量 | `COUNT(*) AS bad_hashes` |
| `AS` | 替欄位或結果取易讀的別名 | `AS source_version` |
| `<>` | 判斷不等於 | `content_hash <> ...` |

本節不要求背完所有 SQL；先知道每個語法在查詢中負責什麼。

### 3. 主鍵：每筆資料的固定身份

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

### 4. 一對多：一個上層資料對應多筆下層資料

```text
categories 1 ───< products
    一個分類有多個產品

documents 1 ───< chunks
    一份 SOP 有多個段落
```

產品用 `category_id` 指向分類；段落用 `document_id` 指向文件。這些欄位是外鍵，必須指向已存在的資料。

查一個分類底下有哪些產品：

```sql
SELECT category_id, product_id, name
FROM products
WHERE category_id = 1
ORDER BY product_id;
```

這會回傳分類 1 的多個產品。反過來看，一個產品只有一個 `category_id`：

```sql
SELECT product_id, name, category_id
FROM products
WHERE product_id IN ('P001', 'P002')
ORDER BY product_id;
```

同樣地，一份 SOP 可以有多個段落：

```sql
SELECT document_id, chunk_id, source_version
FROM chunks
WHERE document_id = 'D002'
ORDER BY chunk_id;
```

預期：

```text
C003  D002  1
C004  D002  1
```

### 為什麼現在要查 chunks？

因為一份 SOP 文件不是後面搜尋的最小單位。後面的 Embedding 與向量檢索會以 chunk 為單位：

```text
D002
├── C003 → 未來產生一個向量
└── C004 → 未來產生一個向量
```

RAG 的檢索階段會先找到合格的 chunk，再把這些段落提供給 LLM。現在先查出 D002 的 C003、C004，是為了確認後面真正要搜尋、轉成向量與交給 LLM 參考的資料單位。

這些查詢是在讀取一對多的資料，不需要 `JOIN`。

### 5. 多對多：使用關聯表

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

### 6. 沒有關聯不等於資料不存在

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

### 7. 文件與段落各有自己的 ID

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

這表示目前沒有發現 chunk 的文字與保存的 hash value 不一致。這是後面產生 embedding 前的基本檢查：

```text
chunk 原文
→ content_hash
→ embedding vector
```

三者必須能對得起來，否則 RAG 可能把新版原文和舊版向量混在一起。

本節不是在教 hash 演算法，也不是在做向量搜尋；本節先建立：

```text
document
→ chunks
→ 每個 chunk 的原文與版本
→ 確認內容沒有不一致
```

這一節先讀懂關係，不建立新表。第 05 節再把關係圖寫成 DDL，第 08 節才用 JOIN 組合資料。

---

## Workshop

### 題目

在 `mariadb_workshop_2026` 完成以下任務：

1. 寫出 `products`、`documents`、`product_documents`、`chunks` 各自的一列意義、主鍵與外鍵方向。
2. 查詢 P001 的所有文件，再反查 D001 的所有產品。
3. 用兩個查詢證明 P010「產品存在，但沒有文件關聯」。
4. 查詢 D002 的段落與版本，說明 C003、C004 為什麼是後續向量與 RAG 的檢索單位。
5. 比對所有 chunks 的 hash value，確認 `bad_hashes`。
6. 說明為什麼 P001/D005 合法，而重複的 P001/D001 與不存在的 P001/D999 不合法。

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
- 一段說明：chunk 為什麼是未來向量檢索與 RAG 的資料單位
- 一段說明：為什麼 SOP 不應複製到每個產品

不要修改正式 products、documents 或 chunks 資料，也不要提交密碼。

### 解答

- [本節解答與關係說明](https://github.com/4-learn/mariadb-workshop/blob/main/04-relations.sql)
- [公開 demo SQL](https://github.com/4-learn/mariadb-demo/blob/main/demo/04-relations.sql)

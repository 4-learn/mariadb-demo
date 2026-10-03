# 11 參數化 CRUD：把 SQL 與資料分開

> **定位**：用 Python Connector 的參數化查詢完成新增、讀取、修改與刪除，不讓外部輸入改寫 SQL。

## 學習目標

完成本節後，你應該能夠：

- 使用 `?` 與參數 tuple 執行 CRUD
- 保存含單引號的文字資料
- 分辨資料值與 SQL 語法
- 用回讀與 `rowcount` 核對新增、修改、刪除
- 使用 `P9xx` 練習 ID，不污染正式產品

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

本節使用 Ch10 的 Python 虛擬環境與自己的 `course_app` 設定檔。

---

## 情境

客服輸入：

```text
O'Reilly
```

如果把文字直接拼進 SQL，單引號可能造成語法錯誤；如果輸入看起來像 SQL，更不能讓它改變查詢邏輯。

正確做法是讓 Connector 分開傳送：

```text
SQL 結構
資料值
```

本節只使用 `P9xx` 練習產品。所有操作最後回滾，不修改 P001～P012。

---

## 講解

### 1. 使用參數，不拼接 SQL

```python
from contextlib import closing
from course_db import connect

with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT product_id, name FROM products WHERE product_id = ?",
            ("P001",),
        )
        print(cur.fetchone())
```

預期：

```text
('P001', '教學感測器 A')
```

注意：

```text
? 不加引號
("P001",) 是只有一個元素的 tuple
```

不要寫：

```python
"WHERE product_id = '?'"
```

也不要使用：

```python
f"...{user_input}..."
"...%s" % user_input
"...{}".format(user_input)
```

參數可以放值，不能拿來代替表名或欄名：

```sql
SELECT * FROM ?   -- 錯誤用法
```

### 2. 四種 CRUD 操作

`course_db.py` 提供可重用函式：

```python
cur.execute(
    "INSERT INTO products "
    "(product_id, category_id, name, price, stock, status) "
    "VALUES (?, ?, ?, ?, ?, ?)",
    (product_id, category_id, name, Decimal(price), stock, status),
)

cur.execute(
    "UPDATE products SET stock = ? WHERE product_id = ?",
    (stock, product_id),
)

cur.execute(
    "DELETE FROM products WHERE product_id = ?",
    (product_id,),
)
```

四種操作：

```text
INSERT：新增資料
SELECT：讀取資料
UPDATE：修改資料
DELETE：刪除資料
```

本節的函式會限制寫入 ID 為：

```text
P9xx
```

這是課堂練習的保護範圍，不是所有正式系統都必須使用的 ID 規則。

### 3. 用回讀確認結果

`rowcount` 只表示受影響的列數，不能單獨證明內容正確。

```python
created = create_product(conn, "P915", "客服's 測試品", price="125.50")
updated = update_stock(conn, "P915", 4)
row = get_product(conn, "P915")
```

要再檢查：

```text
名稱是否保留單引號
價格是否為 125.50
庫存是否為 4
```

`UPDATE` 回傳 0 可能表示：

```text
ID 不存在
值沒有改變
```

要用 `get_product()` 回讀，不要只看數字猜原因。

### 4. 驗證單引號與類 SQL 輸入

執行 demo：

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/11-crud.py
```

Demo 會把以下文字當成一個普通值：

```text
O'Reilly'; DELETE FROM products; --
```

回讀時必須完整保留。另一個查詢值：

```text
P001' OR '1'='1
```

應該查不到資料，而不是列出 P001 或整張表。

### 5. 回滾練習資料

Demo 與 Workshop 會：

```text
開始交易
新增／修改／刪除 P9xx
回讀並驗證
ROLLBACK
確認正式 P001 仍存在
```

這次只回滾資料變更；資料表結構不受影響。完整交易責任會在 Ch12 深入說明。

---

## Workshop

### 題目

在自己的 VM 執行：

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/11-crud.py
```

並完成自己的練習：

1. 新增 P915，名稱為 `客服's 測試品`，價格 125.50，初始庫存 1。
2. 將 P915 庫存修改成 4，回讀名稱、金額與庫存。
3. 查詢 `P915' OR 1=1 -- `，結果應為 `None`。
4. 刪除 P915 兩次，確認回傳 1、0。
5. 最後確認 P915 不存在，P001 仍存在。

### 預期輸出

```text
create=1
update=1
price=125.50
stock=4
delete=1
repeated_delete=0
quote/injection/cleanup OK
```

### 交件

提交：

- CRUD 程式或執行結果
- 名稱、價格、庫存的回讀結果
- 注入形狀輸入的結果
- 第一次與第二次 DELETE 的影響筆數
- 回滾後 P915 與 P001 的狀態

不要提交密碼或私人設定檔內容。不要直接修改 P001～P012。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

# 11 參數化 CRUD：把 SQL 結構與資料值分開

> **定位**：延續 Ch5～9 的條件查詢，用一個安全的 P9xx 練習看懂參數化 CRUD。先看完整 code，再請 Agent 解釋與執行；本章不要求先會寫 Python。

[上一節](10-python-connection.md) · [下一節](12-transactions.md)

## 1. 先連回 Ch5～9

SQL 的結構與資料值要分開。先在 MariaDB client 確認正式資料基準：

```sql
SELECT product_id, name, price, stock
FROM products
WHERE product_id = 'P001';
```

本章只使用練習產品 `P915`，不修改 P001～P012。程式最後會 rollback，P915 不應留下。

## 2. Code section：一個可執行的 CRUD 練習

```python
from contextlib import closing
from decimal import Decimal
from course_db import connect

with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        conn.begin()
        try:
            cur.execute(
                """
                INSERT INTO products
                    (product_id, category_id, name, price, stock, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("P915", 1, "O'Reilly 測試品", Decimal("125.50"), 1, "active"),
            )
            created = cur.rowcount

            cur.execute(
                "SELECT product_id, name, price, stock FROM products WHERE product_id = ?",
                ("P915",),
            )
            before_update = cur.fetchone()

            cur.execute(
                "UPDATE products SET stock = ? WHERE product_id = ?",
                (4, "P915"),
            )
            updated = cur.rowcount

            cur.execute(
                "SELECT product_id, name, price, stock FROM products WHERE product_id = ?",
                ("P915",),
            )
            after_update = cur.fetchone()

            cur.execute(
                "SELECT product_id FROM products WHERE product_id = ?",
                ("P915' OR 1=1 -- ",),
            )
            injection_shaped_lookup = cur.fetchone()

            cur.execute("DELETE FROM products WHERE product_id = ?", ("P915",))
            deleted = cur.rowcount
            print(created, before_update, updated, after_update,
                  injection_shaped_lookup, deleted)
        finally:
            conn.rollback()
```

看懂五件事即可：`?` 是資料值位置；tuple 是傳入值；`rowcount` 是受影響列數；回讀才知道資料內容；最後 rollback 讓練習不污染資料庫。`O'Reilly` 不會破壞 SQL，類 SQL 文字也只會被當成資料。

## 3. Workshop：請 Agent 解釋與執行

把上面的完整 code section 貼給 Agent，使用：

```text
你現在在 Ubuntu 的 ~/workspace/mariadb-demo repo 根目錄。
請只驗證這段 Ch11 CRUD code，不要設計新程式。
先用簡單中文說明 INSERT、兩次 SELECT、UPDATE、DELETE、? 參數與 rollback；說明為什麼 P001～P012 不會被修改。
不要讀取、列印或修改密碼、JSON 設定檔、token、.cnf 或私人檔案。
不要修改 repo 內任何檔案；可以在 /tmp/opencode/run_crud.py 建立暫存檔，執行後刪除。
必須使用：
PYTHONPATH=/home/yillkid/workspace/mariadb-demo
/home/yillkid/mariadb-course-venv/bin/python
將 code section 原樣寫入暫存檔，不要改寫 SQL。
執行：
PYTHONPATH=/home/yillkid/workspace/mariadb-demo /home/yillkid/mariadb-course-venv/bin/python /tmp/opencode/run_crud.py
回報實際命令、created、updated、before_update、after_update、類 SQL 查詢結果、deleted 與 exit code。
最後用一句話說明是否只留下資料庫原狀。
先說明計畫，確認後才建立暫存檔並執行。
```

也可以自己把 code section 存成 `workshop/11-crud.py` 後執行。基本任務是看懂 CRUD 與驗證，不是先手寫 Python。

## 4. 執行與 SQL 驗證

```bash
PYTHONPATH=. python3 workshop/11-crud.py
printf 'exit=%s\n' "$?"
```

預期：`created=1`、`updated=1`、價格 `125.50`、stock 從 1 變 4、類 SQL 查詢為 `None`、`deleted=1`、exit code 為 0。

用 MariaDB 驗證清理與正式資料：

```sql
SELECT product_id FROM products WHERE product_id IN ('P001', 'P915');
SELECT product_id, name, price, stock FROM products WHERE product_id = 'P001';
```

P915 不應存在，P001 應維持原值。

## 交件

完整 code section、Agent 或自己的說明、實際命令與 exit code、CRUD 輸出、SQL 驗證結果。不要提交密碼或私人設定檔。

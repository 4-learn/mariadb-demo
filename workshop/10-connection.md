# Ch10 Workshop：把完整 code section 交給 Agent 執行

## 任務

本章不要求你先補 Python。請先把主講義的完整 code section 貼給 Agent，要求它解釋並執行；也可以自己把程式存檔後執行。

## Code section

```python
from contextlib import closing
from course_db import connect

with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT DATABASE(), CURRENT_USER(), @@autocommit"
        )
        identity = cur.fetchone()

        cur.execute(
            """
            SELECT product_id, name, price
            FROM products
            WHERE product_id = ?
            """,
            ("P001",),
        )
        product = cur.fetchone()

        print(identity)
        print(product)
```

## 方式 A：自己執行

將程式存成 `workshop/10-connection.py`，不要修改 SQL，直接執行：

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python3 workshop/10-connection.py
printf 'exit=%s\n' "$?"
```

## 方式 B：請 Agent 執行

把 code section 和以下任務一起貼給 Agent：

```text
請先用簡單中文說明這段程式會查詢什麼、會不會修改資料。
不要修改檔案，不要讀取密碼或私人設定檔。
接著在目前課程 repo 執行這段程式，回報實際輸出與 exit code。
```

Agent 只需解釋與執行，不需要替你設計新程式。

## 驗證

預期內容類似：

```text
('mariadb_workshop_2026', 'course_app@localhost', 1)
('P001', '教學感測器 A', Decimal('800.00'))
exit=0
```

再用 MariaDB client 交叉確認：

```sql
SELECT DATABASE(), CURRENT_USER(), @@autocommit;
SELECT product_id, name, price FROM products WHERE product_id = 'P001';
```

確認：

```text
database 正確
course_app@localhost 正確
P001 價格為 800.00
只有 SELECT，沒有修改資料
沒有提交密碼或私人設定檔
```

## 交件

- 使用方式：自己執行或 Agent 執行。
- 完整 code section。
- 實際輸出與 exit code。
- SQL 交叉驗證結果。
- 一句話說明 `execute()` 與 `fetchone()` 的用途。

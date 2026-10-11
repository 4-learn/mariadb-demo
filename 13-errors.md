# 13 錯誤處理：看懂錯誤，再安全回報

> **定位**：延續 Ch5～9 的主鍵、外鍵、權限與連線概念，用一個完整 code section 觀察錯誤。學生不必先會 Python；先讓 Agent 執行，再看錯誤類型、errno 與資料庫狀態。

[上一節](12-transactions.md) · [下一節](14-indexes.md)

## 1. 先回想已學錯誤

```text
1062：主鍵或唯一鍵重複
1452：外鍵不存在
1142：權限不足
2002：socket／連線問題
```

錯誤不是「查無資料」。要保留真正的失敗，不能使用 `except: pass`、`INSERT IGNORE` 或把所有錯誤重試。

## 2. Code section：預期的重複鍵錯誤

```python
from contextlib import closing
from course_db import connect

with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        conn.begin()
        try:
            cur.execute(
                "INSERT INTO products "
                "(product_id, category_id, name, price, stock, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("P914", 1, "錯誤處理測試品", "77.00", 1, "active"),
            )
            print("first insert", cur.rowcount)

            try:
                cur.execute(
                    "INSERT INTO products "
                    "(product_id, category_id, name, price, stock, status) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    ("P914", 1, "重複測試品", "66.00", 1, "active"),
                )
            except Exception as exc:
                print("duplicate", type(exc).__name__, getattr(exc, "errno", None))
                conn.rollback()

            cur.execute("SELECT 1")
            print("connection usable", cur.fetchone())
        finally:
            conn.rollback()

with closing(connect()) as observer:
    with closing(observer.cursor()) as cur:
        cur.execute("SELECT product_id FROM products WHERE product_id = ?", ("P914",))
        print("after rollback", cur.fetchone())
```

看懂三件事即可：錯誤發生在第二次 INSERT；rollback 取消第一次 INSERT；第二條連線確認 P914 不存在。`errno=1062` 是可分類的證據，不是要隱藏的訊息。

## 3. Workshop：請 Agent 解釋與執行

```text
你現在在 Ubuntu 的 ~/workspace/mariadb-demo repo 根目錄。
請只驗證這段 Ch13 error-handling code，不要設計新程式。
先說明第一次 INSERT、第二次重複 INSERT、errno、rollback、SELECT 1 與第二條連線。
不要讀取、列印或修改密碼、JSON 設定檔、token、.cnf 或私人檔案。
不要修改 repo；可在 /tmp/opencode/run_errors.py 建立暫存檔，執行後刪除。
必須使用 /home/yillkid/mariadb-course-venv/bin/python，PYTHONPATH=/home/yillkid/workspace/mariadb-demo。
原樣寫入 code section；先說明計畫，確認後才執行。
回報 duplicate 的錯誤類型、errno、SELECT 1、after rollback 與 exit code；失敗不可假裝成功。
```

也可以自己執行完整 code section。不要為了讓畫面好看而刪除錯誤。

## 4. 驗證與延伸

預期看到：

```text
duplicate ... 1062
connection usable (1,)
after rollback None
exit code=0
```

用 MariaDB 再確認：

```sql
SELECT product_id FROM products WHERE product_id = 'P914';
```

應為空。連線失敗、權限錯誤與外鍵錯誤可在教師提供的其他案例中觀察；本章先學會保留並分類一個真實錯誤。

## 交件

完整 code section、Agent 或自己的說明、實際錯誤類型與 errno、exit code、SQL 驗證結果。不要提交密碼、私人設定檔或完整 socket 路徑。

# 12 交易：兩個寫入必須一起成功

> **定位**：延續 Ch5～9 的外鍵與 Ch11 的 DML，用一個成功／失敗案例看懂 BEGIN、COMMIT、ROLLBACK。先看完整 code，再請 Agent 解釋與執行。

[上一節](11-parameterized-crud.md) · [下一節](13-errors.md)

## 1. 先連回已學概念

產品與 SOP 關聯必須符合外鍵：

```sql
SELECT product_id, document_id FROM product_documents WHERE document_id = 'D001';
SELECT product_id FROM products WHERE product_id IN ('P912','P913');
```

本章的業務操作是「新增產品，再新增它與 SOP 的關聯」。兩步一起成功才算成功；第二步失敗，第一步也必須消失。

## 2. Code section：成功與失敗交易

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
                ("P912", 1, "交易成功測試品", "99.00", 1, "active"),
            )
            created = cur.rowcount
            cur.execute(
                "INSERT INTO product_documents (product_id, document_id) VALUES (?, ?)",
                ("P912", "D001"),
            )
            linked = cur.rowcount
            conn.commit()
            print("commit", created, linked)
        except BaseException:
            conn.rollback()
            raise

        conn.begin()
        try:
            cur.execute(
                "INSERT INTO products "
                "(product_id, category_id, name, price, stock, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("P913", 1, "交易失敗測試品", "88.00", 1, "active"),
            )
            cur.execute(
                "INSERT INTO product_documents (product_id, document_id) VALUES (?, ?)",
                ("P913", "D999"),
            )
            conn.commit()
        except BaseException as exc:
            conn.rollback()
            print("rollback", type(exc).__name__, getattr(exc, "errno", None))

        cur.execute("DELETE FROM product_documents WHERE product_id = ?", ("P912",))
        cur.execute("DELETE FROM products WHERE product_id = ?", ("P912",))
        conn.commit()
        print("cleanup", cur.rowcount)
```

只要看懂：`begin()` 開始一組操作；`commit()` 保留全部；`rollback()` 取消尚未提交的全部寫入；D999 不存在，所以外鍵錯誤不能只留下 P913。

## 3. Workshop：請 Agent 解釋與執行

```text
你現在在 Ubuntu 的 ~/workspace/mariadb-demo repo 根目錄。
請只驗證這段 Ch12 transaction code，不要設計新程式。
先說明 begin、commit、rollback、外鍵錯誤與為什麼 P913 不應留下。
不要讀取秘密，不要修改 repo，不要停用 FOREIGN_KEY_CHECKS；可在 /tmp/opencode/run_transactions.py 建立暫存檔，執行後刪除。
必須使用 /home/yillkid/mariadb-course-venv/bin/python，PYTHONPATH=/home/yillkid/workspace/mariadb-demo。
原樣寫入 code section；先說明計畫，確認後才執行。
回報成功 commit、失敗 errno、rollback、cleanup 與 exit code；失敗不可假裝成功。
```

也可以自己執行完整 code section。

## 4. 驗證

```sql
SELECT product_id FROM products WHERE product_id IN ('P912','P913');
SELECT product_id, document_id FROM product_documents WHERE product_id IN ('P912','P913');
```

成功與失敗測試結束後兩者都應被清理；正式 checkpoint 不變。交件包含實際輸出、exit code、外鍵錯誤 errno 與 SQL 驗證。

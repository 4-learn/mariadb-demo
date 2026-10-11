# 11 參數化 CRUD：把 SQL 結構與資料值分開

> **定位**：延續 Ch5–9 的 `SELECT`、條件與交易觀念，用一個受保護的 `P9xx` 練習完成參數化 CRUD。先完成 code section，再執行、回讀與清理。

[上一節](10-python-connection.md) · [下一節](12-transactions.md)

## 學習目標

- 用 `cursor.execute(sql, values)` 傳值，不拼接 SQL。
- 完成 INSERT、SELECT、UPDATE、DELETE，並用 `rowcount` 與回讀驗證。
- 以 `O'Reilly` 與類 SQL 字串證明資料值不會改寫 SQL。
- 只使用 `P915`，最後回滾，不修改 P001–P012。

## 1. 先連回 Ch5–9

在 MariaDB client 先確認基準：

```sql
SELECT product_id, name, price, stock FROM products WHERE product_id = 'P001';
SELECT COUNT(*) AS products FROM products;
```

本章的 Python `SELECT` 應與同一條件得到相同資料。`?` 是值的位置，不是 SQL 字串的一部分；`("P915",)` 是單元素 tuple。

## 2. Code section：完成一組可回滾 CRUD

這是本章唯一需要修改的區段。請完成 TODO；所有外部值都必須是參數，不能使用 f-string、`%` 或 `.format()`。

```python
from contextlib import closing
from course_db import connect

with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        conn.begin()
        try:
            # TODO 1：INSERT P915，名稱為 O'Reilly；價格 125.50、庫存 1。
            # 使用 ? 與 tuple，記錄 created = cur.rowcount。
            created = None

            # TODO 2：SELECT P915，記錄 row；再 UPDATE stock=4，記錄 updated。
            # 用 row 回讀 name/price/stock，確認單引號原樣保留。
            row = None
            updated = None

            # TODO 3：以參數查詢 "P915' OR 1=1 -- "，記錄 injection_row。
            # 它應為 None；接著 DELETE P915，記錄 deleted。
            injection_row = None
            deleted = None

            print(created, updated, row, injection_row, deleted)
        finally:
            # 練習資料不可留下；正式資料不可修改。
            conn.rollback()
```

示範中的 `course_db.py` helper 與 `demo/11-crud.py` 可用來對照，但不要用字串拼接取代參數。`rowcount=0` 只表示沒有受影響的列，仍要回讀判斷原因。

## 3. 執行與驗證

在 repo 根目錄執行你的完成檔（或先執行教師示範）：

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/11-crud.py
```

通過條件：

```text
created=1、updated=1、name 保留 O'Reilly、price=125.50、stock=4
類 SQL 查詢結果為 None
刪除後 P915 不存在；P001 仍存在
```

再用 SQL 交叉驗證：

```sql
SELECT product_id FROM products WHERE product_id IN ('P001','P915');
```

## 4. 交件

提交 code section、執行命令與 exit code、`rowcount` 和回讀結果、SQL 參數化證據，以及 P001/P915 的最後查詢。不要提交密碼、私人設定檔或修改 P001–P012。

# Ch11 Workshop：參數化 CRUD

沿用 Ch5–9 的條件查詢與 Ch10 的連線。只用 `P915`，所有值以 `?` 傳入，最後回滾。

## 共同 code section

請自行完成 TODO，或選擇下方的 Agent completion；兩條路線使用完全相同的程式與驗證。

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
            conn.rollback()
```

## 自行完成或 Agent completion

- **自行完成**：填入三個 TODO，執行並修正錯誤。
- **Agent completion**：可貼上這段安全短 prompt：

```text
只修改這個 code section 的 TODO。使用 MariaDB ? 參數與 tuple，禁止 f-string、%、format、DDL 和修改 P001–P012。完成後先列出 diff，再執行一次；最後回報 rowcount、回讀值與 exit code，不要輸出密碼或設定檔。
```

## 執行與驗證

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/11-crud.py
```

預期 `created=1`、`updated=1`、`price=125.50`、`stock=4`，`P915' OR 1=1 -- ` 查不到，刪除後 P915 不存在。用 MariaDB 查詢確認 P001 仍存在；交件包含程式、輸出、exit code 與參數化證據。不要提交私人設定。

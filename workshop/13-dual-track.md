# Ch13 Workshop：安全錯誤處理

延續 Ch5–9 的約束與 Ch12 的 rollback。練習重複鍵 `P914`，不輸出秘密，也不把失敗當成功。

## 共同 code section

請自行完成 TODO，或使用下方 Agent completion；兩條路線執行同一段程式。

```python
from contextlib import closing
import mariadb
from course_db import connect, create_product, get_product

with closing(connect()) as conn:
    conn.begin()
    try:
        # TODO 1：參數化新增 P914，再故意以同一 ID 新增一次。
        # 捕捉 mariadb.IntegrityError，僅接受 errno=1062，輸出安全摘要。
        duplicate_errno = None

    except mariadb.IntegrityError as exc:
        # TODO 2：記錄 exc.errno；不是 1062 就重新 raise，不可 except: pass。
        duplicate_errno = exc.errno
        conn.rollback()
        print(f"duplicate: errno={duplicate_errno}; not retried")
    else:
        conn.rollback()

    # TODO 3：回讀 P914 應為 None，並執行 SELECT 1 證明同一連線仍可用。
    print(get_product(conn, "P914"))
```

## 自行完成或 Agent completion

- **自行完成**：完成 TODO，執行真實 demo、socket 負面測試與 mock 測試。
- **Agent completion**：可貼上這段安全短 prompt：

```text
只修改這個 code section 的 TODO。用 mariadb.IntegrityError 並檢查 errno=1062，錯誤時 rollback、保留原始錯誤，禁止 except: pass、IGNORE、REPLACE、無限重試。只輸出錯誤型別/errno，不輸出密碼或私人設定；列出 diff、測試結果與 exit code。
```

## 執行與驗證

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/13-errors.py
PYTHONPATH=. python workshop/13-connection-failure.py
PYTHONPATH=. python workshop/13-errors.py
```

應看到 1062 不重試、rollback 後 `SELECT 1=1`、資源關閉，socket 2002 且設定未變，mock `OK`。以 SQL 確認 P914 不存在；交件包含摘要、測試輸出、exit code 與安全檢查。

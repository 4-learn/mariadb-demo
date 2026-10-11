# 13 錯誤處理：先分類，再安全回報

> **定位**：延續 Ch5–9 的約束與 Ch12 的交易，將失敗按階段、例外型別與 errno 分類；資源要關閉，錯誤不可被吞掉，秘密不可輸出。

[上一節](12-transactions.md)

## 學習目標

- 分辨設定、連線、cursor、SQL、權限、主鍵與外鍵錯誤。
- 以例外型別與 errno 分類，不靠模糊字串猜測。
- 失敗時 rollback、關閉已建立資源，並保留原始錯誤。
- CLI 只輸出安全摘要，例如 `OperationalError/2002`。

## 1. 錯誤地圖

| 階段 | 典型證據 | 行動 |
|---|---|---|
| 設定檔 | `FileNotFoundError` | 修正路徑，不執行 SQL |
| 連線 | `OperationalError`, 2002 | 檢查 socket/環境 |
| 主鍵 | `IntegrityError`, 1062 | 回報重複，不覆蓋、不重試 |
| 外鍵 | `IntegrityError`, 1452 | rollback，檢查來源 ID |
| SQL | 1064 | 修正程式，不無限重試 |
| 權限 | 1142 | 停止越權，不要求全域 GRANT |

`connect()` 失敗沒有 connection 可關；cursor 建立失敗仍要關 connection；`execute()` 失敗要關 cursor 與 connection。`close` 釋放資源，`rollback` 撤回未提交資料，兩者不是同一件事。

## 2. Code section：分類重複鍵並保留資源責任

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

可用 `demo/13-errors.py` 看真實 MariaDB 的完整負面案例；`workshop/13-connection-failure.py` 使用暫時設定檔測試 2002，不能改原始設定。不要 `except: pass`、`INSERT IGNORE`、`REPLACE` 或輸出密碼、完整私人 JSON、socket 設定與含秘密的原始訊息。

## 3. 執行與驗證

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/13-errors.py
PYTHONPATH=. python workshop/13-connection-failure.py
PYTHONPATH=. python workshop/13-errors.py
```

預期：`errno=1062` 且不重試、rollback 後 `SELECT 1=1`、資源關閉；socket 測試為 2002 且原始設定不變；mock 測試 `OK`。最後用 SQL 確認 P914 不存在。

## 4. 交件

提交 code section、1062/2002 摘要、mock 測試結果、錯誤分類與資源責任說明、P914 最終查詢。不要提交密碼、私人設定檔或完整 exception message。

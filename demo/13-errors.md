# 13 錯誤處理：先分類，再安全回報

> **定位**：區分設定、連線、SQL、權限與完整性錯誤；關閉已建立的資源，不洩漏秘密，也不把失敗當成功。

## 學習目標

完成本節後，你應該能夠：

- 依例外型別與錯誤碼分類失敗原因
- 區分連線尚未建立、游標失敗與 SQL 執行失敗
- 在成功與失敗路徑關閉 cursor、connection
- 保留真正的錯誤，不用 `except: pass` 隱藏問題
- 讓 CLI 回報安全摘要，不輸出密碼或私人設定

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

本節使用 Ch12 的 Python 虛擬環境、自己的 `course_app` 設定檔與 P9xx 練習 ID。

---

## 情境

客服說「新增失敗」，但原因可能不同：

```text
設定檔不存在
socket 不存在
產品 ID 重複
外鍵不存在
權限不足
SQL 語法錯誤
```

這些不能都顯示成「查無資料」，也不能把原始例外與設定檔內容全部印出。

本節會使用預期失敗案例，證明程式能：

```text
分辨原因
回復交易
關閉資源
安全回報
```

---

## 講解

### 1. 先確認失敗階段

| 情況 | 證據 | 處理方向 |
| --- | --- | --- |
| 設定檔不存在 | `FileNotFoundError`、exit 1 | 修正路徑；尚未執行 SQL |
| 設定欄位或權限錯誤 | `ValueError`、exit 1 | 檢查 JSON 與 0600；不印密碼 |
| socket 不存在 | `OperationalError`、通常 errno 2002 | 檢查本機環境；不是查無產品 |
| 主鍵重複 | `IntegrityError`、1062 | 回報 ID 已使用；不要覆蓋 |
| 外鍵不存在 | `IntegrityError`、1452 | 回滾交易，檢查來源 ID |
| 權限不足 | errno 1142 | 停止越權；不要要求全域 GRANT |
| SQL 語法錯誤 | errno 1064 | 修正程式；不要無限重試 |

使用例外型別與錯誤碼分類，不要只猜錯誤訊息中的文字。

### 2. 預期的重複鍵錯誤

公開 demo 檔案是：

```text
demo/13-errors.py
```

在自己的 VM 執行：

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/13-errors.py
```

預期：

```text
duplicate: errno=1062; not retried
rollback complete; same connection SELECT 1=1
cursor and connection closed
```

Demo 先在交易內新增 P914，再用同一 ID 新增一次。程式只接受：

```text
mariadb.IntegrityError
errno = 1062
```

最後會 `rollback`，確認 P914 不存在，再用同一條連線執行 `SELECT 1`。

不要：

```text
except: pass
INSERT IGNORE
REPLACE
無限重試
```

這些做法會把真正的資料問題藏起來，或把新增偷偷變成覆蓋。

### 3. 資源關閉的三個時點

共用程式檔案：

```text
course_db.py
```

最小讀取範例：

```python
from contextlib import closing
from course_db import connect, get_product

with closing(connect()) as conn:
    product = get_product(conn, "P001")
    print(product["product_id"])
```

不同失敗位置：

```text
connect() 失敗：沒有 conn，不要關閉未建立的變數
cursor() 失敗：conn 已建立，仍要關閉 conn
execute() 失敗：cursor 與 conn 都要關閉
```

`get_product()` 會關閉自己的 cursor；外層的 `closing(connect())` 負責 connection。

關閉資源不等於回滾交易：

```text
close：釋放連線／游標
rollback：撤回尚未提交的資料變更
```

### 4. 真實 socket 失敗

教師提供的 Workshop 檔案：

```text
workshop/13-connection-failure.py
```

若要執行真實 driver 的 socket 負面測試：

```bash
PYTHONPATH=. python workshop/13-connection-failure.py
```

它會使用暫時設定檔，把 socket 改成不存在的位置，不修改你的原始設定檔。

預期：

```text
connection rejected: errno=2002; no connection returned
original config unchanged; temporary config removed
```

### 5. Mock 測試能證明什麼

教師解答檔案：

```text
workshop/13-errors.py
```

執行：

```bash
PYTHONPATH=. python workshop/13-errors.py
```

它使用 Python 標準函式庫的 mock，檢查：

```text
commit／rollback 是否被呼叫
cursor／connection 是否關閉
參數是否與 SQL 分開
connect 失敗時是否保留原始例外
```

Mock 測試不能證明真實 MariaDB 已經執行外鍵或真的提交；真實資料庫證據來自 Ch12 與 `demo/13-errors.py`。

### 6. 安全錯誤輸出

`course_db.py` 的 CLI 只回報例外種類與錯誤碼，例如：

```json
{"error":"OperationalError","errno":2002}
```

不要輸出：

```text
密碼
完整私人 JSON
完整 socket 設定
含連線資訊的原始 exception message
```

---

## Workshop

### 題目

在自己的 VM 完成：

1. 執行 `demo/13-errors.py`，保留重複鍵 1062、回滾與 `SELECT 1` 結果。
2. 執行 `workshop/13-connection-failure.py`，確認原始設定檔沒有改變。
3. 執行 `workshop/13-errors.py`，確認五個 mock tests 通過。
4. 說明三種資源狀態：connect 失敗、cursor 失敗、execute 失敗。
5. 檢查交件內容沒有密碼或私人設定。

### 預期輸出

```text
duplicate: errno=1062; not retried
rollback complete; same connection SELECT 1=1
cursor and connection closed
connection rejected: errno=2002; no connection returned
original config unchanged; temporary config removed
Ran 5 tests
OK
```

Mock 測試的 `OK` 不能取代真實 MariaDB 的錯誤證據。

### 交件

提交：

- 1062 重複鍵結果
- 2002 socket 失敗結果
- mock tests 結果
- 一段錯誤分類說明
- 一段資源關閉責任說明

不要提交密碼、私人設定檔內容或完整錯誤訊息。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

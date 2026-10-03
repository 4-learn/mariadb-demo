# 10 Python 連線：先確認身分，再查一筆資料

> **定位**：用私人設定檔建立最小權限的 Python 連線，確認資料庫身分與 checkpoint，並正確關閉資源。

## 學習目標

完成本節後，你應該能夠：

- 使用 `course_app` 設定檔建立 MariaDB 連線
- 不把密碼寫入程式、命令列或交件
- 用 `DATABASE()`、`CURRENT_USER()` 與資料集版本確認環境
- 分辨 connection、cursor 與查詢結果
- 在成功與例外時正確關閉資源
- 分辨查無資料和連線／設定檔錯誤

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

本節程式需要在課程資料夾執行，並使用 `PYTHONPATH=.` 找到共用的 `course_db.py`。

---

## 情境

客服已能用 SQL 查詢產品，現在要做一個 Python 查詢工具。

程式沒有報錯，不代表查到正確資料庫。它可能：

```text
連到錯的 database
使用錯的帳號
讀到錯的資料集版本
沒有關閉 connection 或 cursor
```

所以第一個 Python 功能不是新增資料，而是輸出可以核對的環境證據。

本節只讀取資料，不修改正式 checkpoint。

---

## 講解

### 1. 準備私人設定檔

教師提供：

```text
$HOME/mariadb-course-app.json
```

設定檔應包含四個鍵：

```json
{
  "user": "course_app",
  "password": "教師提供的密碼",
  "database": "mariadb_workshop_2026",
  "unix_socket": "教師提供的 socket 絕對路徑"
}
```

設定檔只放在自己的 VM，不要放進 Git、講義、截圖或命令列。

檢查檔案權限，不要顯示內容：

```bash
stat -c '%a %n' "$HOME/mariadb-course-app.json"
```

預期權限：

```text
600
```

### 2. 使用 course_app 建立連線

在課程根目錄執行：

```bash
python3 course_db.py check
```

或執行公開 demo：

```bash
PYTHONPATH=. python3 demo/10-connection.py
```

Python 程式會從私人設定檔取得連線資訊，不把密碼寫在 SQL 或 Python 原始碼中。

這一章使用：

```text
course_app@localhost
```

不是 root，也不是 `course_editor`。

### 3. connection、cursor 與結果

最小查詢範例：

```python
from contextlib import closing
from course_db import connect

with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT DATABASE(), CURRENT_USER(), @@autocommit"
        )
        print(cur.fetchone())
```

預期：

```text
('mariadb_workshop_2026', 'course_app@localhost', 1)
```

三個角色：

```text
connection：與 MariaDB server 的工作階段
cursor：執行 SQL、取得結果
fetchone()：取回一列結果
```

`closing(...)` 會在離開區塊時呼叫 `.close()`；即使區塊中發生例外，也會關閉已建立的資源。

### 4. 核對 checkpoint

```bash
python3 course_db.py check
```

標準結果應包含：

```json
{
  "account": "course_app@localhost",
  "autocommit": 1,
  "chunks": 16,
  "database": "mariadb_workshop_2026",
  "documents": 8,
  "products": 12,
  "versions": ["products-v1", "sop-v1"]
}
```

這些欄位一起證明：

```text
帳號正確
資料庫正確
autocommit 狀態正確
資料筆數正確
資料集版本正確
```

### 5. 查詢一筆產品

```bash
python3 course_db.py get P001
```

P001 應是：

```text
name：教學感測器 A
category_id：1
price：800.00
stock：10
status：active
```

Python 內部的金額使用 `Decimal`；命令列輸出固定兩位小數。不要把金額轉成 `float`。

### 6. 失敗不是空清單

執行不存在的設定檔：

```bash
python3 course_db.py \
  --config /nonexistent/course-app.json check
printf '%s\n' "$?"
```

預期：

```text
FileNotFoundError
errno = 2
exit code = 1
```

這和查不到產品不同：

```text
P999 不存在：查詢結果可以是 None
設定檔不存在：程式錯誤，應回報例外
```

不要把設定檔錯誤、權限錯誤或 socket 連線錯誤顯示成「查無資料」。

### 7. autocommit 先認識即可

本節會讀出：

```text
@@autocommit = 1
```

這表示一般 DML 通常會自動提交。本節不做寫入，也不在這裡深入交易控制；`BEGIN`、`COMMIT`、`ROLLBACK` 會在 Ch12 完整介紹。

---

## Workshop

### 題目

在自己的 VM 完成：

1. 檢查 `mariadb-course-app.json` 權限為 600，不提交檔案內容。
2. 執行 checkpoint，確認 database、account、autocommit、版本與三個資料數量。
3. 查詢 P001，核對名稱、分類、價格、庫存與狀態。
4. 用不存在的設定檔執行一次，保存退出碼與不含秘密的錯誤摘要。
5. 說明 connection、cursor 的關閉責任，以及為什麼 connect 失敗時不能關閉不存在的 connection。

### 預期輸出

```text
account = course_app@localhost
database = mariadb_workshop_2026
autocommit = 1
products = 12
documents = 8
chunks = 16
versions = products-v1, sop-v1
P001 price = 800.00
connection closed
```

負面測試：

```text
FileNotFoundError
errno = 2
exit code = 1
```

### 交件

提交：

- checkpoint 結果
- P001 查詢結果
- 設定檔權限結果
- 負面測試的錯誤類型與退出碼
- 資源關閉責任的說明

不要提交密碼、私人設定檔內容或完整 socket 設定。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

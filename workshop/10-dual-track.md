# Ch10 雙軌 Workshop

## 雙軌實作

### 共同概念

兩條路線都要確認 `course_app`、database、`CURRENT_USER()`、`@@autocommit`，並且不把密碼寫入程式或命令列。

### 路線 A：Agent／Vibe Coding

請先讓 Agent 讀取 `course_db.py` 與 `demo/10-connection.py`，只說明設定檔來源、帳號、資料庫與資源關閉方式，不要修改。確認計畫後，才讓它加入最小的身分查詢。完成後先看：

```bash
git diff -- demo/10-connection.py course_db.py
PYTHONPATH=. python3 demo/10-connection.py
```

### 路線 B：Python-first

自行使用 `connect()`、`cursor()` 與 `execute()` 完成同一個只讀查詢；可參考本章既有程式，不要求另建連線框架。

### 共同驗證與交件

用 MariaDB client 交叉確認 `DATABASE()`、`CURRENT_USER()` 與 `course_meta`。交件包含命令、exit code、輸出與你如何確認 connection／cursor 已關閉。


## 驗收規則

Agent 路線與 Python-first 路線使用相同資料庫驗證；不得把 Agent 摘要當成證據。

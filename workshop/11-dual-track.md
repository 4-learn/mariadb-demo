# Ch11 雙軌 Workshop

## 雙軌實作

### 共同概念

SQL 結構與資料值必須分開；所有外部值使用 `?` 參數與 tuple，不使用 f-string、`%` 或 `.format()` 拼接 SQL。練習只准使用 P9xx，最後清理。

### 路線 A：Agent／Vibe Coding

請 Agent 先閱讀 schema、`course_db.py` 與 `demo/11-crud.py`，提出 CRUD 計畫；確認後才修改。要求它列出 diff，並檢查新增、讀取、修改、刪除都使用參數。

```bash
git diff -- demo/11-crud.py course_db.py
PYTHONPATH=. python3 demo/11-crud.py
```

### 路線 B：Python-first

自行完成一組 P9xx CRUD，使用 `cursor.execute(sql, values)`、`rowcount`、回讀與 finally／context manager；用 `O'Reilly` 測試文字值。

### 共同驗證與交件

交件包含 diff 或程式碼、rowcount、回讀結果，以及 SQL 沒有字串拼接的證據。用 MariaDB 查詢確認 P001～P012 未變。


## 驗收規則

Agent 路線與 Python-first 路線使用相同資料庫驗證；不得把 Agent 摘要當成證據。

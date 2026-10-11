# Ch13 雙軌 Workshop

## 雙軌實作

### 共同概念

錯誤要依階段與 errno 分類，不可用 `except: pass` 隱藏，也不可輸出密碼或私人設定。

### 路線 A：Agent／Vibe Coding

先讓 Agent 執行 `demo/13-errors.py`，不要先改檔。請它根據實際 exit code 與錯誤碼提出分類與修正計畫；確認後才修改，並保留 diff。

```bash
git diff -- demo/13-errors.py course_db.py
PYTHONPATH=. python3 demo/13-errors.py
```

### 路線 B：Python-first

自行以例外型別與 errno 分類設定、連線、主鍵、外鍵、權限與語法錯誤；保留真正失敗，並在 finally 關閉資源。

### 共同驗證與交件

確認 `errno=1062`、`rollback complete`、`cursor and connection closed`，並以 SQL 確認 P914 最後不存在；另證明同一連線仍可執行 `SELECT 1`。


## 驗收規則

Agent 路線與 Python-first 路線使用相同資料庫驗證；不得把 Agent 摘要當成證據。

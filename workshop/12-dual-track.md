# Ch12 雙軌 Workshop

## 雙軌實作

### 共同概念

新增產品與 `product_documents` 關聯是同一個業務操作：全部成功才 commit，任何一步失敗都 rollback。成功案例為 P912／D001，失敗案例為 P913／D999。

### 路線 A：Agent／Vibe Coding

請 Agent 先讀取 `demo/12-transactions.py` 與外鍵 schema，說明交易邊界與兩個案例；確認計畫後才修改或執行。執行前要求它列出資料庫與預計變更。

```bash
git diff -- demo/12-transactions.py course_db.py
PYTHONPATH=. python3 demo/12-transactions.py
```

### 路線 B：Python-first

自行完成 `begin()`、兩次 DML、`commit()` 與例外時 `rollback()`；不可只依賴畫面輸出。

### 共同驗證與交件

用第二條 MariaDB 連線查詢 products 與 product_documents：P912 成功存在，P913 及其關聯完全不存在。交件包含成功／失敗 exit code、交易結果與清理結果。


## 驗收規則

Agent 路線與 Python-first 路線使用相同資料庫驗證；不得把 Agent 摘要當成證據。

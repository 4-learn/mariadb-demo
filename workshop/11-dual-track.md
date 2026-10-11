# Ch11 Workshop：貼上完整 CRUD code 並驗證

## 任務

把主講義的完整 Ch11 code section 貼給 Agent，或自己存成暫存程式執行。不要先補 TODO，也不要修改 repo。

## Agent prompt

```text
你現在在 Ubuntu 的 ~/workspace/mariadb-demo repo 根目錄。
請只驗證這段 Ch11 CRUD code，不要設計新程式。
先用簡單中文說明 INSERT、SELECT、UPDATE、DELETE、? 參數與 rollback。
不要讀取、列印或修改密碼、JSON 設定檔、token、.cnf 或私人檔案。
不要修改 repo；可以在 /tmp/opencode/run_crud.py 建立暫存檔，執行後刪除。
必須使用 /home/yillkid/mariadb-course-venv/bin/python，並設定 PYTHONPATH=/home/yillkid/workspace/mariadb-demo。
把 code section 原樣寫入暫存檔，不要改寫 SQL。
回報實際命令、created、updated、回讀值、類 SQL 查詢結果、deleted、exit code。
先說明計畫，確認後才執行。
```

## 驗證

```text
created=1
updated=1
O'Reilly 原樣保留
stock=4
類 SQL 查詢為 None
deleted=1
exit code=0
```

最後用 SQL 確認 P915 已清理、P001 未改變。不要提交秘密。

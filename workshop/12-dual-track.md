# Ch12 Workshop：貼上完整交易 code 並驗證

把主講義的完整 code section 貼給 Agent，或自己存檔執行。

## Agent prompt

```text
你現在在 Ubuntu 的 ~/workspace/mariadb-demo repo 根目錄。
請只驗證這段 Ch12 transaction code，不要設計新程式。
先說明 begin、commit、rollback、外鍵錯誤與為什麼 P913 不應留下。
不要讀取秘密，不要修改 repo，不要停用 FOREIGN_KEY_CHECKS；可在 /tmp/opencode/run_transactions.py 建立暫存檔，執行後刪除。
必須使用 /home/yillkid/mariadb-course-venv/bin/python，PYTHONPATH=/home/yillkid/workspace/mariadb-demo。
原樣寫入 code section；先說明計畫，確認後才執行。
回報成功 commit、失敗 errno、rollback、cleanup 與 exit code；失敗不可假裝成功。
```

## 驗證

```sql
SELECT product_id FROM products WHERE product_id IN ('P912','P913');
SELECT product_id, document_id FROM product_documents WHERE product_id IN ('P912','P913');
```

確認 P912、P913 及其關聯都已清理，正式 checkpoint 沒有漂移。交件包含實際命令、輸出、exit code 與 SQL 驗證。

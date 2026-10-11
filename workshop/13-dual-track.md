# Ch13 Workshop：貼上完整錯誤處理 code 並驗證

把主講義的完整 code section 貼給 Agent，或自己存檔執行。

## Agent prompt

```text
你現在在 Ubuntu 的 ~/workspace/mariadb-demo repo 根目錄。
請只驗證這段 Ch13 error-handling code，不要設計新程式。
先說明第一次 INSERT、第二次重複 INSERT、errno、rollback、SELECT 1 與第二條連線。
不要讀取秘密，不要修改 repo；可在 /tmp/opencode/run_errors.py 建立暫存檔，執行後刪除。
必須使用 /home/yillkid/mariadb-course-venv/bin/python，PYTHONPATH=/home/yillkid/workspace/mariadb-demo。
原樣寫入 code section；先說明計畫，確認後才執行。
回報 duplicate 的錯誤類型、errno、SELECT 1、after rollback 與 exit code；失敗不可假裝成功。
```

## 驗證

```text
duplicate ... 1062
connection usable (1,)
after rollback None
exit code=0
```

再用 SQL 確認 P914 不存在。不要提交密碼或私人設定檔。

# 10 Workshop：完成最小 Python 連線查詢

## 目標

把主講義的兩個 code section TODO 補完，確認 Python 連線和 Ch5～9 已學的 SQL 查詢指向同一個 checkpoint。

## Code section

請完成 `workshop/10-connection.py`：

```python
from contextlib import closing
from course_db import connect

with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        # TODO 1：執行身分與交易設定查詢，並把結果存到 identity。
        identity = None

        # TODO 2：查詢 P001 的 product_id、name、price，並把結果存到 product。
        product = None

        print(identity)
        print(product)
```

## 完成方式 A：自己補完

使用主講義提示完成兩個 TODO。不要改 `course_db.py`、私人設定檔或正式資料。

## 完成方式 B：要求 Agent 補完

在 repo 根目錄啟動 Agent，貼上：

```text
請只修改 workshop/10-connection.py 的兩個 TODO，不要修改其他檔案，不要讀取私人設定檔。
先說明每個 TODO 要執行的 SQL 與預期結果，等我確認後才修改。
必須使用 SELECT、? 參數與 ("P001",) tuple，不得拼接 SQL。
修改後列出 git diff，不要自行執行寫入資料庫的命令。
```

確認 diff 只包含兩個 TODO 的實作後，才執行。

## 執行

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python3 workshop/10-connection.py
printf 'exit=%s\n' "$?"
```

## 預期結果

應看到一列包含：

```text
mariadb_workshop_2026
course_app@localhost
1
```

以及 P001 的 `product_id`、名稱與 `800.00`。實際 tuple 顯示形式可以依 Connector 版本不同，但資料內容必須正確。

## SQL 交叉驗證

```bash
mariadb --defaults-file="$HOME/mariadb-course-app.cnf" mariadb_workshop_2026
```

```sql
SELECT DATABASE(), CURRENT_USER(), @@autocommit;
SELECT product_id, name, price FROM products WHERE product_id = 'P001';
SELECT COUNT(*) AS products FROM products;
```

## 交件

- 完成方式：自己補完或 Agent 補完。
- `git diff` 或修改前後的 code section。
- Python exit code 與輸出。
- SQL 交叉驗證結果。
- 不提交密碼、私人 JSON 或完整 socket 路徑。

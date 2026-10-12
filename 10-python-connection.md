# 10 Python 連線：先確認身分，再查一筆資料

> **定位**：先用 Ch5～9 已學的 SQL 查詢確認環境，再把同一個查詢交給一小段 Python 執行。學生不必先會寫 Python；可以把 code section 交給 Agent 執行與解釋。

[上一節](09-aggregate-like.md) · [下一節](11-parameterized-crud.md)

## 學習目標

- 了解 Python 程式如何連到已經學過的 MariaDB。
- 說明 `connect`、`cursor`、`execute`、`fetchone` 的角色。
- 讀取 `DATABASE()`、`CURRENT_USER()`、`@@autocommit` 與 P001。
- 執行後確認沒有修改資料，也沒有暴露密碼。

## 1. 先用 SQL 確認基準

Ch5～9 已經會用 MariaDB client。先執行：

```sql
SELECT DATABASE(), CURRENT_USER(), @@autocommit;
SELECT product_id, name, price FROM products WHERE product_id = 'P001';
```

這兩個查詢就是等等 Python 程式的對照答案。預期 database 是 `mariadb_workshop_2026`，帳號是 `course_app@localhost`，P001 價格是 `800.00`。

## 2. Python 環境準備（第一次使用才做）

如果教師尚未提供課程環境，第一次使用 Ubuntu VM 時先安裝系統依賴並建立專用 venv：

```bash
sudo apt update
sudo apt install -y build-essential pkg-config libmariadb-dev python3-dev python3-venv
python3 -m venv "$HOME/mariadb-course-venv"
. "$HOME/mariadb-course-venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install mariadb==1.1.14
```

確認 Connector 已安裝：

```bash
/home/yillkid/mariadb-course-venv/bin/python -c \
'import mariadb; print(mariadb.__version__)'
```

預期版本為 `1.1.14`。如果教師已經準備好 venv，不要重複安裝，只要執行：

```bash
test -x "$HOME/mariadb-course-venv/bin/python"
/home/yillkid/mariadb-course-venv/bin/python -c \
'import mariadb; print(mariadb.__version__)'
```

這些是學生或教師的課前環境準備，不是 Agent Workshop 任務。Agent 不得自行 `pip install`、修改系統套件或改變課程 venv；若 import 失敗，保留真實錯誤與 exit code，交給教師處理。

## 3. 開始 Python 連線

Python 需要一個連線設定檔，但學生不需要閱讀密碼。先啟用教師準備好的環境，只檢查檔案權限：

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
stat -c '%a %n' "$HOME/mariadb-course-app.json"
```

預期權限是 `600`。若這一步失敗，先把錯誤交給教師；不要把密碼寫進程式，也不要把設定檔內容貼給 Agent。

## 4. Code section：執行同一個查詢

這是完整、可直接執行的 code section。先不要挖空；Workshop 會把它貼上後交給 Agent 執行簡單任務。

```python
from contextlib import closing
from course_db import connect

with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT DATABASE(), CURRENT_USER(), @@autocommit"
        )
        identity = cur.fetchone()

        cur.execute(
            """
            SELECT product_id, name, price
            FROM products
            WHERE product_id = ?
            """,
            ("P001",),
        )
        product = cur.fetchone()

        print(identity)
        print(product)
```

只要先懂這四件事即可：

```text
connect()：建立資料庫連線
cursor()：準備執行 SQL
execute()：送出 SQL
fetchone()：取回一筆結果
```

`?` 表示資料值的位置；`("P001",)` 是傳入的值。`closing` 會在區塊結束時關閉已建立的資源。本段只有 `SELECT`，不會 INSERT、UPDATE 或 DELETE。

## 5. Workshop 任務

把上面的完整 code section 貼給 Agent，使用下面這個較完整的任務。這個任務允許 Agent 建立暫存檔，但不允許它自行改寫程式或碰私人設定：

```text
你現在在 Ubuntu 的 ~/workspace/mariadb-demo repo 根目錄。

任務：只驗證下面這段 Ch10 Python code section，不要設計新程式。

規則：
1. 先用簡單中文說明兩個 SELECT 查詢、connect、cursor、execute、fetchone、? 參數，以及為什麼這段程式不會 INSERT/UPDATE/DELETE。
2. 不要讀取、列印或修改任何密碼、JSON 設定檔、token、.cnf 或私人檔案。
3. 不要修改 repo 內任何檔案。可以在 /tmp/opencode/ 建立暫存的 run_query.py；執行完可刪除。
4. 必須使用已存在的課程環境：
   PYTHONPATH=/home/yillkid/workspace/mariadb-demo
   /home/yillkid/mariadb-course-venv/bin/python
5. 將 code section 原樣寫入暫存檔，不要把路徑改成別的 repo，也不要改寫 SQL。
6. 執行命令必須等同：
   PYTHONPATH=/home/yillkid/workspace/mariadb-demo /home/yillkid/mariadb-course-venv/bin/python /tmp/opencode/run_query.py
7. 執行後回報：實際命令、exit code、DATABASE()、CURRENT_USER()、@@autocommit、P001 的 product_id/name/price。
8. 最後明確回答：是否只讀、是否修改 repo、是否讀取秘密。

如果 Python、course_db 或資料庫連線失敗，保留真實錯誤與 exit code，不要假裝成功。
先說明計畫，確認後再建立暫存檔並執行。
```

也可以不使用 Agent，自己把 code section 存成 `workshop/10-connection.py` 後執行。這一章的基本任務不是補 Python，而是看懂查詢與驗證結果。

## 6. 執行與驗證

```bash
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python workshop/10-connection.py
printf 'exit=%s\n' "$?"
```

預期內容類似：

```text
('mariadb_workshop_2026', 'course_app@localhost', 1)
('P001', '教學感測器 A', Decimal('800.00'))
exit=0
```

實際 `Decimal` 顯示形式可能不同，但 database、account、autocommit 與 P001 資料必須符合前面的 SQL。

再用 MariaDB 查詢交叉驗證：

```sql
SELECT DATABASE(), CURRENT_USER(), @@autocommit;
SELECT product_id, name, price FROM products WHERE product_id = 'P001';
```

## 7. 失敗也要能分辨

不存在的設定檔是「連線設定失敗」，不是「P001 查不到」：

```bash
python3 course_db.py --config /nonexistent/course-app.json check
printf 'exit=%s\n' "$?"
```

只記錄錯誤類型與退出碼，不要貼私人設定內容。

## 8. 交件

- 完整 code section。
- Agent 的簡短說明，或自己的簡短說明。
- 實際輸出與 exit code。
- SQL 交叉驗證結果。
- 一句話說明這段 Python 對應 Ch5～9 的哪個 SQL 查詢。

不要提交密碼、私人 JSON、完整 socket 路徑或其他同學的設定檔。

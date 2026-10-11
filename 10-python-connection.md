# 10 Python 連線：先確認身分，再查一筆資料

> **定位**：先用 Ch5～9 已學的 SQL 概念確認資料庫，再把同一個只讀查詢放進一小段 Python。Python 不熟也可以選擇請 Agent 補完；本章最後仍以資料庫輸出驗證。

[上一節](09-aggregate-like.md) · [下一節](11-parameterized-crud.md)

## 學習目標

- 說明 Python 程式與 Ch5～9 SQL 的關係。
- 使用 `course_app` 連線，不把密碼寫入程式或命令列。
- 讀取 `DATABASE()`、`CURRENT_USER()`、`@@autocommit` 與課程 checkpoint。
- 分辨查無資料、設定錯誤與連線錯誤。

## 1. 先用 SQL 確認已知結果

Ch5～9 已經會用 MariaDB client 查詢資料。先確認本章的 Python 程式應該連到同一個環境：

```sql
SELECT DATABASE(), CURRENT_USER(), @@autocommit;
SELECT meta_key, meta_value FROM course_meta ORDER BY meta_key;
SELECT COUNT(*) AS products FROM products;
SELECT COUNT(*) AS documents FROM documents;
SELECT COUNT(*) AS chunks FROM chunks;
SELECT product_id, name, price FROM products WHERE product_id = 'P001';
```

預期是 `course_app@localhost`、`mariadb_workshop_2026`、12 個 products、8 個 documents、16 個 chunks，P001 價格為 `800.00`。這些是 Python 程式的驗證基準，不是要背的 Python 語法。

## 2. 執行環境與私人設定

教師已在 VM 準備課程虛擬環境與私人設定檔。不要把設定檔內容貼給 Agent、寫進 Git 或交件；只檢查權限：

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
stat -c '%a %n' "$HOME/mariadb-course-app.json"
```

預期權限是 `600`。若環境尚未準備好，先回報錯誤，不要把密碼硬寫進 Python。

## 3. Code section：完成最小唯讀查詢

下面是本章唯一需要完成的 code section。它把前面的 SQL 查詢包成 Python 輸出；`TODO` 是 Workshop 要完成的地方。

```python
from contextlib import closing
from course_db import connect

# Workshop：請完成兩個 TODO，再執行本檔案。
with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        # TODO 1：執行身分與交易設定查詢，並把結果存到 identity。
        # 提示：SQL 是 SELECT DATABASE(), CURRENT_USER(), @@autocommit
        identity = None

        # TODO 2：查詢 P001 的 product_id、name、price，並把結果存到 product。
        # 提示：使用 ? 參數與 ("P001",) tuple，不要拼接 SQL。
        product = None

        print(identity)
        print(product)
```

這段程式的重點與 Ch5～9 相同：`SELECT` 不修改資料；`?` 是參數位置；`("P001",)` 是傳給查詢的值；`closing` 讓已建立的 cursor 與 connection 在離開區塊時關閉。

執行檔案時，在 repo 根目錄使用：

```bash
PYTHONPATH=. python3 workshop/10-connection.py
```

Workshop 提供的是待完成版本；若想先看教師完整示範，請閱讀 `demo/10-connection.py`，不要把示範檔直接覆蓋 Workshop。

## 4. 失敗也要能解釋

若把設定檔路徑改成不存在的檔案，這不是「P001 查不到」，而是設定階段失敗。只記錄錯誤類型與退出碼，不要貼出私人設定內容：

```bash
python3 course_db.py --config /nonexistent/course-app.json check
printf 'exit=%s\n' "$?"
```

## 5. 驗證

用 MariaDB client 重新查詢，交叉確認 Python 輸出：

```sql
SELECT DATABASE(), CURRENT_USER(), @@autocommit;
SELECT product_id, name, price FROM products WHERE product_id = 'P001';
SELECT COUNT(*) FROM products;
```

通過條件：

```text
course_app@localhost
mariadb_workshop_2026
P001 price=800.00
products=12
Python 程式退出後沒有留下未關閉資源的錯誤
```

本章不做 INSERT、UPDATE、DELETE；交易控制留到 Ch12。

## 交件

- SQL 基準查詢結果。
- 完成後的 code section 與執行命令。
- Python 輸出、exit code 與 P001 回讀結果。
- 失敗設定檔測試的錯誤類型與退出碼。
- 一句話說明：Python 這段程式和 Ch5～9 的哪個 SQL 概念相同。

不要提交密碼、私人 JSON、完整 socket 路徑或其他同學的設定檔。

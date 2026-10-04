# 16 CSV 匯入品質：先拒絕整批錯誤，再原子寫入

> **定位**：先驗證整批 CSV，再決定是否寫入；壞檔 0 筆，好檔才整批提交。

## 學習目標

完成本節後，你應該能夠：

- 用 `csv.DictReader` 正確讀取逗號、引號與 UTF-8 BOM
- 分辨重複 ID、未知分類、空字串、NULL、金額與型別錯誤
- 讓整批驗證失敗時完全不寫入資料庫
- 用交易與第二條連線確認有效批次已提交
- 分辨 CSV 驗證錯誤與資料庫連線錯誤

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

本節的檔案位置：

```text
data/import-errors.csv
demo/16-import-quality.py
workshop/16-import-quality.py
course_db.py
```

---

## 情境

供應商 CSV 第一列正常，後面卻有重複 ID、未知分類與空名稱。如果工具逐列寫入，可能先留下部分資料，再因後面錯誤停止。

本節採用：

```text
先驗證整批
全部通過才 begin／INSERT／commit
任何資料庫錯誤就 rollback
```

練習 ID：

```text
P941、P945
```

正式 P001～P012 不可修改。

---

## 講解

### 1. CSV 不是用逗號 split

錯誤 CSV 範例位於：

```text
data/import-errors.csv
```

欄位固定為：

```csv
product_id,category_id,name,price,stock,status
P941,1,"O'Reilly, 教學感測器",100.00,2,active
```

名稱內有逗號，所以必須使用 CSV parser；不要使用：

```python
line.split(',')
```

`validate_csv()` 使用：

```python
csv.DictReader(..., strict=True)
```

並以：

```text
newline=""
encoding="utf-8-sig"
```

讀取，支援 UTF-8 BOM。

### 2. 空字串、NULL 與文字 NULL

本課約定：

```text
空欄／""：空字串
\N：NULL 語意
NULL：四個普通文字
```

匯入的 `name` 不接受空字串或 NULL；不會偷偷把空欄修剪或轉換。

其他規則：

```text
product_id：P9xx
category_id：必須存在
price：Decimal、非負、最多兩位小數
stock：0～4294967295 的整數
status：active 或 inactive
```

金額不要用 float 偷做四捨五入；使用 `Decimal`。

### 3. 執行壞檔驗證

公開 demo 檔案：

```text
demo/16-import-quality.py
```

執行：

```bash
cd ~/workspace/mariadb-demo
. "$HOME/mariadb-course-venv/bin/activate"
PYTHONPATH=. python demo/16-import-quality.py
```

預期：

```text
3:product_id:duplicate_id
4:category_id:unknown_category
5:name:empty_not_allowed
6:name:null_not_allowed
valid=False; individually_valid_rows=2; import entire batch forbidden
```

這表示有些列個別看起來合法，但因為整批 `valid=False`，兩列也不能先匯入。

也可以使用 CLI：

```bash
python3 course_db.py validate data/import-errors.csv
```

這是資料品質錯誤，退出碼是 2；不是 MariaDB 連線失敗。

### 4. 寫入資料庫前後的交易

共用 API 在：

```text
course_db.py → import_products()
```

有效批次流程：

```text
讀取 categories 與既有 product IDs
→ validate_csv()
→ 驗證通過
→ conn.begin()
→ 逐列參數化 create_product()
→ 全部成功才 conn.commit()
```

驗證失敗時：

```text
inserted = 0
不開始資料寫入
```

若驗證後另一條連線搶先使用 ID，資料庫 PK／FK 仍是最後防線；發生錯誤時整批 rollback，不留下前幾列。

### 5. 執行 Workshop 測試

完整 Workshop 檔案：

```text
workshop/16-import-quality.py
```

先執行不需要 MariaDB 的標準函式庫測試：

```bash
PYTHONPATH=. python workshop/16-import-quality.py
```

預期：

```text
CSV: valid batch=2; existing ID rejected; bad batch rejected
```

再執行真實資料庫測試：

```bash
PYTHONPATH=. python workshop/16-import-quality.py --database
```

預期：

```text
database: invalid batch inserted=0
database: valid batch inserted=2; second connection verified
database: repeated batch inserted=0
database: cleanup complete
```

第二條連線確認：

```text
P941 名稱保留逗號與單引號
P945 stock = 0
```

最後只清理本次新增的兩筆。

---

## Workshop

### 題目

1. 閱讀 `data/import-errors.csv`，列出四個錯誤與原因。
2. 執行 `demo/16-import-quality.py`，確認整批拒絕。
3. 執行 `workshop/16-import-quality.py`，完成標準函式庫測試。
4. 執行 `workshop/16-import-quality.py --database`，確認壞檔 0 筆、好檔 2 筆、重送 0 筆。
5. 說明為什麼 CSV parser 不能用 `split(',')`。
6. 確認清理後正式 checkpoint 沒有改變。

執行：

```bash
cd ~/workspace/mariadb-demo
. "$HOME/mariadb-course-venv/bin/activate"
PYTHONPATH=. python demo/16-import-quality.py
PYTHONPATH=. python workshop/16-import-quality.py
PYTHONPATH=. python workshop/16-import-quality.py --database
```

### 預期輸出

```text
CSV: valid batch=2; existing ID rejected; bad batch rejected
database: invalid batch inserted=0
database: valid batch inserted=2; second connection verified
database: repeated batch inserted=0
database: cleanup complete
```

### 交件

提交：

- 四個壞資料錯誤與行號
- 標準函式庫驗證結果
- 壞批次 0 筆與好批次 2 筆的證據
- 第二條連線回讀結果
- 重送結果與清理結果

不要提交密碼、私人設定檔或正式產品內容。不要用 `LOAD DATA INFILE` 取代本課 API，也不要把好批次的資料猜改成其他分類。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

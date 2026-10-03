# 12 交易：新增產品與 SOP 關聯必須一起成功

> **定位**：用 `begin`、`commit` 與 `rollback` 把多步寫入包成一次完整的業務操作。

## 學習目標

完成本節後，你應該能夠：

- 說明為什麼兩個相關寫入必須一起成功
- 使用 `begin()`、`commit()` 與 `rollback()` 控制交易
- 以外鍵失敗驗證 all-or-nothing
- 用第二條連線確認資料是真的提交或已回復
- 遵守父表／子表的刪除順序完成清理

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：教師示範與學生練習。
- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

本節使用 Ch10 的 Python 虛擬環境、自己的 `course_app` 設定檔，以及 Ch11 的參數化函式。

---

## 情境

新增一個產品後，必須立刻把它連到一份已存在的 SOP：

```text
1. 新增 products 列
2. 新增 product_documents 關聯列
```

兩步應該被視為一次業務操作：

```text
全部成功 → COMMIT
任何一步失敗 → ROLLBACK
```

否則可能留下「產品存在，但沒有 SOP」的半成品。

本節使用：

```text
成功：P912 / D001
失敗：P913 / D999
```

D001 存在；D999 不存在。練習最後會清理 P912，不修改 P001～P012。

---

## 講解

### 1. 交易邊界

交易包住兩次 DML：

```python
conn.begin()
try:
    create_product(conn, product_id, name)
    # 建立 product_documents 關聯
    conn.commit()
except BaseException:
    conn.rollback()
    raise
```

作用：

```text
begin()：開始交易
commit()：全部成功，正式保存
rollback()：任一步失敗，撤回整個交易
raise：保留原始錯誤，不假裝成功
```

不要把 `CREATE TABLE` 或 `ALTER TABLE` 混進這個交易，DDL 和 DML 的復原規則不同。

### 2. 成功案例：P912 連到 D001

在自己的 VM 執行：

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/12-transactions.py
```

成功函式呼叫的核心是：

```python
from course_db import connect, create_product_with_document

result = create_product_with_document(
    conn, "P912", "交易練習", "D001"
)
```

預期第二條連線可以看到：

```text
commit: product=1 link=1 (second connection)
```

這表示兩個資料列都已提交：

```text
products：P912
product_documents：P912 / D001
```

### 3. 失敗案例：P913 連到不存在的 D999

第二個案例使用：

```python
create_product_with_document(
    conn, "P913", "必須回復", "D999"
)
```

第一步新增 P913 可以成功，但第二步的外鍵找不到 D999，應得到：

```text
ERROR 1452
```

交易函式會：

```text
新增 P913
→ 嘗試新增 P913 / D999
→ 外鍵錯誤 1452
→ rollback
→ 重新拋出錯誤
```

第二條連線應確認：

```text
P913 不存在
P913 的 product_documents 關聯數 = 0
```

預期：

```text
second write rejected: errno=1452
rollback: product=0 link=0 (second connection)
```

這就是 all-or-nothing：第一步也不能留下來。

### 4. 為什麼要用第二條連線？

寫入交易自己的連線可能看得到尚未提交的資料。因此：

```text
同一條連線查得到 ≠ 已經 COMMIT
```

第二條連線看不到第一條連線未提交的資料，適合用來確認：

```text
成功案例：真的已提交
失敗案例：真的已回復
```

### 5. 清理成功案例

成功的 P912 已經提交，所以清理時也要明確使用交易：

```python
conn.begin()
try:
    # 先刪子表關聯
    cur.execute(
        "DELETE FROM product_documents WHERE product_id = ?",
        ("P912",),
    )
    # 再刪父表產品
    cur.execute(
        "DELETE FROM products WHERE product_id = ?",
        ("P912",),
    )
    conn.commit()
except BaseException:
    conn.rollback()
    raise
```

順序是：

```text
先刪 product_documents
再刪 products
```

不能先刪仍被外鍵參照的產品，也不要停用 `FOREIGN_KEY_CHECKS`。

最後執行：

```bash
python3 course_db.py check
```

確認正式 checkpoint 回到：

```text
products = 12
documents = 8
chunks = 16
```

---

## Workshop

### 題目

在自己的 VM 完成：

1. 確認 P912、P913 不存在，D001 存在，D999 不存在。
2. 執行成功案例 P912／D001，用第二條連線確認 product=1、link=1。
3. 執行失敗案例 P913／D999，保存 `ERROR 1452`。
4. 用第二條連線確認 P913 與它的關聯都是 0。
5. 依照外鍵順序清理 P912。
6. 執行 checkpoint，確認正式 products/documents/chunks 為 12/8/16。

執行：

```bash
PYTHONPATH=. python demo/12-transactions.py
python3 course_db.py check
```

### 預期輸出

```text
commit: product=1 link=1 (second connection)
second write rejected: errno=1452
rollback: product=0 link=0 (second connection)
cleanup: P912/P913 absent
```

Checkpoint：

```text
products = 12
documents = 8
chunks = 16
```

### 交件

提交：

- 成功案例的 commit 證據
- `ERROR 1452` 的錯誤摘要
- 失敗案例的 rollback 證據
- 第二條連線的查詢結果
- 清理後 checkpoint
- 一段說明：為什麼兩步必須 all-or-nothing

不要提交密碼或私人設定檔，不要停用外鍵檢查，也不要修改正式 P001～P012。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。

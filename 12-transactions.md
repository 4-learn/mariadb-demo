# 12 交易：相關寫入必須一起成功

> **定位**：延續 Ch5–9 的外鍵、DML 與查詢驗證，將新增產品與 SOP 關聯包成一個 transaction。完成一個 code section，觀察 commit、rollback 與第二條連線。

[上一節](11-parameterized-crud.md) · [下一節](13-errors.md)

## 學習目標

- 用 `begin()`、`commit()`、`rollback()` 表達 all-or-nothing。
- 以 `P912/D001` 成功與 `P913/D999` 外鍵失敗驗證交易邊界。
- 用第二條連線確認提交或回復，而非只看寫入連線。
- 依外鍵順序清理子表再清理父表。

## 1. 先確認基準

```sql
SELECT document_id FROM documents WHERE document_id IN ('D001','D999');
SELECT product_id FROM products WHERE product_id IN ('P912','P913');
```

預期 D001 存在、D999 不存在，P912/P913 未被使用。交易內的兩次 DML 都應使用 Ch11 的參數化寫法；不要把 DDL 混入交易。

## 2. Code section：成功與失敗案例

```python
from contextlib import closing
import mariadb
from course_db import connect

with closing(connect()) as conn:
    # TODO 1：開始交易，參數化 INSERT P912 與 product_documents(P912,D001)。
    # 兩步都成功才 commit；任一步例外都 rollback 後重新 raise。
    pass

    # TODO 2：用同樣的交易邊界嘗試 P913/D999。
    # 捕捉並記錄 mariadb.IntegrityError errno=1452；確認第二條連線看不到 P913。
    pass

    # TODO 3：用交易清理 P912：先 DELETE product_documents，再 DELETE products，然後 commit。
```

完整示範 `demo/12-transactions.py` 顯示第二條連線查詢與清理順序；可對照其 `create_product_with_document()`，但保留本節的邊界：成功全提交、失敗全回復。

## 3. 執行與驗證

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/12-transactions.py
python3 course_db.py check
```

通過條件：

```text
commit: product=1 link=1 (second connection)
second write rejected: errno=1452
rollback: product=0 link=0 (second connection)
cleanup: P912/P913 absent
products=12、documents=8、chunks=16
```

第二條連線的觀察才是提交／回復證據；同一條連線看得到資料不代表已 commit。

## 4. 交件

提交 code section、兩個案例的 exit code、commit/rollback 輸出、第二條連線結果、清理結果與 checkpoint。不要停用外鍵檢查、提交密碼或修改 P001–P012。

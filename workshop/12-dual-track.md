# Ch12 Workshop：交易邊界

延續 Ch5–9 的外鍵與 DML。成功案例是 `P912/D001`，失敗案例是 `P913/D999`；成功後必須清理 P912。

## 共同 code section

請自行完成 TODO，或使用下方 Agent completion。兩條路線執行同一個 code section，並以第二條連線驗證。

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

## 自行完成或 Agent completion

- **自行完成**：實作 `begin`、兩次參數化 DML、`commit`／`rollback`，再查詢驗證。
- **Agent completion**：可貼上這段安全短 prompt：

```text
只修改這個 code section 的 TODO。使用 ? 參數；P912/D001 必須全成功才 commit，P913/D999 必須捕捉 errno=1452 並 rollback。清理時先刪 product_documents 再刪 products；不可停用外鍵或修改 P001–P012。列出 diff、執行結果與第二條連線證據，不要輸出秘密。
```

## 執行與驗證

```bash
. "$HOME/mariadb-course-venv/bin/activate"
cd ~/workspace/mariadb-demo
PYTHONPATH=. python demo/12-transactions.py
python3 course_db.py check
```

預期成功為 `product=1 link=1`，失敗為 `errno=1452` 且第二條連線看到 `product=0 link=0`；清理後 P912/P913 不存在，checkpoint 為 products/documents/chunks = 12/8/16。交件包含輸出、exit code 與清理證據。

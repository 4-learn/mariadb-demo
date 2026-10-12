# 21 篩選與評估 Workshop

## 概念
先用產品、分類和有效狀態篩出合格資料，再用 qrels 評估搜尋結果是否找對。

## 完整程式 `/tmp/ch21_eval.py`
```python
import os
from pathlib import Path
from embedding_course import load_artifact
from course_db import connect
from vector_course import recorded_query, search, evaluate
a=load_artifact(Path(os.environ.get("VECTOR_ARTIFACT",str(Path.home()/"mariadb-vectors.json"))))
with connect() as conn:
 for q in ("Q01","Q08"):
  case,v=recorded_query(a,q)
  rows=search(conn,v,k=3,category_id=case["category_id"],mode="exact")
  print(q,[r["chunk_id"] for r in rows])
 print(evaluate(conn,a,k=3))
```

## Baseline reset（必要時由教師確認）

若 `evaluate()` 回報 `documents differ from artifact baseline`，先由教師確認這是課程合成資料庫，再執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/21-reset-baseline.sql
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python \
  vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"
```

reset 不 DROP table、不需要 root、不列印秘密；Agent 不得自行猜測設定檔或重置資料。

## Agent prompt
> 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，將完整程式原樣寫入並執行 `/tmp/ch21_eval.py`；不得 placeholders、由排名反推 qrels、改分類或讀 HackMD/repos。回報 stdout、stderr 與實際 exit code；若資料庫不是 artifact baseline，保留真實錯誤。

```bash
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch21_eval.py; rc=$?; echo "exit_code=$rc"
python vector_course.py evaluate --artifact "$HOME/mariadb-vectors.json" --k 3; rc=$?; echo "evaluate_exit_code=$rc"
mariadb mariadb_workshop_2026 -e "SELECT COUNT(*) FROM chunks c JOIN documents d ON d.document_id=c.document_id WHERE d.status='active' AND EXISTS (SELECT 1 FROM product_documents pd JOIN products p ON p.product_id=pd.product_id WHERE pd.document_id=d.document_id AND p.status='active' AND p.category_id=999);"
```
記錄 category 1 集合、Q01/Q08、八題結果、空 qrels 的 NULL precision/recall 與所有退出碼。

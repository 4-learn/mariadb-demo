# 21 篩選與評估：相似段落不等於可用答案

> **概念**：先用 `EXISTS` 形成唯一合格集合（文件 active、產品 active、分類符合），再用獨立人工 qrels 評估。相似度不能取代型號、否定與安全規則。

[上一節](20-ann.md) · [下一節](22-consistency.md)

## 1. SQL 合格集合

```sql
SET @category=1;
SELECT c.chunk_id,c.document_id
FROM chunks c JOIN documents d ON d.document_id=c.document_id
WHERE d.status='active' AND EXISTS (
 SELECT 1 FROM product_documents pd JOIN products p ON p.product_id=pd.product_id
 WHERE pd.document_id=d.document_id AND p.status='active' AND (@category IS NULL OR p.category_id=@category)
) ORDER BY c.chunk_id;
```

分類 1 預期十個唯一 chunk；category 999 應零列。

## 2. 完整可執行 code section

```python
import os
from pathlib import Path
from embedding_course import load_artifact, recorded_query
from course_db import connect
from vector_course import search, evaluate

artifact = load_artifact(Path(os.environ.get("VECTOR_ARTIFACT", str(Path.home()/"mariadb-vectors.json"))))
for case_id in ("Q01", "Q08"):
    case, vector = recorded_query(artifact, case_id)
    with connect() as conn:
        rows = search(conn, vector, k=3, category_id=case["category_id"], mode="exact")
    print(case_id, [r["chunk_id"] for r in rows])
print(evaluate(artifact, k=3))
```

## 3. 固定 Agent prompt

> 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，把完整程式寫到 `/tmp/ch21_eval.py` 後執行；不得 placeholders、由排名反推 qrels、改 category 或讀 HackMD/repos。回報實際輸出與 exit code。

## 4. 執行與驗收

```bash
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch21_eval.py; rc=$?; echo "exit_code=$rc"
python vector_course.py evaluate --artifact "$HOME/mariadb-vectors.json" --k 3; rc=$?; echo "exit_code=$rc"
```

```sql
SELECT COUNT(*) AS eligible_category_999 FROM chunks c JOIN documents d ON d.document_id=c.document_id
WHERE d.status='active' AND EXISTS (SELECT 1 FROM product_documents pd JOIN products p ON p.product_id=pd.product_id WHERE pd.document_id=d.document_id AND p.status='active' AND p.category_id=999);
```

Q03 relevant 可為空、Q04 可含 C003/C004；R 空時 precision／recall 為 NULL，另記 returned_on_no_answer。交件附 SQL、Q01/Q08 IDs、八題實際結果、退出碼與一個計算。

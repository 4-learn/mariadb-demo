# 21 篩選與評估：相似段落不等於可用答案

> **概念**：先用產品、分類和有效狀態篩出合格資料，再用 qrels 評估搜尋結果是否找對。

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

### SQL 欄位怎麼看？

| 欄位 | 簡單說明 | 預期 |
|---|---|---|
| `category_id` | 產品分類條件 | 依問題而定 |
| `eligible_category_999` | 分類 999 的合格資料數 | `0` |
| `exact_ids` | 條件篩選後的片段 | 依 Q01/Q08 實際輸出 |
| `precision_at_k` / `recall_at_k` | 搜尋結果命中 qrels 的比例 | 依八題計算 |
| `returned_on_no_answer` | 沒有答案時仍回傳幾筆 | 如實記錄 |

## 2. 完整可執行 code section

```python
import os
from pathlib import Path
from embedding_course import load_artifact
from course_db import connect
from vector_course import recorded_query, search, evaluate

artifact = load_artifact(Path(os.environ.get("VECTOR_ARTIFACT", str(Path.home()/"mariadb-vectors.json"))))
with connect() as conn:
    for case_id in ("Q01", "Q08"):
        case, vector = recorded_query(artifact, case_id)
        rows = search(conn, vector, k=3, category_id=case["category_id"], mode="exact")
        print(case_id, [r["chunk_id"] for r in rows])
    print(evaluate(conn, artifact, k=3))
```

### 重要片段怎麼看？

| 程式片段 | 這一章要理解什麼 |
|---|---|
| `for case_id in ("Q01", "Q08")` | 依序測試兩個已記錄的問題，不需要先學會建立查詢。 |
| `case["category_id"]` | 取得該問題允許搜尋的產品分類條件。 |
| `search(..., category_id=...)` | 先套用分類與有效狀態條件，再做 exact 搜尋。 |
| `evaluate(conn, artifact, k=3)` | 用 artifact 裡的人工 qrels，比對搜尋結果是否找對。 |
| `precision_at_k` / `recall_at_k` | 分別看 Top-K 命中比例與找回相關答案的比例。 |

## 3. 固定 Agent prompt

> 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，把完整程式原樣寫到 `/tmp/ch21_eval.py` 後執行；不得 placeholders、由排名反推 qrels、改 category 或讀 HackMD/repos。回報實際輸出、stderr 與 exit code；若資料庫不是 artifact baseline，保留真實錯誤。

## 4. 回到 artifact baseline（需要時）

如果 `evaluate()` 回報 `documents differ from artifact baseline`，先確認你要重置的是這個合成課程資料庫。不要讓 Agent 猜測或讀密碼；由教師確認後，使用已存在的 `course_editor.cnf` 執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/21-reset-baseline.sql

PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python \
  vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"
```

這個 reset 只重建 `documents`、`product_documents`、`chunks`、`course_meta` 與 `chunk_vectors` 的課程合成資料，不會 DROP table、不需要 root、不會列印秘密。完成後再執行本節 code 與 `evaluate`。

## 5. 執行與驗收

```bash
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch21_eval.py; rc=$?; echo "exit_code=$rc"
python vector_course.py evaluate --artifact "$HOME/mariadb-vectors.json" --k 3; rc=$?; echo "exit_code=$rc"
```

```sql
SELECT COUNT(*) AS eligible_category_999 FROM chunks c JOIN documents d ON d.document_id=c.document_id
WHERE d.status='active' AND EXISTS (SELECT 1 FROM product_documents pd JOIN products p ON p.product_id=pd.product_id WHERE pd.document_id=d.document_id AND p.status='active' AND p.category_id=999);
```

### Workshop Output 怎麼看？

| Output | 代表什麼 | 通過／判讀方式 |
|---|---|---|
| `exit_code` | 完整 Python 篩選與評估程式是否成功 | `0` |
| `evaluate_exit_code` | qrels 評估是否成功 | `0` |
| `category_id` | 本次搜尋使用的資料範圍 | 由測試案例提供；不是評估結果 |
| `exact_ids` | exact 搜尋找出的 Top-K 候選 | 只在合格資料中搜尋 |
| `relevant_ids` | 人工 qrels 定義的相關片段 | 用來核對搜尋結果 |
| `precision_at_k` | Top-K 中有多少筆真的相關 | `no_answer=True` 時為 `NULL` |
| `recall_at_k` | 找回多少相關答案 | `no_answer=True` 時為 `NULL` |
| `returned_on_no_answer` | 明知沒有答案時仍回傳幾筆 | 應如實記錄，不能假裝找到答案 |
| `ann_overlap_with_exact` | ANN 與 exact 結果的重疊比例 | 本次結果，不代表普遍準確率 |

成功不是只看 `exit_code=0`；還要保留 Q01～Q08 的實際結果、空 qrels 行為與 SQL 篩選結果。

Q03 relevant 可為空、Q04 可含 C003/C004；R 空時 precision／recall 為 NULL，另記 returned_on_no_answer。交件附 SQL、Q01/Q08 IDs、八題實際結果、退出碼與一個計算。

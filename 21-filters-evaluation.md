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
| `exit_code` | Linux 執行 Python 後回報的結果。`0` 代表程式跑完，非 `0` 代表中途發生錯誤。 | 先確認是 `0`；若不是，先看 stderr 的真實錯誤，不要直接說搜尋失敗原因。 |
| `evaluate_exit_code` | `vector_course.py evaluate` 命令的結果；它把八個問題的搜尋結果，和 artifact 裡預先準備的人工答案逐一比較。 | `0` 代表評估程式完成；仍要閱讀每題結果，不能只看這個數字。 |
| `category_id` | 資料表中的分類編號。搜尋時只看這個分類和 active 文件中的 chunks；它是「去哪裡找」的條件，不是答案。 | 確認和測試問題設定一致；不要自行改分類。 |
| `exact_ids` | exact 搜尋挑出的 chunk 編號，例如 `C004`、`C003`。這些是資料庫找出的候選文字片段，不是已寫好的回答。 | 確認結果來自指定 category 的 active 資料，並保留實際順序。 |
| `relevant_ids` | 人類事先判定「和這個問題有關」的 chunk 編號，也就是這題的參考答案清單。 | 只用來和 `exact_ids` 比較；不可從搜尋排名倒推或修改它。 |
| `precision_at_k` | 找出的前 K 筆中，有幾筆真的在 `relevant_ids` 裡。例：找 3 筆，2 筆相關，就是 `2/3`。 | 有答案的題目才計算；數字越高表示前 K 筆混入的無關片段越少。 |
| `recall_at_k` | 人類標記的相關片段中，前 K 筆找回了幾筆。例：有 2 筆相關、找回 1 筆，就是 `1/2`。 | 有答案的題目才計算；數字越高表示漏掉的相關片段越少。 |
| `returned_on_no_answer` | 人類答案清單是空的時，搜尋仍回傳了幾筆候選；用來檢查會不會把「沒有答案」誤當成有答案。 | 如實記錄；不能因為文字相似就宣稱找到了答案。 |
| `ann_overlap_with_exact` | ANN 和 exact 找到相同 chunk 的比例。例如 exact 有 3 筆，ANN 有 2 筆相同，比例就是 `2/3`。 | 只描述這次資料與這次問題；不能據此宣稱 ANN 一定更快或永遠正確。 |

成功不是只看 `exit_code=0`；還要保留 Q01～Q08 的實際結果、空 qrels 行為與 SQL 篩選結果。

Q03 relevant 可為空、Q04 可含 C003/C004；R 空時 precision／recall 為 NULL，另記 returned_on_no_answer。交件附 SQL、Q01/Q08 IDs、八題實際結果、退出碼與一個計算。

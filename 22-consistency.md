# 22 原文與向量一致性：整份文件一起更新

> **概念**：文件更新時，必須在同一個交易中同步更新原文、版本、hash 與向量，確保它們不會互相不一致。

[上一節](21-filters-evaluation.md) · [下一節](23-integration.md)

## 1. SQL before snapshot

```sql
SELECT d.document_id,d.source_version,c.chunk_id,c.source_version AS chunk_version,
 v.source_version AS vector_version,SHA2(c.text,256)=c.content_hash AS text_ok
FROM documents d JOIN chunks c USING (document_id) LEFT JOIN chunk_vectors v USING (chunk_id)
WHERE d.document_id='D001' ORDER BY c.chunk_id;
```

乾淨起點是 D001/C001/C002 與 vectors 全版本 1；不要在其他 checkpoint 注入故障。

### SQL 欄位怎麼看？

| 欄位 | 簡單說明 | 預期 |
|---|---|---|
| `source_version` | 原文或向量目前版本 | 成功後 D001 為 `2` |
| `chunk_id` | 被更新的文字片段 | `C001`、`C002` |
| `vector_version` | 向量版本 | 和原文版本相同 |
| `text_ok` | 原文 hash 是否正確 | `1` |

故障 rollback 後，before 和 after 應該一樣；成功更新後，三種版本才一起變成 `2`。

## 2. 完整可執行 code section

```python
import os
from pathlib import Path
from embedding_course import load_artifact
from course_db import connect
from vector_course import update_document

artifact = load_artifact(Path(os.environ.get("VECTOR_ARTIFACT", str(Path.home()/"mariadb-vectors.json"))))
texts = {c["chunk_id"]: c["text"] for c in artifact["updates"]["D001"]["chunks"]}
with connect() as conn:
    result = update_document(conn, "D001", 1, texts, prepared=artifact)
    print(result)
    conn.commit()
```

### 重要片段怎麼看？

| 程式片段 | 這一章要理解什麼 |
|---|---|
| `texts = {...}` | 從 artifact 取出 D001 的完整兩段新文字，確保文件不是只更新一半。 |
| `expected_version=1` | 只允許在「我預期目前是版本 1」時更新；版本不符就拒絕。 |
| `prepared=artifact` | 使用已驗證的向量與文字資料，避免拿不相符的向量更新。 |
| `update_document(...)` | 在交易內鎖定、重查版本，並同步更新文字、hash、向量與版本。 |
| `conn.commit()` | 確認整批更新成功後才提交；中途錯誤則由程式 rollback。 |

## 3. 固定 Agent prompt

> 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"`，完成下列 Ch22 完整驗證；不得 placeholders、忽略版本衝突或讀 HackMD/repos。先用 `demo/21-reset-baseline.sql` 將課程合成資料庫恢復到 artifact baseline，再取得 before snapshot。先測 CLI 的故障 rollback、正常更新與 stale 拒絕；最後再次 reset baseline，才把完整 code section 原樣寫入 `/tmp/ch22_consistency.py` 並執行。每一步回報實際命令、stdout、stderr 與 exit code；不把例外當成功，不要自行修改資料庫來掩蓋錯誤。

## 4. 執行、快照與驗收

CLI scenario 與完整 code section 必須各自從 version 1 baseline 開始，不能讓前一個成功更新消耗下一個 scenario 的 expected version：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/21-reset-baseline.sql
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"
# before snapshot
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --document D001 --expected-version 1 --fail-after-first; rc=$?; echo "failure_exit_code=$rc"
# after-failure snapshot
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --document D001 --expected-version 1; rc=$?; echo "success_exit_code=$rc"
# version 2 is now expected; this stale request must fail
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --document D001 --expected-version 1; rc=$?; echo "stale_exit_code=$rc"
# reset again before running the standalone code section
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/21-reset-baseline.sql
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch22_consistency.py; rc=$?; echo "code_exit_code=$rc"
```

```sql
SELECT d.source_version,c.chunk_id,c.source_version,v.source_version,SHA2(c.text,256)=c.content_hash AS text_ok
FROM documents d JOIN chunks c USING(document_id) JOIN chunk_vectors v USING(chunk_id)
WHERE d.document_id='D001' ORDER BY c.chunk_id;
```

故障 exit 非零且 before==after；成功後所有版本 2；stale 為 `VersionConflict` 且快照不變。交件附四組 SQL 快照、完整 code、命令及實際 exit code。

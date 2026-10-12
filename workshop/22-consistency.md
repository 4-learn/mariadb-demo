# 22 一致性 Workshop

## 概念
向量先在交易外計算；交易內鎖文件並重查 expected_version，再完整更新文字/hash/vector。故障 rollback，stale 拒絕。

## 完整程式 `/tmp/ch22_consistency.py`
```python
import os
from pathlib import Path
from embedding_course import load_artifact
from course_db import connect
from vector_course import update_document
a=load_artifact(Path(os.environ.get("VECTOR_ARTIFACT",str(Path.home()/"mariadb-vectors.json"))))
texts={c["chunk_id"]:c["text"] for c in a["updates"]["D001"]["chunks"]}
with connect() as conn:
 result=update_document(conn,"D001",1,texts,prepared=a); print(result); conn.commit()
```

## Agent prompt
> 使用 `/home/yillkid/mariadb-course-venv/bin/python`、`PYTHONPATH="$PWD"` 完成 Ch22 完整驗證；不得 placeholders、忽略版本衝突或讀 HackMD/repos。先用 `demo/21-reset-baseline.sql` 恢復 artifact baseline，再測 CLI 的 failure rollback、success、stale；最後再次 reset baseline，才執行 `/tmp/ch22_consistency.py`。每一步回報 stdout、stderr 與實際 exit code；保留真實錯誤。

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/21-reset-baseline.sql
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --document D001 --expected-version 1 --fail-after-first; rc=$?; echo "failure_exit_code=$rc"
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --document D001 --expected-version 1; rc=$?; echo "success_exit_code=$rc"
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --document D001 --expected-version 1; rc=$?; echo "stale_exit_code=$rc"
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/21-reset-baseline.sql
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python vector_course.py ingest --artifact "$HOME/mariadb-vectors.json"
PYTHONPATH="$PWD" /home/yillkid/mariadb-course-venv/bin/python /tmp/ch22_consistency.py; rc=$?; echo "code_exit_code=$rc"
```

```sql
SELECT d.source_version,c.chunk_id,c.source_version,v.source_version,SHA2(c.text,256)=c.content_hash AS text_ok
FROM documents d JOIN chunks c USING(document_id) JOIN chunk_vectors v USING(chunk_id)
WHERE d.document_id='D001' ORDER BY c.chunk_id;
```
故障非零且 before=after；成功版本 2；stale `VersionConflict` 且 snapshot 不變。交付四組 SQL 快照與實際退出碼。

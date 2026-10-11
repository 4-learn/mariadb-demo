# 22 一致性 Workshop

## 任務

在隔離的版本 1 checkpoint 使用主課同一 code section。可自行補 TODO，或請 Agent 補 TODO；不要提供私人設定檔，執行與 SQL 快照由你完成。

```python
from pathlib import Path
from course_db import connect
from embedding_course import load_artifact
from vector_course import update_document

artifact = load_artifact(Path.home() / "mariadb-vectors.json")
texts = {c["chunk_id"]: c["text"] for c in artifact["updates"]["D001"]["chunks"]}
# TODO 1：在乾淨版本 1 checkpoint 呼叫一次更新。
result = None
# TODO 2：印出結果，保留 document 與兩個 chunk 的版本。
print(result)
```

## 執行與驗收

1. 保存 before SQL 快照。
2. `update ... --fail-after-first` 應非零；after 必須與 before 的文字、hash、vector bytes、版本完全相同。
3. 用 code section 或 CLI 成功更新；D001/C001/C002/vectors 全為版本 2。
4. 再用 expected_version=1 重送，得到 `VersionConflict`，快照不變。

只有印出例外不算 rollback 證據；若錯誤發生在連線或 artifact 載入，也不算「寫入後故障」。`FOR UPDATE` 後重新檢查版本才是 stale 防護核心。

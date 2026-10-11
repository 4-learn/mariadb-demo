# 22 原文與向量一致性：整份文件一起更新

> **定位**：把 Ch5–7 的 UPDATE、交易、rollback 與版本條件套到文件／chunk／vector；Python 只協助執行，SQL 快照才是驗證證據。

[上一節](21-filters-evaluation.md) · [下一節](23-integration.md)

## 學習目標

- 找出文字、hash、向量、文件版本不同步的風險。
- 在短交易中 `SELECT ... FOR UPDATE` 並檢查 expected_version。
- 證明故障完整 rollback、成功完整提交、stale 更新拒絕。

## 1. 先用 SQL 保存 checkpoint

```sql
SELECT d.document_id,d.source_version,c.chunk_id,c.source_version AS chunk_version,
       v.source_version AS vector_version,
       SHA2(c.text,256)=c.content_hash AS text_ok
FROM documents d JOIN chunks c USING (document_id)
LEFT JOIN chunk_vectors v USING (chunk_id)
WHERE d.document_id='D001' ORDER BY c.chunk_id;
```

乾淨起點為 D001/C001/C002 與 vectors 全版本 1。不要在已更新到版本 2 的資料上重跑故障注入。

## 2. 交易規則

向量先在交易外計算；交易開始後鎖 document，核對目前版本仍等於 expected_version，再鎖定恰好兩段，更新兩段 text/hash/vector 與 document version，成功才 commit。任何錯誤 rollback。`autocommit=True` 不會把多句 SQL 自動變成一個交易。

## 3. Code section：完成安全更新呼叫（Python 可選）

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

提示：`update_document(conn, 'D001', 1, texts, prepared=artifact)`；故障注入與 stale 重送使用 CLI，不把例外當成功。

## 4. 執行、驗證、交付

先執行 `--fail-after-first`，預期非零；用同一 SQL 快照確認所有文字、hash、vector bytes、版本仍與 before 完全相同。再成功更新，所有版本變 2；以 expected_version=1 重送，必須 `VersionConflict` 且快照不變。成功後舊版 qrels 不可直接當新版 baseline。

## 交件

交付 before／failure／success／stale 四組 SQL 快照、code section、命令與退出碼，並解釋為何鎖內重查版本能防止舊頁面覆蓋新版。不要在共享或非 v1 checkpoint 做故障注入。

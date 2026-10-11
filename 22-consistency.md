# 22 原文與向量一致性：兩段文件一起更新

> 本章完全使用 MariaDB client 與 SQL，使用教師預計算的 D001 v2 向量，練習交易、版本檢查與一致性驗證；不執行 Python。

## 1. 一致性條件

同一 document 的兩個 chunks 與各自 vectors 必須具有相同 `source_version`；chunk 的 `content_hash=SHA2(text,256)`，vector 的 `content_hash` 必須相同。

## 2. 先保存版本，再執行更新

確認目前是版本 1：

```sql
SELECT document_id, source_version
FROM documents WHERE document_id='D001';
```

`demo/22-consistency-sql.sql` 會在交易內鎖定文件，更新 C001、C002 的文字、hash、向量與版本，最後更新 D001 並提交。

執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/22-consistency-sql.sql
```

最後的 SELECT 應顯示 D001、C001、C002 版本一致，且 `text_hash_ok=1`、`vector_hash_ok=1`。

## 3. 為什麼向量是預計算的

MariaDB SQL 不會執行 embedding 模型。本章使用教師課前針對 D001 v2 產生的真實向量 fixture；不拿舊向量冒充新文字，也不在課堂臨時產生向量。

## Workshop

1. 在版本 1 checkpoint 執行 `demo/22-consistency-sql.sql`。
2. 保存更新前後 D001、C001、C002 的版本與 hash。
3. 確認兩個 chunks 與兩個 vectors 都是版本 2。
4. 說明為什麼只更新文字、不更新向量會造成錯誤。
5. stale 版本與故障 rollback 的完整演示需由教師使用獨立 reset checkpoint 示範；學生不在已更新的版本 2 上重跑版本 1 fixture。

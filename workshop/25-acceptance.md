# 25 增量驗收 Workshop

## 情境

你要將 17～23 的工具交給下一位同學，對方應能重現成功與故意失敗，而不是只相信「我測過」。

### 專案背景

使用教師另備 fresh v1 workshop；向量已入庫。完成腳本後原文恢復，D001 版本留下 3，其他文件仍 1。

### 使用者需求

> 「我要看到沒有混模型、不會半份更新、舊版本不能覆蓋，以及還原真的包含向量。」

### 你的任務

1.確認 checkpoint執行整理證據。
2. 附 exact／ANN 實際計畫及八題結果，未測的項目明示未測。
3. 檢查最終狀態，不能把原文復原描述成版本倒退。

### 技術需求

- 以 app 權限執行；不建表、不 DROP、不授權。
- artifact 源 hash／revision 固定；case filter／k 留在報告。
- 原文／hash／vector bytes 全部前後比對。

## 輸入資料格式

```bash
python demo/25-acceptance.py --artifact "$HOME/mariadb-vectors.json"
```

若私人檔不在預設位置，附 `--config "$HOME/mariadb-course-app.json"`，不附其內容。

## 輸出示例

```text
checks: 實際通過的檢查清單
plans: exact，索引存在時另有 ann
evaluation: 八題實際結果
final_document_version: 3
```

不是預填通過清單；任何 assert 失敗都須保留原因，不繼續改資料湊結果。

## 你需要實作的功能

交付一份文字報告，包含環境版本、source_hash、模型 revision、case／k／category、實際計畫、回滾快照相同、stale 拒絕、成功 v2 及復原 v3。

### 提示

若途中已成功提交 v2，再發生其他錯誤，資料不一定自動回 v1。先查看現在版本與 check，請教師決定後續；不要直接重跑整套。

## 解答

合理的結論格式如下，每行用實際證據填寫，不複製成假成果：

```text
環境：server 與 Connector 的實際版本
來源：artifact.source_hash / model_revision
完整性：維度、metadata、來源誤改均被指定檢查拒絕
資格：category1 十個唯一 chunk，category999 空
精確：plan 未選 vector_idx
ANN：plan 選 vector_idx，或明示 ANN NOT TESTED
品質：八題實際結果；Q03/Q05 的限制說明
交易：注入失敗 before==after；成功 v2；stale after 不變
還原：文字/hash/vector bytes 回到原始，D001 版本 3
未驗證：VM 真實安裝、效能、教師真人覆核等依實際列出
```

為何 v3 正確？source_version 描述提交序列，不是內容指紋。原文相同用 content_hash 表示；兩次更新仍要留下不同版本以拒絕過期編輯。這也是 baseline qrels 在復原後仍須重新確認的原因。


## Agent 操作與驗證

請先要求 Agent 說明命令與預期變更，確認後才執行；完成後自行核對 exit code、實際輸出與資料庫證據。

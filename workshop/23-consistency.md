# 23 一致性 Workshop

## 情境

你正在修改 D001，另一位同學也可能同時提交。必須避免半份文件及舊編輯覆蓋新內容。

### 專案背景

初始 D001／C001／C002 及 vectors 全為版本 1。artifact 已含两段新版原文及真實向量，生成在交易外完成。

### 使用者需求

> 「整份一起更新；寫到一半失敗就全部不要變。別人的新版不能被我的舊頁面蓋掉。」

### 你的任務

1.保存快照失敗及成功 stale 拒絕。
2. 證明錯誤發生在第一段及向量寫入後，不是連線階段。
3. 比對兩段／文件／向量版本與原文 hash。

### 技術需求

- `update_document` 持有短交易、document FOR UPDATE 與 expected_version 核對。
- 兩段完整 texts mapping，不能只傳 C001。
- 不在別人正在用的 checkpoint 跑故障注入。

## 輸入資料格式

```python
texts = {c["chunk_id"]: c["text"] for c in artifact["updates"]["D001"]["chunks"]}
expected_version = 1
```

此處 artifact 由 `load_artifact(Path.home() / 'mariadb-vectors.json')` 驗證載入，不能任意手填向量。

## 輸出示例

```text
injected failure: 所有資料仍與 before 完全相同
success: D001、C001、C002、兩 vectors 皆 v2
stale v1: VersionConflict，after 快照不變
```

## 你需要實作的功能

```bash
python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --expected-version 1 --fail-after-first
python vector_course.py check
python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --expected-version 1
python vector_course.py update --artifact "$HOME/mariadb-vectors.json" --expected-version 1
```

逐句執行；第一與最後一句故意非零退出。每次用 demo/23-consistency.sql 核對，完整 bytes 快照可參考 demo/25-acceptance.py。

### 提示

課程 demo/24 腳本需要 fresh v1，不能在本練習結束的 v2 上再跑。若需還原原文，以 expected_version=2 更新回原文，版本增加到 3。

## 解答

核心不是「先查一下版本」，而是**取得 document 鎖後**比對目前版本。第一位編輯者提交 v2 後，第二位帶 v1 的人取得鎖時讀到 2，拋 VersionConflict，rollback，不能再次寫入。

encode 在鎖外完成，避免把下載或 CPU 耗時放進短交易。這代表可能白算一份向量，但不能犧牲資料正確性來避免白算。

只更改 C001 會被完整 chunk ID 集合檢查拒絕。把 C002 的版本留 1，或向量 source_version 留 1，都會破壞 `check`。失敗前後必須比較完整快照；只有最後 `check=true` 也可能漏掉「整份都被錯誤換過」的情況。


## Agent 操作與驗證

請先要求 Agent 說明命令與預期變更，確認後才執行；完成後自行核對 exit code、實際輸出與資料庫證據。

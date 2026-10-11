# 17 在 Ubuntu 使用 OpenCode CLI：讓 Agent 協助執行與驗證

> **定位**：本章不是 Python 語法課，而是學習在 Ubuntu 安全使用 OpenCode CLI，讓 Agent 讀程式、執行命令、解釋輸出；學生仍必須自己驗證結果。

[上一節](16-import-quality.md) · [下一節](18-embedding.md)

## 學習目標

- 在 Ubuntu VM 安裝並啟動 OpenCode CLI。
- 要求 Agent 先說明命令，再執行安全的課程測試。
- 讀懂 exit code、錯誤訊息與預期輸出。
- 分辨 Agent 說成功和自己有證據證明成功。

## 安裝與啟動

```bash
uname -a
lsb_release -a
node --version
npm --version
opencode --version
cd ~/workspace/mariadb-demo
opencode
```

若缺少 Node.js／npm，依教師指定的官方方式安裝；不要執行不明來源的安裝腳本。

## 第一個 Agent 任務

請貼給 Agent：

```text
請閱讀 demo/16-import-quality.py，先說明它會執行什麼；不要修改檔案，不要讀取密碼或私人設定檔。確認後，再執行唯讀的標準測試，回報 exit code 與實際輸出。
```

## 安全規則

```text
先說明命令與目標資料庫
先取得同意，再執行
不讀取密碼檔、token 或私人設定檔
不執行 DROP、PURGE、rm -rf
不修改正式 products
不把 Agent 摘要當成測試證據
```

涉及寫入資料庫時，要求 Agent 先列出目標 database、預計變更與驗證 SQL。

## 驗證

學生必須自行確認 exit code、預期輸出、資料庫筆數、版本、hash 或交易結果。Agent 說「成功」不算證據；命令輸出與資料庫查詢才是證據。

## Workshop

1. 確認 `opencode --version`。
2. 讓 Agent 只讀取並解釋 `demo/16-import-quality.py`，不得修改檔案。
3. 執行標準測試，記錄命令、exit code 與輸出。
4. 說明為什麼不能只相信 Agent 的完成摘要。

本章不要求學生手寫完整 Python；但要能看懂命令、辨認風險並驗證結果。

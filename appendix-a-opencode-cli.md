# 附錄 A｜OpenCode CLI（選）：讓 Agent 協助執行與驗證

> **定位**：本附錄不是 Python 語法課，而是學習在 Ubuntu 安全使用 OpenCode CLI，讓 Agent 讀程式、執行命令、解釋輸出；學生仍必須自己驗證結果。

[上一節](16-import-quality.md) · [回到 Ch17](17-embedding.md)

## 學習目標

- 在 Ubuntu VM 安裝並啟動 OpenCode CLI。
- 設定一個可用的 LLM provider，確認不是只有安裝成功。
- 要求 Agent 先說明命令，再執行安全的課程測試。
- 讀懂 exit code、錯誤訊息與預期輸出。

## 1. 環境確認

```bash
uname -a
lsb_release -a
```

本附錄的基本安裝**不需要先安裝 Node.js 或 npm**。官方安裝腳本會安裝 `opencode` 執行檔；只有選擇 npm 安裝方式時才需要 Node.js／npm。

## 2. 安裝 OpenCode CLI

在確認來源是官方網站後，使用官方安裝腳本：

```bash
curl -fsSL https://opencode.ai/install | bash
```

重新開一個 terminal，或載入 shell 設定後確認：

```bash
command -v opencode
opencode --version
```

如果仍然顯示 `command not found`，先不要執行 `sudo snap install opencode` 或自行修改 PATH；請記錄完整輸出，交由教師檢查安裝位置與 shell PATH。

### 替代安裝：npm

只有在課堂已提供 Node.js／npm 時才使用：

```bash
npm install -g opencode-ai
opencode --version
```

不要把 `node --version`、`npm --version` 當成 OpenCode 的必要前置測試。

## 3. 設定 provider

「能執行 `opencode --version`」只證明 CLI 已安裝，不代表 Agent 能回答。啟動後在 OpenCode 介面輸入：

```text
/connect
```

選擇教師指定的 provider，依畫面登入或貼上 API key。API key 只貼到 OpenCode 的認證畫面，不要貼到課堂對話、Git、講義或 terminal transcript。

若教師使用其他 provider，依教師提供的 provider 文件設定，不要猜測模型名稱或把別人的 key 拿來用。完成後在 OpenCode 內提出不涉及專案修改的問題，例如：

```text
請只回答 OK，不要讀取檔案，也不要執行命令。
```

能得到回應，才算 provider 設定完成。

## 4. 啟動課程專案

```bash
cd ~/workspace/mariadb-demo
opencode
```

第一次可輸入：

```text
請先說明目前專案目錄與你打算使用的工具；不要修改檔案，不要讀取密碼或私人設定檔。
```

本附錄不要求執行 `/init`；若教師要求建立 `AGENTS.md`，先確認檔案內容，再決定是否提交。

## 5. 第一個安全任務

請貼給 Agent：

```text
請閱讀 demo/16-import-quality.py，先說明它會執行什麼；不要修改檔案，不要讀取密碼或私人設定檔。確認後，再執行唯讀的標準測試，回報 exit code 與實際輸出。
```

## 6. 安全規則

```text
先說明命令與目標資料庫
先取得同意，再執行
不讀取密碼檔、token 或私人設定檔
不執行 DROP、PURGE、rm -rf
不修改正式 products
不把 Agent 摘要當成測試證據
```

涉及寫入資料庫時，要求 Agent 先列出目標 database、預計變更與驗證 SQL。看到不理解的命令時，先拒絕執行並請教師說明。

## 7. 驗證與故障排除

學生必須自行確認：

```text
command -v opencode 是否有路徑
opencode --version 是否成功
provider 是否真的回應
exit code、預期輸出與資料庫筆數／版本／hash 是否正確
```

常見情況：

| 輸出 | 意義 | 處理 |
| --- | --- | --- |
| `node: command not found` | 尚未安裝 Node.js；不是官方腳本安裝失敗的充分證據 | 先確認是否採用官方 install script；不要直接把 npm 當唯一解法 |
| `opencode: command not found` | 尚未安裝成功，或 PATH 尚未載入 | 重開 terminal，執行 `command -v opencode`，保留輸出交教師 |
| `opencode --version` 成功但 Agent 無回應 | CLI 在，但 provider 尚未設定或認證失敗 | 重新執行 `/connect`，不要把 API key 貼到公開地方 |
| Agent 要求危險命令 | 風險尚未被確認 | 不執行，先要求說明並請教師確認 |

Agent 說「成功」不算證據；命令輸出與資料庫查詢才是證據。

## Workshop

1. 執行 `command -v opencode` 與 `opencode --version`，記錄輸出。
2. 確認 provider 能回答一個不讀檔、不改檔的小問題。
3. 讓 Agent 只讀取並解釋 `demo/16-import-quality.py`，不得修改檔案。
4. 在確認命令後執行標準測試，記錄 exit code 與輸出。
5. 說明為什麼不能只相信 Agent 的完成摘要。

本附錄不要求學生手寫完整 Python；但要能看懂命令、辨認風險並驗證結果。

## 官方文件

- [OpenCode 官方安裝與入門](https://opencode.ai/docs/)

# 23 CLI 串接 Workshop

## 情境

同學沒有模型快取，但要演示搜尋；你需提供明確的預計算模式，而不是假裝所有問題都能處理。

### 專案背景

SQL、embedding 與連線模組已有完整實作。本練習組合它們，不增加生成式 LLM 或自行發明新的 corpus。

### 使用者需求

> 「請告訴我這次是真的算模型，還是固定題目的離線重播；原文是哪一版也要看得到。」

### 你的任務

1.固定模式 live 或離線拒絕空結果與型號檢查。
2. 用同一 app 私人設定與 socket，不在命令列提供明文密碼。
3. 比較 Q05 有候選但不適用與 Q08 零候選。

### 技術需求

- `--case` 必須帶 `--artifact`；`--query` 真實 encode，不能同時帶 artifact。
- 連線資源在 finally 關閉；預設 exact。

## 輸入資料格式

```text
固定：--artifact ~/mariadb-vectors.json --case Q01
即時：--query '教學感測器 G 上傳逾時時應先查什麼？' --offline --category 1
```

## 輸出示例

```text
query.mode: recorded-query 或 live-model
metadata: 固定模型/revision/preprocessing
rows: chunk_id/document_id/source_version/text/distance
notice: 候選不代表答案
```

## 你需要實作的功能

```bash
python demo/23-integration.py --artifact "$HOME/mariadb-vectors.json" --case Q01
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q05
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q08
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q99
```

### 提示

demo 的欄位名為 embedding_mode，完整 CLI 為 query.mode；兩者都要誠實標示。Q99 的錯誤應在 DB 查詢前發生，沒有固定題就不做 fallback。

## 解答

小型完整程式在 demo/23-integration.py：載入 artifact、找 case、connect、search、print JSON、finally close。主 CLI 還提供 live-model、filter 覆寫及 EXPLAIN。

Q05：P010 沒有 SOP 關聯，其他感測器原文不能當作 H 的專用操作。這次工具是候選檢索，不是已完成型號約束或拒答判定的問答機器。

Q08：category 999 在 SQL eligibility 階段排除全部段落，rows 應為 []。不能換成未篩選結果讓畫面看起來有內容。

Q99：必須明確 ValueError 且非零退出。live-model 缺快取也應如實失敗；學生仍可交固定八題的演示，但成果不能寫「支援任意離線問題」。

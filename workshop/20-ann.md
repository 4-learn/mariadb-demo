# 20 ANN Workshop

## 情境

你要確認新索引真的被查詢使用，並且精確對照沒有一起走近似路徑。

### 專案背景

第 19 節已有精確結果。現在建立 vector_idx，但不根據 16 段資料作效能保證。

### 使用者需求

> 「請拿兩份實際計畫證明你測的是兩條路徑，不是只換了命令列名稱。」

### 你的任務

1.建立索引保留 plan比較候選。
2. 核對距離型別 cosine、M=6、索引名 vector_idx。
3. 分開報告 ANN 與精確重合、人工語意相關性。

### 技術需求

- MariaDB 11.8.9 `ADD VECTOR INDEX ... DISTANCE=cosine`。
- exact `IGNORE INDEX`；ann `FORCE INDEX`，且實測 EXPLAIN。

## 輸入資料格式

兩條查詢使用完全相同 Q01 向量、category 1、k=3、資料版本。

## 輸出示例

```text
exact key: 不能是 vector_idx
ann key: 必須實際有 vector_idx 才可聲稱測到 ANN
overlap: 實際 |A intersect E| / |E|
```

## 你需要實作的功能

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/20-ann.sql
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode exact --explain
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q01 --mode ann --explain
python vector_course.py evaluate --artifact "$HOME/mariadb-vectors.json" --k 3
```

### 提示

hint 不等於實際計畫；ANN 內層不要加第二排序鍵破壞可用形狀。Python 的候選內 tie-break 不會找回 ANN 沒取出的同分段落。

## 解答

假設實際 E 是 `{C001,C002,C009}`、A 是 `{C001,C009,C010}`，則交集 `{C001,C009}`，相對 exact 重合率為 2/3。這只是手算練習，**不是本課模型實測結果**；自己的報告必須填實際 ID。

若某次實際 E、A 相同，只能說本次重合率 1。不能推論 ANN 永遠精確、資料放大後仍一樣、或較快。若 category 999 下 E 為空，重合率記 null，不除以零。

失敗條件：ANN plan 沒用 vector_idx 卻稱通過；exact 用了 vector_idx；兩邊 category／k 不同；用單次小資料耗時宣稱模型或索引效能。

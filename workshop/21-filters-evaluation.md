# 21 篩選與評估 Workshop

## 情境

你要讓多產品共用 SOP 的結果不重複，並區分否定資訊與肯定答案。

### 專案背景

D001 連兩個 active 產品；D003 inactive；D004 有一個 inactive 與一個 active 關聯。這些刻意安排是業務規則測試，不是需要清掉的髒資料。

### 使用者需求

> 「不要回給我停用 SOP，也不要把『不支援 5 GHz』說成支援。」

### 你的任務

1.核對集合執行八題分析失敗。
2. 保留 query／category／qrels／實際結果，不只貼平均分數。
3. 說明 Q03 和 Q04 為何含相同關鍵詞，相關集合卻不同。

### 技術需求

- 用 EXISTS 形成唯一 chunk 的合格集合。
- qrels 綁 baseline v1，教師覆核後才作正式人工作答基準。

## 輸入資料格式

```json
{"case_id":"Q08","category_id":999,"relevant_chunk_ids":[]}
```

完整 query 與 rationale 在 data/search_cases.json，不能只取 ID 忽略篩選條件。

## 輸出示例

分類 1 十列、分類 2 兩列、分類 3 兩列、999 零列；所有 case 的實際排名另保存。

## 你需要實作的功能

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026 < demo/21-filters-evaluation.sql
python vector_course.py evaluate --artifact "$HOME/mariadb-vectors.json" --k 3
python vector_course.py search --artifact "$HOME/mariadb-vectors.json" --case Q08
```

### 提示

Q05 的 P010 是文字中的產品要求，本課 category filter 不會自動解析它。回傳其他感測器候選仍可能不是適用答案。

## 解答

1. D001 的直接 JOIN 產生四列，但 EXISTS 只讓 C001／C002 各一列，因只判斷至少存在一個合格產品。
2. D004 保留，因 P007 active；D003 排除，因文件 inactive。
3. Q03 要求提供支援產品與設定，corpus 不提供，qrels 空；Q04 問限制，C003／C004 直接回答不支援。
4. Q01 若 top-3 含 C001，precision@3=1/3、recall@3=1；若沒含，兩者為 0。不要改 qrels 迎合結果。
5. Q08 的合格集合空，SQL 應零列；Q03 的 qrels 空不代表 SQL 零列，需保留 `returned_on_no_answer`。

通過條件不是八題都「滿分」，而是機制正確、結果可重算、失誤如實解釋。重複 chunk、混入 inactive、跨分類補 k 或用 distance 當百分比皆失敗。

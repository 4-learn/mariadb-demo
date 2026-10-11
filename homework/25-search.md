# 22 搜尋與一致性 Homework

> **承接**：17～22 的真實 embedding、向量儲存、精確／ANN、資格篩選與兩段交易更新。
> **目標**：在既有工具上提交可核對的八題評估，以及成功／失敗／過期更新證據，不要求從零開發大型專案。

---

## 情境

客服搜尋找到了很像的文字，但可能引用停用文件、錯的產品型號，或剛改到一半的文件。你需要證明每一個回傳候選都能追溯，更新也不會留下舊向量配新原文。

> 核心概念：問題與篩選 -> 合格集合 -> 距離排序 -> 人工判讀；編輯請求 -> 版本鎖定 -> 全部提交或全部回滾。

---

## 題目

在現有 `vector_course.py` 的基礎上，不換 corpus、不換模型、不提高 app 權限，完成一份實際執行報告及一項小型程式驗證。

### 資料格式

```python
request = {
    "document_id": "D001",
    "expected_version": 1,
    "case_id": "Q01",
    "category_id": 1,
    "k": 3,
}
```

新原文必須直接讀 artifact `updates.D001.chunks` 的兩段；任意新文字則要實際 encode。不能改現有向量數字或手填分數。

### 需要實作

1. **來源核對**：讀並驗證 artifact，記 source_hash、revision、preprocessing、維度及向量來源模式，不上傳私人設定。
2. **八題評估**：使用 data/search_cases.json，逐題記 query、filter、人工 relevant IDs、exact IDs、precision／recall；空 qrels 額外說明為何不能自動視為拒答。
3. **唯一性小驗證**：對 category 1、k=16 呼叫 search，assert 十個唯一 chunks，沒有 D003；category 999 assert 空 list。
4. **索引對照**：有索引時附兩份實際 EXPLAIN，exact 不用 vector_idx、ANN 使用；若未建立或計畫不符，明記未通過／未測，不能填猜测數字。
5. **更新證據**：保存完整快照，注入第一段寫入後失敗、成功更新兩段、stale 重送三種狀態；附 source_version 與 hash／bytes 比對。

### 處理規則

| 狀態／條件 | 行為 |
| --- | --- |
| model／revision／source hash 不符 | 拒絕，不入庫、不搜尋混合資料 |
| category 無合格資料 | 回空候選，不跨分類補滿 |
| 模型排錯或漏掉人工相關段落 | 記錄失敗，不改標註迎合排名 |
| expected_version 已過期 | 取得鎖後拒絕，資料完全不變 |
| 第一段已寫入後注入失敗 | 兩段、向量及文件全部 rollback |
| 成功更新 | 兩段與文件／向量版本同時 +1 |
| 恢復原文 | 同一交易 API，版本再 +1，不倒退 |

---

## 預期輸出

### 正常流程

```text
source_hash 與 metadata：附實際值
category1: 10 unique chunks
八題：逐題實際候選與評估，不預設全滿分
D001 成功更新：兩段、document、vectors 皆 v2
```

### 邊界情況

```text
category999: []
Q03: 原文否定 5 GHz 支援，不可輸出肯定設定步驟
Q05: P010 無 SOP，不能套用 A/B 文件
injected failure: 快照完全相同
stale expected_version=1: VersionConflict，v2 快照不變
```

提交檔案可用 `22-search-report.md` 和自己的小驗證程式；不要修改 corpus／contract、發布筆記或附密碼。教師判分看可執行判準，不以向量模型是否符合期望排名作為程式正確性的唯一條件。

---

## 解答

程式路徑見 [vector_course.py](../vector_course.py)，完整驗證参考 [24 acceptance](../demo/24-acceptance.py)。必須在 fresh v1 checkpoint 跑，不在已更新的 v2 上硬改版本。

唯一性小驗證的完整答案：

```python
from pathlib import Path
from course_db import connect
from embedding_course import load_artifact
from vector_course import recorded_query, search
a = load_artifact(Path.home() / "mariadb-vectors.json")
_, q = recorded_query(a, "Q01")
conn = connect()
try:
    rows = search(conn, q, k=16, category_id=1)
    assert len(rows) == len({r["chunk_id"] for r in rows}) == 10
    assert all(r["document_id"] != "D003" for r in rows)
    assert search(conn, q, category_id=999) == []
    print("eligibility verified")
finally:
    conn.close()
```

算例：Q06 的 relevant 集合只有 C015。若 top-3 含 C015，precision@3=1/3、recall@3=1；沒有則兩者 0。這是公式解答，不是虛構實測分數。

Q03 的相關集合空，不作除以零的 recall。即使 C003 距離很小，也只可引用「不支援」限制，不能憑相似度生成不存在的支援步驟。Q04 問的就是限制，因此 C003／C004 可以是直接相關段落。

交易證據必須是兩段文字、兩份 hash、向量 bytes、source_version 的前後比較。只貼「rollback」訊息、只測到查無表或連線失敗、只更新其中一段，均不算完成。

---

## 延伸思考

1. 為何 encode 在交易外，卻仍要在鎖內檢查版本？答：避免長鎖，但交易外版本可能過期，只有鎖內重新讀取才能拒絕競爭寫入。
2. 為何恢復原文後仍是版本 3？答：內容 hash 表示相同文字，版本表示不同提交；回退版本會讓過期編輯再次被誤接受。
3. 為何不能用這八題調一個距離閾值後宣稱通用拒答？答：案例太少且已用於觀察，需要獨立標註測試集及型號／否定檢查，模型距離也不是機率。

---

## 流程說明

```text
驗 artifact -> 驗 DB baseline -> 八題 exact / ANN / qrels 證據
                                      |
                                      v
版本 1 -> 注入失敗 -> 快照仍為版本 1
版本 1 -> 完整成功 -> 版本 2
舊版本 1 重送 ----> 拒絕，快照仍為版本 2
版本 2 -> 原文恢復 -> 版本 3（完整驗收延伸）
```

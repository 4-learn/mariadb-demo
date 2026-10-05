# 24 增量驗收：成功、失敗與還原都要有證據

> **定位**：不另造大型專案，對既有搜尋工具執行可重現的增量驗收，區分模型觀察、資料正確性與尚未驗證事項。

[上一節](23-integration.md) · [模組作業](homework/22-search.md)


## 學習目標

- 用明確輸入、執行指令及可失敗判準整理驗收。
- 保存精確／ANN 計畫與八題結果，不只保留漂亮的成功畫面。
- 證明中途失敗及舊版本不改資料，成功後能以新版本恢復原文。

## 範例程式碼

- [實際驗收腳本](demo/24-acceptance.py)、[搜尋與交易 API](vector_course.py)。
- [一致性 SQL](demo/22-consistency.sql)、[八題 qrels](data/search_cases.json)。
- [驗收紀錄解答](workshop/24-acceptance.md)。

---

## 情境

同學說「搜尋可以用了」。你要追問：輸入是什麼？有沒有排除停用文件？同一 chunk 是否重複？更新到一半斷掉會怎樣？還原是否真的還原向量，而不是只把文字改回去？這節把前面成果變成可交接的證據，不從零再寫另一套系統。

先修 checkpoint：教師提供**獨立、初始版本 1**的 workshop checkpoint，DDL 與 16 個向量已入庫；若要驗 ANN，先建立 vector_idx。不要直接拿 22 已更新的版本 2 或 3 跑腳本。備份與還原仍沿第 15 節權限流程，不增加 DROP 或自行覆蓋既有庫。

---

## 講解

### 1. 把「完成」改成可反證的條件

| 項目 | 通過條件 | 可執行失敗判準 |
| --- | --- | --- |
| Artifact | 512 維、固定 metadata、來源 hash 一致 | 改 revision／原文／維度應被拒絕 |
| 合格集合 | 分類 1 十個唯一 chunks，無 D003 | duplicate、停用文件或跨分類即失敗 |
| 精確基準 | distance/id 排序且繞過向量索引 | EXPLAIN 選 vector_idx 即失敗 |
| ANN | 真實 plan 使用 vector_idx | 只有 hint、plan 未選即不算 ANN 已驗 |
| 交易失敗 | 注入第一段寫入後，快照完全相同 | 任一 text/hash/vector byte/version 變動即失敗 |
| 交易成功 | 兩段及文件版本一起成為 2 | 只有一段更新或 mixed metadata 即失敗 |
| stale | expected_version=1 重送遭拒，快照不變 | 覆蓋版本 2 即失敗 |
| 還原 | 原文／hash／向量 bytes 恢復，版本變 3 | 只還原文字或倒退版本即失敗 |

不要用「畫面出現搜尋兩字」當作功能判準，也不要把找不到 table 的錯誤當成 rollback 通過。

### 2. 執行驗收並保留 exit status

```bash
python embedding_course.py validate --artifact "$HOME/mariadb-vectors.json"
python vector_course.py check
python demo/24-acceptance.py --artifact "$HOME/mariadb-vectors.json"
```

腳本先核對原始 baseline，再做維度／revision／source 篡改拒絕、分類與唯一性、實際 EXPLAIN、八題評估，最後才開始 D001 寫入測試。錯誤會非零退出，不用 `--force` 或忽略 exception 繼續印成功。

有 vector_idx 時，腳本要求 ANN plan 確實使用它，否則停下；沒有索引則明記 `ANN NOT TESTED`，不偽裝 ANN 通過。它沒有新建表或索引，使用 app 權限即可執行。

成功會輸出 checks、plans、evaluation 與 `final_document_version=3`。這是期待的輸出結構，實際排名與分數必須從執行結果保存，不從教材複製。課程外的 Ubuntu VM 啟動、教師發布或效能負載，不是這支測試的覆蓋範圍。

### 3. 看懂快照與還原

腳本快照包含原文、各版本、兩份 hash、model metadata 與 `HEX(v.embedding)`。用 bytes 比對能發現「看起來都叫 512 維，但數字已換掉」的變化。

```python
before = snapshot(conn)
try:
    update_document(conn, "D001", 1, texts, prepared=artifact,
                    fail_after_first=True)
except RuntimeError:
    pass
assert snapshot(conn) == before
```

此片段展示失敗核對原理；完整腳本的 `rejected` 還要求必須真的收到預期錯誤，避免函式意外成功卻被測試放過。交易失敗後 `conn.in_transaction` 應為 False。

還原也透過公開更新 API，而不是單獨 UPDATE 文字：

```python
original = {c["chunk_id"]: c["text"] for c in artifact["chunks"]
            if c["document_id"] == "D001"}
update_document(conn, "D001", 2, original, prepared=artifact)
```

成功後版本為 3。原文及向量 bytes 與版本 1 相同，不代表「歷史上沒有修改過」；版本計數不能倒退。因此此時 `check` 可通過，baseline `evaluate` 仍應拒絕。若要再跑整套驗收，由教師依第 15 節準備新 checkpoint，而不是手動把版本改回 1。

### 4. 交接限制比漂亮分數重要

报告至少寫：server／Connector 版本、artifact source_hash、模型 revision、實際 case／category／k、兩份 EXPLAIN、八題結果、交易前後快照核對、最終版本與未驗項目。私人設定只寫檔案用途，不附內容。

如果失敗發生在成功 commit 之後、還原之前，資料可能停在版本 2。不要再次盲跑整支腳本，先執行 `check` 與一致性 SQL，看現在的版本和內容，再由教師決定恢復流程。這支程式不是背景自動修復器，且不會為了清除錯誤而 DROP／覆蓋資料。

人工作答分析也要保留：Q03 的高相似候選仍不支援 5 GHz；Q05 不能將 A/B SOP 套到 H；Q08 應零候選。這些不是加入生成式模型就會自動消失的問題。只能聲稱本次案例、固定資料和環境的結果，不能保證模型準確度或 CPU 速度。

---

## Workshop

### 題目

checkpoint 執行 整理結論。

1. 確認初始版本 1 與 artifact 一致，再執行完整驗收。
2. 對每個 check 附實際輸出或失敗原因，注明 ANN 是否真的測到。
3. 確認最終原文已恢復且 D001 版本為 3，其他文件仍為 1。
4. 交出一份不含密碼的結論，明確列出模型品質及 VM／效能未驗範圍。

### 預期輸出

```text
完整性／唯一性／版本拒絕／回滾／還原：依實際執行列出
EXPLAIN：附實際計畫，不用教材猜測
八題：附實際 IDs 與人工相關集合
最終 D001 版本：3；原文、hash、向量 bytes 與 baseline 相同
未驗證：逐項明示，不當成通過
```

### 解答

[24 Workshop 解答](workshop/24-acceptance.md)。完成本節表示能交出可核對的增量證據，不代表已通過正式上線安全或大規模效能審查。

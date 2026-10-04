# Workshop：客服知識庫上線前驗收

> **Ch1～Ch16 綜合專案：進入 Vector 前的資料庫基線**

## 專案情境

客服團隊準備啟用產品與 SOP 知識庫，下一階段將加入 Embedding 與 Vector Search。你是負責上線前驗收的資料庫／後端工程師。

在建立任何向量表之前，你必須證明：

```text
資料正確、權限適當、交易可復原、查詢可解釋、備份可還原、匯入不污染資料
```

最後提交一份驗收報告，決定：

```text
可以進入 Vector 階段
```

或：

```text
不得進入 Vector 階段
```

## 使用檔案

公開 demo repo：

```text
course_db.py
demo/11-crud.py
demo/12-transactions.py
demo/13-errors.py
demo/14-indexes.sql
demo/15-backup-restore.sh
demo/16-import-quality.py
workshop/16-import-quality.py
data/import-errors.csv
```

Private Workshop repo：

```text
student/workshop-acceptance.md
```

## 規則

- 使用自己的 Ubuntu VM、自己的 MariaDB 與自己的設定檔。
- 不提交密碼、私人 JSON、editor cnf、core.sql 或完整產品資料截圖。
- 不修改正式 P001～P012。
- 練習資料只使用 P9xx，完成後清理。
- 不使用 root、`GRANT ALL ON *.*`、`FOREIGN_KEY_CHECKS=0` 或 `LOAD DATA INFILE` 逃避驗收。
- 每一項都要保留命令與安全的結果摘要；不要只貼「成功」。

## 任務一：接手 baseline

```bash
cd ~/workspace/mariadb-demo
. "$HOME/mariadb-course-venv/bin/activate"
python3 course_db.py check
```

記錄：

```text
account = course_app@localhost
database = mariadb_workshop_2026
products = 12
documents = 8
chunks = 16
versions = products-v1, sop-v1
```

## 任務二：驗證 CRUD 與交易

執行：

```bash
PYTHONPATH=. python demo/11-crud.py
PYTHONPATH=. python demo/12-transactions.py
```

保留：

```text
quote preserved; injection lookup=None
commit: product=1 link=1 (second connection)
second write rejected: errno=1452
rollback: product=0 link=0 (second connection)
cleanup: P912/P913 absent
```

## 任務三：驗證錯誤分類

執行：

```bash
PYTHONPATH=. python demo/13-errors.py
PYTHONPATH=. python ../mariadb-workshop/teacher/answers/13-connection-failure.py
PYTHONPATH=. python ../mariadb-workshop/teacher/answers/13-errors.py
```

記錄 1062、2002 與 mock `OK`。說明：

```text
1062：重複鍵
1452：外鍵不存在
2002：socket 連線失敗
```

## 任務四：驗證查詢路徑

使用 `course_editor` 執行：

```bash
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < demo/14-indexes.sql
mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" \
  mariadb_workshop_2026 < workshop/14-indexes.sql
```

提交三種 EXPLAIN 的 `key`、`type`、`rows`，以及前三筆：

```text
P001 800.00
P002 1200.00
P008 1250.00
```

## 任務五：完成備份還原演練

先確認教師提供的 restore 庫為空，再執行一次：

```bash
bash demo/15-backup-restore.sh "$HOME/mariadb-core-backup-15"
```

記錄 checksum、`VERIFIED`、`cmp` 與：

```text
12  8  16  2
```

說明本次不涵蓋至少三種物件。

## 任務六：驗證 CSV 匯入品質

執行：

```bash
PYTHONPATH=. python demo/16-import-quality.py
PYTHONPATH=. python workshop/16-import-quality.py
PYTHONPATH=. python workshop/16-import-quality.py --database
```

記錄：

```text
壞批次 inserted=0
好批次 inserted=2
重送 inserted=0
cleanup complete
```

## 最終報告

建立 `baseline-report.md`，只提交安全摘要：

```markdown
# 客服知識庫上線前驗收報告

- VM／日期：
- 結論：可以進入 Vector 階段／不得進入 Vector 階段

## Evidence

- [ ] baseline：course_app、資料庫、12/8/16、兩個版本
- [ ] CRUD 與參數化輸入
- [ ] transaction commit／rollback／1452
- [ ] 1062／2002／mock tests
- [ ] EXPLAIN、索引順序與查詢前三筆
- [ ] backup checksum／restore／cmp
- [ ] CSV 壞批次 0、好批次 2、重送 0
- [ ] P9xx 已清理，正式 checkpoint 未變更

## 限制與風險

- 未驗證的項目：
- 進入 Vector 前仍需注意：
```

## 通過標準

只有全部證據具備，且正式 checkpoint 仍為：

```text
products=12, documents=8, chunks=16
```

才可以寫：

```text
可以進入 Vector 階段
```

缺少任何真實資料庫證據、留下 P9xx、修改正式資料或洩漏秘密，都必須寫：

```text
不得進入 Vector 階段
```

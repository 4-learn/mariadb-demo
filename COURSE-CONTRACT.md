# 04～24 共用實作契約

日期：2026-09-16。供本輪作者與測試共用；正式操作說明見各節及教師指引。

## 環境與權限

- 01～03 的 mariadb_course／course_reader／products-v1 完全保留，不因進階實作改掉初學者答案。
- 04～24 使用新隔離庫 `mariadb_workshop_2026`，先複製同一份 products-v1，再加入 SOP；不是另換產品情境。
- 教師用 `prepare_workshop.py`（主 agent 製作）一次準備 checkpoint，拒絕覆蓋既有庫／帳號。新增 3 個表與 chunks 由 `data/sop_seed.sql` 提供。
- `course_editor@localhost`：SELECT／INSERT／UPDATE／DELETE／CREATE／ALTER／INDEX，只限 workshop 與預備的 `mariadb_restore_2026`；不含 DROP、GRANT、其他庫。
- `course_app@localhost`：SELECT／INSERT／UPDATE／DELETE，只限 workshop。向量表／索引由 editor／教師準備，不用應用帳號建表。
- editor 私人檔 `~/mariadb-course-editor.cnf`，0600；client 設定不含 database，登入須 `mariadb --defaults-file="$HOME/mariadb-course-editor.cnf" mariadb_workshop_2026`，以便相同檔案供 dump 使用。
- Python `course_db.connect(config_path=None)` 讀 `COURSE_DB_CONFIG` 或 `~/mariadb-course-app.json`；JSON keys 為 user/password/database/unix_socket。database 固定 workshop，socket 路徑實際提供；連線預設 autocommit=True，多步操作明確 begin／commit／rollback。CLI 不接受命令列明文密碼。
- 17～22 課堂主流程改為 MariaDB client／SQL；embedding 使用教師預計算 fixture，學生不需 Python、venv 或模型推論。
- Connector/Python 固定 `mariadb==1.1.14`。開發端會在 MariaDB 官方 11.8.9 Ubuntu24.04 base 安裝 libmariadb-dev／Python build dependencies 測試，不修改主機套件。

## 資料

原 products／categories 定義與 12 筆資料不變；course_meta 增加 sop-v1 列，所以進階庫有 products-v1、sop-v1 兩列。

```text
documents(document_id VARCHAR(16) PK, title VARCHAR(120), source_version INT, status ENUM active/inactive)
product_documents(product_id CHAR(4), document_id VARCHAR(16), PK pair, FK products/documents)
chunks(chunk_id VARCHAR(16) PK, document_id VARCHAR(16) FK, source_version INT, text TEXT, content_hash CHAR(64))
```

- 8 documents：D001～D008，各 2 chunks，共 C001～C016。初始 source_version=1；content_hash=SHA256(UTF-8 原文)，SQL 可 SHA2(text,256)。
- D003 inactive，其餘 active。關聯：D001→P001/P002；D002→P004/P005；D003→P003；D004→P006/P007；D005→P001/P008；D006→P009；D007→P011；D008→P012。故 P010 沒 SOP，P001 有兩份；同一 SOP 可連多產品。
- 全為虛構產品說明，不作真實設備安全指示。C001 必含「重設」但不含「恢復出廠設定」，用後者作 LIKE 同義詞漏失。
- C003／C004 描述閘道器只支援 2.4 GHz、不支援 5 GHz；測試「支援 5 GHz」可作否定／無答案。
- Agent A 建立 data/sop_seed.sql 與 data/sop_corpus.json。JSON 形式：{"dataset_version":"sop-v1","documents":[{"document_id":"D001","title":"...","source_version":1,"status":"active"}],"links":[["P001","D001"]],"chunks":[{"chunk_id":"C001","document_id":"D001","source_version":1,"text":"..."}]}。兩份須內容一致。
- 04～09 的 DDL／寫入練習用 practice_* 表或 P9xx 練習列，不能讓後續 checkpoint 漂移。DML 可 rollback；DDL 不宣稱 rollback。錯誤示例與成功 SQL 分開，不用 --force 掩蓋問題。

## 搜尋與版本

- Agent C 建立 `embedding_course.py`、`vector_course.py`、`data/search_cases.json` 與向量 DDL。使用固定 BAAI/bge-small-zh-v1.5 @ 7999e1d3359715c523056ef9478215996d62a620，512 維，normalize_embeddings=True；query 前綴沿官方模型卡。
- 模型測試可用 /tmp/opencode/llm-lessons-venv 與 HF_HOME=/tmp/opencode/llm-model-cache；主 agent 不重装此 venv。
- 可預計算原 corpus／固定 queries／一組更新文件的真實向量，存 JSON，清楚標記模型與來源 hash；離線預計算不冒充學生新查詢的 encode。
- `chunk_vectors` 每 chunk 一筆，含 source_version、content_hash、model_id、model_revision、preprocessing_id、embedding VECTOR(512) NOT NULL，FK chunks。此輪只支援一個固定模型集合；metadata 不符就拒絕，不混向量空間。
- 19 精確比較先不依賴 ANN；20 才建立向量索引，精確對照需明確繞過該索引並 EXPLAIN 驗證。不靠小資料或一次結果宣稱更快／召回必定正確。
- 21 回傳唯一 chunk：document active，至少一個關聯 product active 且符合 filter；先形成合格集合取 top-k，不讓 JOIN 重複占位置。人工 qrels 綁定 filter／版本，空集合即無符合文件；分數不是機率或自動拒答規則。
- 22 更新一份完整 document 的兩段文字：交易外 encode；短交易內鎖定並核對 expected document source_version，兩 chunks／hash／vectors 與 document 版本一起更新。版本衝突或任何寫入失敗一律 rollback。不得只更新一段版本而讓另一段和 document 不一致。
- 23 CLI 可用明示 metadata 的預計算向量串接；24 增量核對成功、失敗、還原證據，不要求從零大專案。

## 各作者範圍

- A：04-relations.md、05-ddl.md、06-insert.md、07-update-delete.md、08-joins.md、09-aggregate-like.md；data/sop_seed.sql、sop_corpus.json；demo／workshop 中 04～09 檔；homework/09-relational.md。
- B：10-python-connection.md、11-parameterized-crud.md、12-transactions.md、13-errors.md、14-indexes.md、15-backup-restore.md、16-import-quality.md；course_db.py；demo／workshop 中 10～16 檔；data/import-errors.csv；homework/13-python.md、16-operations.md。
- C：17-embedding.md、18-vector-storage.md、19-vector-ranking.md、20-ann.md、21-filters-evaluation.md、22-consistency.md、23-integration.md、24-acceptance.md；embedding_course.py、vector_course.py、data/search_cases.json；demo／workshop 中 17～24 檔；homework/22-search.md。
- 主 agent：環境 build、prepare_workshop.py、整課測試、README／TEACHER／RESULTS、发布工具與 Book Mode。其他作者不改這些或 01～03。

三份既有 template 不變。每篇有 35＋15 配時、先修 checkpoint、實際可執行例子、預期輸出／失敗判準與具體解答。不寫假測試數字、不建立尚未存在的遠端 URL。程式與 SQL 要能從教學內容核對，不只一行「執行腳本」代替概念講解。

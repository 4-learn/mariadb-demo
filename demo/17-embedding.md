# 17 Embedding：讓文字成為可比較的數字

> **定位**：用固定的中文模型將 SOP 與問題編成 512 維向量，保留來源及版本，不把相似度當答案。

[上一節](16-import-quality.md) · [下一節](18-vector-storage.md)

時間：講解與示範 35 分鐘，Workshop 15 分鐘。以下判準是學生應實際核對的條件，不是 VM 已實測的宣稱。

## 學習目標

- 說明 embedding 與文字、token、產品編號各有什麼不同。
- 使用固定 model revision、CLS pooling 與 L2 normalization，實際產生 512 維向量。
- 區分即時 encode 與教師預計算，核對 corpus、hash 及前處理設定。

## 範例程式碼

- [模型與 artifact 程式](embedding_course.py)、[小型 encode 示範](demo/17-embedding.py)。
- [固定 SOP corpus](data/sop_corpus.json)、[八筆人工判讀規則](data/search_cases.json)。
- [固定 revision 模型卡](https://huggingface.co/BAAI/bge-small-zh-v1.5/blob/7999e1d3359715c523056ef9478215996d62a620/README.md)。

---

## 情境

客服輸入「恢復出廠設定」，但 C001 寫「重設」。`LIKE '%恢復出廠設定%'` 找不到這一段，不代表 corpus 沒有相關內容。你要增加「依語意找候選段落」的功能，而不是更換資料或讓模型自行編寫設備指示。所有產品及 SOP 均為虛構課堂資料。

先修 checkpoint：完成 16 的匯入品質練習，`mariadb_workshop_2026` 仍有原始 8 documents、16 chunks、初始版本 1，且本機可讀 `data/sop_corpus.json`。本節 encode 不需 DB 連線；不能拿別份 corpus 代替缺少的檔案。

---

## 講解

### 1. 一串數字表示文字，不是把答案放進資料庫（7 分鐘）

Embedding 是模型把文字映射成固定長度的浮點數序列。512 是輸出座標數，不是字數、token 數或可存 512 篇文章。兩段文字可以有相近方向，但數字本身不包含「這項操作安全」的保證。

本課以 chunk 為檢索單位，保留 document_id、chunk_id、source_version 與原文。取出候選時才用這些欄位回查原文及適用產品。不要把模型輸出的座標命名成「重設程度」等人類特徵；這不是人工指定的 512 個欄位。

### 2. 固定模型、前處理與執行環境（8 分鐘）

模型為 `BAAI/bge-small-zh-v1.5`，revision 為 `7999e1d3359715c523056ef9478215996d62a620`，輸出 512 維。學生在自己的新 venv 安裝，不修改教師的既有 LLM venv：

```bash
python3 -m venv "$HOME/mariadb-vector-venv"
. "$HOME/mariadb-vector-venv/bin/activate"
python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install transformers==4.57.3 huggingface-hub==0.36.2 numpy==2.2.6
```

教師先確認 VM 的 Python／架構支援套件，預留模型下載空間與時間；上課 35 分鐘不包含第一次下載。CPU 可以執行，但不保證任何 VM 的耗時或排名。第 18 節連線還需要前面已準備的 `mariadb==1.1.14` 與 Connector/C 開發依賴。

本課不依賴 sentence-transformers 套件，而是依模型卡的 Transformers 實作取第一個 token 的 CLS，再做 L2 normalization。等價的設定意圖是 `normalize_embeddings=True`，metadata 也明記此值：

```python
with torch.inference_mode():
    cls = model(**batch).last_hidden_state[:, 0]
    vectors = torch.nn.functional.normalize(cls, p=2, dim=1)
```

查詢加上模型卡指定前綴 `为这个句子生成表示以用于检索相关文章：`；SOP 原文不加。前綴保留模型卡原字，不翻譯。課程程式拒絕超過 512 tokens 的輸入，而不是偷偷截斷後仍宣稱 encode 了全文。

### 3. 真正執行 encode（10 分鐘）

在課程根目錄執行，首次連網下載固定 revision：

```bash
python demo/17-embedding.py
```

已快取模型時，可改 `python demo/17-embedding.py --offline`。離線缺檔應明確失敗，不臨時换模型。等同的可互動程式為：

```python
from embedding_course import Encoder, metadata
encoder = Encoder(offline=True)
v = encoder.encode(["如何恢復出廠設定？"], query=True)[0]
print(metadata())
print(len(v), sum(x*x for x in v))
```

第一項應為 512，第二項應接近 1，非要求浮點數剛好等於 1。完整向量包含正負小數；不應複製示範的前五個數字再補零成向量。`encode` 的輸入是 list，輸出是一個 list of vectors，`[0]` 才是第一段文字的向量。

### 4. Artifact 是可追溯的計算成果（10 分鐘）

```bash
python embedding_course.py generate --output "$HOME/mariadb-vectors.json" --offline
python embedding_course.py validate --artifact "$HOME/mariadb-vectors.json"
```

產物包含原始 16 chunks、八筆固定問題、D001 两段新版文字及其實際向量。`source_hash` 對 JSON 正規序列化計算，避免單純空白排版造成內容 hash 不同；`provenance.source_file_sha256` 另外保存檔案原始 bytes 的 hash。每段 `content_hash` 都是原文 UTF-8 的 SHA-256；`payload_hash` 檢查整份產物是否被意外改動。

這些 hash 可發現誤改，**不是數位簽章**。有能力改內容的人也能重算 hash，教師仍要從信任管道發送 artifact。版本名稱相同但來源 hash 不同，也不能混用。

教師可提供已生成 artifact 給沒有模型快取的學生，讓 18～24 的 SQL 照常進行，但必須標示「預計算」。它只支援 `Q01`～`Q08` 的原文；新問題一定要重新 encode，不能選一筆相似問題的向量冒充。本節產物不是固定排名答案，後續仍需實測距離。

---

## Workshop

### 題目

15 分鐘：讀 metadata 4 分鐘、執行及核對向量 7 分鐘、記錄失敗 4 分鐘。

1. encode「如何恢復出廠設定？」並記下維度、平方範數、revision 與是否離線。
2. 以原始 corpus 生成 artifact，或明示使用教師預計算檔。核對 16／8／2 的三種向量數量。
3. 解釋為何 query 有 instruction、文件沒有；為何 512 維不能換成另一模型的 512 維。

### 預期輸出

```text
dimension = 512
squared_norm 接近 1
chunks = 16 / queries = 8 / updated_chunks = 2
metadata.model_revision = 7999e1d3359715c523056ef9478215996d62a620
```

離線快取缺失、輸入過長、檔案已存在或 hash 不符都不算完成。記錄實際錯誤，不把它改寫成成功；`generate` 拒絕覆蓋既有 artifact，請選新檔名而非盲目重做。

### 解答

[17 Workshop 解答](workshop/17-embedding.md)。通過條件是實際 encode 或誠實標示預計算，並完成 metadata 核對；不要求模型一定把某段排第一。

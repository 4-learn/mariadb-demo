# 17 Embedding Workshop

## 情境

你是客服搜尋工具的工程師，已取得同一份 sop-v1，現在要證明向量是真的由固定模型產生，而不是貼上任意數字。

### 專案背景

C001 用「重設」，使用者用「恢復出廠設定」。本練習只建立比較表示，不要求一定命中，也不生成安全操作答案。

### 使用者需求

> 「我要知道這些數字從哪裡來；離線示範也不能冒充剛剛計算的新問題。」

### 你的任務

1.核對模型及 corpus encode 或驗證教師 artifact寫限制。
2. 記錄 revision、dimension、norm、是否使用預計算。
3. 解釋新問題為何不能拿固定 Q01 的向量代替。

### 技術需求

- CPU Transformers：固定 revision、CLS pooling、L2 normalization。
- 不安裝到教師既有 venv；自己的環境依第 17 節準備。
- 不需 DB；讀原本 8 docs／16 chunks，不換資料集。

## 輸入資料格式

```python
texts = ["如何恢復出廠設定？"]
query = True
```

這是一個含一段文字的 list；query=True 才加模型卡前綴。文件 encode 用 query=False。

## 輸出示例

```text
維度 512；norm 接近 1
revision 7999e1d3359715c523056ef9478215996d62a620
artifact 16 chunks + 8 recorded queries + 2 updated chunks
```

不是要求每台 CPU 輸出逐 byte 相同小數，也不指定檢索排名。

## 你需要實作的功能

```bash
python demo/17-embedding.py --offline
python embedding_course.py validate --artifact "$HOME/mariadb-vectors.json"
```

### 提示

1. 快取缺少檔案時 `--offline` 應失敗，先由教師補齊相同 revision。
2. 已存在的 output 不覆蓋，選新檔名保留來源。
3. 分開記錄檔案 bytes hash 與正規 JSON source_hash。

## 解答

完整核對程式：

```python
from pathlib import Path
from embedding_course import load_artifact, validate_vector
a = load_artifact(Path.home() / "mariadb-vectors.json")
assert len(a["chunks"]) == 16
assert len(a["queries"]) == 8
assert len(a["updates"]["D001"]["chunks"]) == 2
for c in a["chunks"]:
    validate_vector(c["embedding"])
print(a["source_hash"], a["metadata"], a["provenance"]["packages"])
```

512 維只代表相同長度，不代表相同模型空間；必須連 revision、pooling、normalization 與 query instruction 一起固定。模型卡建議檢索問題加 instruction、段落不加，故兩條處理路徑不同。

通過：實際 encode 並核對 norm，或明示只驗證教師產物；後者不宣稱本機已跑模型。失敗：用隨機數、抄另一題向量、忽略模型版本，或把離線下載錯誤記成成功。

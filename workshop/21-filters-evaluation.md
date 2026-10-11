# 21 篩選與評估 Workshop

## 任務

先執行主課 SQL，再使用同一 code section。可自己完成或請 Agent 補 TODO；你必須核對實際 IDs 與 qrels。

```python
from pathlib import Path
from vector_course import evaluate, search

artifact_path = Path.home() / "mariadb-vectors.json"
# TODO 1：執行 Q01 的 exact top-k，保留實際唯一 IDs。
q01_rows = None
# TODO 2：執行 Q08，確認 category=999 不跨分類補滿。
q08_rows = None
print("Q01 =", [r["chunk_id"] for r in q01_rows])
print("Q08 =", [r["chunk_id"] for r in q08_rows])
```

## 執行與驗收

分類 1 應十個唯一 chunk；Q08 應零列；Q03/Q04 保留不同 qrels 與實際候選。填寫 Q01 的 `|R∩S|/3` 與 `|R∩S|/|R|`，R 空時記 null。未命中、回傳候選或否定文字都要如實保留，不為了平均分數修改標註。

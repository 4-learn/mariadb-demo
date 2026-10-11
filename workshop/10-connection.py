from contextlib import closing
from course_db import connect

# Workshop：請完成兩個 TODO，再執行本檔案。
# 可以自己補完，也可以請 Agent 只修改本檔案。
with closing(connect()) as conn:
    with closing(conn.cursor()) as cur:
        # TODO 1：執行身分與交易設定查詢，並把結果存到 identity。
        # 提示：SQL 是 SELECT DATABASE(), CURRENT_USER(), @@autocommit
        identity = None

        # TODO 2：查詢 P001 的 product_id、name、price，並把結果存到 product。
        # 提示：使用 ? 參數與 ("P001",) tuple，不要拼接 SQL。
        product = None

        print(identity)
        print(product)

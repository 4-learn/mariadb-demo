from contextlib import closing
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_db import connect, create_product, delete_product, get_product, update_stock

with closing(connect()) as conn:
    assert get_product(conn, "P915") is None, "P915 occupied"
    conn.begin()
    try:
        assert create_product(conn, "P915", "客服's 測試品", price="125.50") == 1
        assert update_stock(conn, "P915", 4) == 1
        row = get_product(conn, "P915")
        assert row["name"] == "客服's 測試品" and row["stock"] == 4
        assert str(row["price"]) == "125.50"
        assert get_product(conn, "P915' OR 1=1 -- ") is None
        assert delete_product(conn, "P915") == 1
        assert delete_product(conn, "P915") == 0
        print("create=1 update=1 price=125.50 stock=4 delete=1 repeated_delete=0")
    finally:
        conn.rollback()
    assert get_product(conn, "P915") is None
print("quote/injection/cleanup OK")

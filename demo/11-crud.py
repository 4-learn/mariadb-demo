from contextlib import closing
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_db import connect, create_product, delete_product, get_product, update_stock

with closing(connect()) as conn:
    if get_product(conn, "P911") is not None:
        raise RuntimeError("P911 occupied; do not overwrite another exercise")
    conn.begin()
    try:
        name = "O'Reilly'; DELETE FROM products; --"
        assert create_product(conn, "P911", name) == 1
        assert get_product(conn, "P911")["name"] == name
        assert get_product(conn, "P001' OR '1'='1") is None
        print("quote preserved; injection lookup=None")
        assert update_stock(conn, "P911", 7) == 1
        print("stock=" + str(get_product(conn, "P911")["stock"]))
        assert delete_product(conn, "P911") == 1
        print("deleted=" + str(get_product(conn, "P911") is None))
    finally:
        conn.rollback()
    assert get_product(conn, "P001") is not None
    print("rollback cleanup; P001 retained")

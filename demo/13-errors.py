from contextlib import closing
import mariadb
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_db import connect, create_product, get_product

with closing(connect()) as conn:
    if get_product(conn, "P914"):
        raise RuntimeError("P914 occupied")
    conn.begin()
    try:
        create_product(conn, "P914", "錯誤分類測試")
        try:
            create_product(conn, "P914", "不可覆蓋")
        except mariadb.IntegrityError as exc:
            assert exc.errno == 1062
            print("duplicate: errno=1062; not retried")
        else:
            raise AssertionError("expected duplicate rejection")
    finally:
        conn.rollback()
    assert get_product(conn, "P914") is None
    with closing(conn.cursor()) as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone() == (1,)
    print("rollback complete; same connection SELECT 1=1")
print("cursor and connection closed")

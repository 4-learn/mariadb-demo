from contextlib import closing
import mariadb
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_db import connect, create_product_with_document, get_product

with closing(connect()) as conn:
    if any(get_product(conn, pid) for pid in ("P912", "P913")):
        raise RuntimeError("P912/P913 occupied; stop rather than overwrite")
    with closing(conn.cursor()) as cur:
        cur.execute("SELECT document_id FROM documents WHERE document_id IN ('D001','D999')")
        assert cur.fetchall() == [("D001",)]
    created = False
    try:
        result = create_product_with_document(conn, "P912", "交易練習", "D001")
        created = True
        # A second connection proves COMMIT, not merely visibility to the writer.
        with closing(connect()) as observer:
            assert get_product(observer, "P912") is not None
            with closing(observer.cursor()) as cur:
                cur.execute("SELECT COUNT(*) FROM product_documents WHERE product_id = ?", ("P912",))
                assert cur.fetchone()[0] == 1
        print("commit: product=1 link=1 (second connection)")
        try:
            create_product_with_document(conn, "P913", "必須回復", "D999")
        except mariadb.IntegrityError as exc:
            assert exc.errno == 1452
            print("second write rejected: errno=1452")
        else:
            raise AssertionError("missing FK failure")
        with closing(connect()) as observer:
            assert get_product(observer, "P913") is None
            with closing(observer.cursor()) as cur:
                cur.execute("SELECT COUNT(*) FROM product_documents WHERE product_id = ?", ("P913",))
                assert cur.fetchone()[0] == 0
        print("rollback: product=0 link=0 (second connection)")
    finally:
        if created:
            conn.begin()
            try:
                with closing(conn.cursor()) as cur:
                    cur.execute("DELETE FROM product_documents WHERE product_id = ?", ("P912",))
                    cur.execute("DELETE FROM products WHERE product_id = ?", ("P912",))
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
    print("cleanup: P912/P913 absent")

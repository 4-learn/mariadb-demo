"""Lessons 10-16. Database calls require mariadb==1.1.14; CSV checks use stdlib."""

import argparse
from contextlib import closing
import csv
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import stat
import sys

DATABASE = "mariadb_workshop_2026"
FIELDS = ["product_id", "category_id", "name", "price", "stock", "status"]


def connect(config_path=None):
    """Return an open MariaDB connection; the caller owns and closes it."""
    path = Path(config_path or os.environ.get("COURSE_DB_CONFIG") or
                "~/mariadb-course-app.json").expanduser()
    with path.open(encoding="utf-8") as source:
        if stat.S_IMODE(os.fstat(source.fileno()).st_mode) & 0o077:
            raise ValueError("config must be private (chmod 600)")
        config = json.load(source)
    if not isinstance(config, dict) or set(config) != {
            "user", "password", "database", "unix_socket"}:
        raise ValueError("config requires user/password/database/unix_socket only")
    if any(not isinstance(value, str) or not value for value in config.values()):
        raise ValueError("config values must be nonempty strings")
    if config["user"] != "course_app" or config["database"] != DATABASE:
        raise ValueError("config must use course_app and workshop database")
    if not Path(config["unix_socket"]).is_absolute():
        raise ValueError("unix_socket must be an absolute path")
    import mariadb
    return mariadb.connect(**config, autocommit=True)


def checkpoint(conn):
    """Return identity, autocommit and deterministic baseline counts."""
    with closing(conn.cursor()) as cur:
        cur.execute("SELECT DATABASE(), CURRENT_USER(), @@autocommit")
        database, account, autocommit = cur.fetchone()
        cur.execute("SELECT dataset_version FROM course_meta ORDER BY dataset_version")
        versions = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT (SELECT COUNT(*) FROM products), "
                    "(SELECT COUNT(*) FROM documents), (SELECT COUNT(*) FROM chunks)")
        products, documents, chunks = cur.fetchone()
    return dict(database=database, account=account, autocommit=autocommit,
                versions=versions, products=products, documents=documents, chunks=chunks)


def get_product(conn, product_id):
    """Return a six-field dict (price is Decimal), or None."""
    with closing(conn.cursor()) as cur:
        cur.execute("SELECT product_id, category_id, name, price, stock, status "
                    "FROM products WHERE product_id = ?", (product_id,))
        row = cur.fetchone()
    return dict(zip(FIELDS, row)) if row else None


def _practice_id(product_id):
    if not isinstance(product_id, str) or not re.fullmatch(r"P9[0-9]{2}", product_id):
        raise ValueError("writes require a P9xx practice product_id")


def create_product(conn, product_id, name, category_id=1, price="100.00",
                   stock=1, status="active"):
    """Insert one practice row; return affected rows. Does not commit for caller."""
    _practice_id(product_id)
    with closing(conn.cursor()) as cur:
        cur.execute("INSERT INTO products "
                    "(product_id, category_id, name, price, stock, status) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (product_id, category_id, name, Decimal(price), stock, status))
        return cur.rowcount


def update_stock(conn, product_id, stock):
    """Return affected rows; 0 also means unchanged, not necessarily absent."""
    _practice_id(product_id)
    if type(stock) is not int or not 0 <= stock <= 4294967295:
        raise ValueError("stock must be an unsigned 32-bit integer")
    with closing(conn.cursor()) as cur:
        cur.execute("UPDATE products SET stock = ? WHERE product_id = ?",
                    (stock, product_id))
        return cur.rowcount


def delete_product(conn, product_id):
    """Delete one practice row; linked products require explicit unlink first."""
    _practice_id(product_id)
    with closing(conn.cursor()) as cur:
        cur.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        return cur.rowcount


def create_product_with_document(conn, product_id, name, document_id):
    """Own a two-write transaction on an idle autocommit connection.

    Return {product_id, document_id, committed: True}; on any failure roll back
    and re-raise. Do not call from an existing transaction (BEGIN is not nested).
    """
    if not conn.autocommit or conn.in_transaction:
        raise ValueError("transaction helper requires autocommit=True")
    _practice_id(product_id)
    conn.begin()
    try:
        create_product(conn, product_id, name)
        with closing(conn.cursor()) as cur:
            cur.execute("INSERT INTO product_documents (product_id, document_id) "
                        "VALUES (?, ?)", (product_id, document_id))
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    return dict(product_id=product_id, document_id=document_id, committed=True)


def validate_csv(path, category_ids, existing_ids=()):
    """Return {valid: bool, rows: list[dict], errors: list[dict]} without SQL.

    rows includes only individually valid rows. NEVER import rows when valid is
    False: a later duplicate invalidates the batch. Errors use CSV record-start
    physical line numbers. An exact \\N means NULL; empty text stays empty.
    """
    rows, errors = [], []
    seen = set(existing_ids)
    categories = set(category_ids)
    with open(path, newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source, strict=True)
        if reader.fieldnames != FIELDS:
            return dict(valid=False, rows=[], errors=[
                dict(line=1, field="header", code="expected_columns")])
        try:
            while True:
                line = reader.line_num + 1
                raw = next(reader, None)
                if raw is None:
                    break
                start = len(errors)

                def error(field, code):
                    errors.append(dict(line=line, field=field, code=code))

                if None in raw or any(value is None for value in raw.values()):
                    error("row", "column_count")
                    continue
                row = {key: None if value == r"\N" else value
                       for key, value in raw.items()}
                for field in FIELDS:
                    if row[field] is None:
                        error(field, "null_not_allowed")
                    elif row[field] == "":
                        error(field, "empty_not_allowed")
                pid = row["product_id"]
                if pid not in (None, ""):
                    if not re.fullmatch(r"P9[0-9]{2}", pid):
                        error("product_id", "practice_id_required")
                    if pid in seen:
                        error("product_id", "duplicate_id")
                    seen.add(pid)
                name = row["name"]
                if name and (not name.strip() or len(name) > 80):
                    error("name", "name_length")
                for field, upper in (("category_id", 2147483647),
                                     ("stock", 4294967295)):
                    value = row[field]
                    if value not in (None, ""):
                        if not re.fullmatch(r"[0-9]+", value) or len(value) > 10:
                            error(field, "unsigned_integer_required")
                        elif int(value) > upper:
                            error(field, "out_of_range")
                        else:
                            row[field] = int(value)
                            if field == "category_id" and row[field] not in categories:
                                error(field, "unknown_category")
                value = row["price"]
                if value not in (None, ""):
                    try:
                        price = Decimal(value)
                        if (not price.is_finite() or price < 0 or
                                price > Decimal("99999999.99") or
                                price != price.quantize(Decimal("0.01"))):
                            error("price", "money_range_or_scale")
                        else:
                            row["price"] = price
                    except InvalidOperation:
                        error("price", "invalid_decimal")
                if row["status"] not in (None, "", "active", "inactive"):
                    error("status", "invalid_status")
                if len(errors) == start:
                    rows.append(row)
        except csv.Error:
            errors.append(dict(line=reader.line_num, field="row", code="malformed_csv"))
    return dict(valid=not errors, rows=rows, errors=errors)


def import_products(conn, path):
    """Validate then atomically insert; return report plus inserted integer.

    Invalid input returns inserted=0. SQL failures (including races after
    validation) roll back all rows and propagate. Requires an idle connection.
    """
    if not conn.autocommit or conn.in_transaction:
        raise ValueError("import requires autocommit=True")
    with closing(conn.cursor()) as cur:
        cur.execute("SELECT category_id FROM categories")
        categories = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT product_id FROM products")
        existing = [r[0] for r in cur.fetchall()]
    report = validate_csv(path, categories, existing)
    report["inserted"] = 0
    if not report["valid"]:
        return report
    conn.begin()
    try:
        for row in report["rows"]:
            create_product(conn, **row)
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    report["inserted"] = len(report["rows"])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="private JSON path, never a password")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    get = commands.add_parser("get")
    get.add_argument("product_id")
    validate = commands.add_parser("validate")
    validate.add_argument("path")
    validate.add_argument("--categories", type=int, nargs="+", default=[1, 2, 3])
    load = commands.add_parser("import")
    load.add_argument("path")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            result = validate_csv(args.path, args.categories)
        else:
            with closing(connect(args.config)) as conn:
                if args.command == "check":
                    result = checkpoint(conn)
                elif args.command == "get":
                    result = get_product(conn, args.product_id)
                else:
                    result = import_products(conn, args.path)
        print(json.dumps(result, ensure_ascii=False, default=str, sort_keys=True))
        return 2 if isinstance(result, dict) and result.get("valid") is False else 0
    except Exception as exc:
        # Connector messages can include connection details. Log only type/code.
        print(json.dumps(dict(error=type(exc).__name__,
                              errno=getattr(exc, "errno", None))), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

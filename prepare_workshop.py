"""Teacher-only fresh 04-24 checkpoint; never overwrite 01-03 or existing data."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parent
DATABASE = "mariadb_workshop_2026"
RESTORE = "mariadb_restore_2026"


def prepare(execute_sql, directory, socket_path="/run/mysqld/mysqld.sock"):
    directory = Path(directory)
    if not directory.is_dir() or not Path(socket_path).is_absolute():
        raise ValueError("use an existing private directory and absolute socket path")
    seed = (ROOT / "data/seed.sql").read_bytes()
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    if hashlib.sha256(seed).hexdigest() != manifest["sha256"]:
        raise ValueError("products-v1 checksum mismatch")
    if not execute_sql("SELECT VERSION();").strip().startswith("11.8."):
        raise ValueError("expected MariaDB 11.8.x")
    if execute_sql(f"SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME IN ('{DATABASE}','{RESTORE}');").strip() != "0":
        raise ValueError("workshop or restore database exists; refusing to overwrite")
    if execute_sql("SELECT COUNT(*) FROM mysql.user WHERE User IN ('course_editor','course_app');").strip() != "0":
        raise ValueError("editor/app account exists; refusing to reuse privileges")
    targets = [directory / "mariadb-course-editor.cnf", directory / "mariadb-course-app.json"]
    if any(p.exists() or p.is_symlink() for p in targets):
        raise ValueError("private file exists; refusing to overwrite")
    passwords = {name: secrets.token_hex(24) for name in ("course_editor", "course_app")}
    settings = [
        f"[client]\nuser=course_editor\npassword={passwords['course_editor']}\nprotocol=socket\nsocket={socket_path}\ndefault-character-set=utf8mb4\n",
        json.dumps(dict(user="course_app", password=passwords["course_app"],
                        database=DATABASE, unix_socket=socket_path)),
    ]
    for target, content in zip(targets, settings):
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
    # DDL cannot be rolled back. On interruption, inspect before restoring a VM
    # checkpoint; never implement recovery by dropping an arbitrary existing DB.
    execute_sql(seed.decode().replace("mariadb_course", DATABASE))
    execute_sql((ROOT / "data/sop_seed.sql").read_text(encoding="utf-8"))
    execute_sql(f"CREATE DATABASE {RESTORE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    for user, password in passwords.items():
        execute_sql(f"CREATE USER '{user}'@'localhost' IDENTIFIED BY '{password}';")
    for db in (DATABASE, RESTORE):
        pattern = db.replace("_", r"\_")
        execute_sql(f"GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,ALTER,INDEX ON `{pattern}`.* TO 'course_editor'@'localhost';")
    pattern = DATABASE.replace("_", r"\_")
    execute_sql(f"GRANT SELECT,INSERT,UPDATE,DELETE ON `{pattern}`.* TO 'course_app'@'localhost';")
    return {"database": DATABASE, "restore": RESTORE, "products": 12, "documents": 8, "chunks": 16}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path.home())
    parser.add_argument("--socket", default="/run/mysqld/mysqld.sock")
    args = parser.parse_args()

    def execute(sql):
        result = subprocess.run(
            ["sudo", "mariadb", "--no-defaults", "--protocol=socket", "--user=root",
             f"--socket={args.socket}", "--default-character-set=utf8mb4", "--batch", "--skip-column-names"],
            input=sql, text=True, capture_output=True,
        )
        if result.returncode:
            raise RuntimeError("administrator SQL failed; private diagnostics withheld; do not blindly rerun")
        return result.stdout
    try:
        print(json.dumps(prepare(execute, args.directory, args.socket)))
    except Exception as exc:
        parser.exit(1, f"Stopped: {type(exc).__name__}; inspect the private VM, no automatic reset.\n")


if __name__ == "__main__":
    main()

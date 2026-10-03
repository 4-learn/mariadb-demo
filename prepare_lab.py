"""Prepare a new local course database; never reset existing data or accounts."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parent
DATABASE = "mariadb_course"
ACCOUNT = "course_reader"


def prepare(execute_sql, credentials):
    seed = (ROOT / "data/seed.sql").read_bytes()
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(seed).hexdigest() != manifest["sha256"]:
        raise RuntimeError("Seed checksum does not match the reviewed dataset; no changes made.")
    version = execute_sql("SELECT VERSION();").strip()
    if not version.startswith("11.8."):
        raise RuntimeError("Expected MariaDB 11.8.x; no changes made.")
    if execute_sql(
        "SELECT COUNT(*) FROM information_schema.SCHEMATA "
        f"WHERE SCHEMA_NAME = '{DATABASE}';"
    ).strip() != "0":
        raise RuntimeError("Course database already exists; refusing to overwrite.")
    if execute_sql(f"SELECT COUNT(*) FROM mysql.user WHERE User = '{ACCOUNT}';").strip() != "0":
        raise RuntimeError("Course account already exists; refusing to reuse privileges.")

    password = secrets.token_hex(24)
    # Exclusive creation also refuses an existing credential file or symlink.
    fd = os.open(credentials, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(
            f"[client]\nuser={ACCOUNT}\npassword={password}\nprotocol=socket\n"
            f"database={DATABASE}\ndefault-character-set=utf8mb4\n"
        )

    # DDL is not transactional. Keep credentials if setup fails; never auto-drop
    # a partially initialized schema. Restore the fresh VM snapshot after review.
    execute_sql(seed.decode("utf-8"))
    # Database-level GRANT treats underscores as wildcards, even inside backticks.
    grant_database = DATABASE.replace("_", r"\_")
    execute_sql(
        f"CREATE USER '{ACCOUNT}'@'localhost' IDENTIFIED BY '{password}';\n"
        f"GRANT SELECT ON `{grant_database}`.* TO '{ACCOUNT}'@'localhost';"
    )
    return version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials", type=Path, default=Path.home() / "mariadb-course-reader.cnf")
    args = parser.parse_args()

    def execute_sql(sql):
        result = subprocess.run(
            ["sudo", "mariadb", "--no-defaults", "--protocol=socket", "--user=root",
             "--default-character-set=utf8mb4", "--batch", "--skip-column-names"],
            input=sql, text=True, capture_output=True, check=False,
        )
        if result.returncode:
            # CLI diagnostics may echo account-creation SQL containing a secret.
            raise RuntimeError("Administrator SQL failed; stop and inspect the VM locally. No automatic reset.")
        return result.stdout

    try:
        version = prepare(execute_sql, args.credentials)
    except (OSError, RuntimeError) as exc:
        parser.exit(1, f"Setup stopped: {exc}\n")
    print(f"Prepared {DATABASE} on {version}; dataset products-v1, 12 products.")
    print(f"Private credentials: {args.credentials}. Do not upload or share this file.")


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Teacher-only reset for the Ch15 restore target.
# Usage: sudo bash demo/15-reset-restore-db.sh
set -Eeuo pipefail

restore_db="mariadb_restore_2026"

if [[ "${EUID}" -ne 0 ]]; then
    printf 'run as Ubuntu administrator: sudo bash %s\n' "$0" >&2
    exit 1
fi

read -r -p "Type RESET ${restore_db} to continue: " answer
if [[ "$answer" != "RESET ${restore_db}" ]]; then
    printf 'confirmation did not match; stopped\n' >&2
    exit 1
fi

mariadb <<SQL
DROP DATABASE IF EXISTS ${restore_db};
CREATE DATABASE ${restore_db}
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER
    ON ${restore_db}.* TO 'course_editor'@'localhost';
FLUSH PRIVILEGES;
SQL

printf 'RESET OK: %s is empty and ready for Ch15\n' "$restore_db"

#!/usr/bin/env bash
# Usage: bash demo/15-backup-restore.sh NEW_PRIVATE_OUTPUT_DIRECTORY
# Teacher must stop all writers/DDL for both databases throughout this exercise.
set -euo pipefail
umask 077
if [[ $# != 1 ]]; then
    printf 'usage: bash demo/15-backup-restore.sh NEW_OUTPUT_DIRECTORY\n' >&2
    exit 2
fi
config="$HOME/mariadb-course-editor.cnf"
source_db=mariadb_workshop_2026
restore_db=mariadb_restore_2026
tables=(categories products course_meta documents product_documents chunks)
client=(mariadb "--defaults-file=$config" --default-character-set=utf8mb4 --batch --raw --skip-column-names)
dump=(mariadb-dump "--defaults-file=$config" --default-character-set=utf8mb4
    --skip-add-drop-table --skip-add-locks --skip-lock-tables --no-tablespaces
    --skip-triggers --single-transaction --skip-comments --skip-dump-date
    --skip-extended-insert --order-by-primary --hex-blob)
[[ -f "$config" && "$(stat -c %a "$config")" == 600 ]] || {
    printf 'editor config missing or not mode 600\n' >&2; exit 1;
}
identity=$("${client[@]}" "$source_db" --execute='SELECT CURRENT_USER()')
[[ "$identity" == course_editor@localhost ]] || {
    printf 'expected course_editor@localhost\n' >&2; exit 1;
}
count=$("${client[@]}" "$source_db" --execute="SELECT COUNT(*) FROM information_schema.TABLES
    WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE'
    AND TABLE_NAME IN ('categories','products','course_meta','documents','product_documents','chunks')")
[[ "$count" == 6 ]] || { printf 'six ordinary checkpoint tables required\n' >&2; exit 1; }
vectors=$("${client[@]}" "$source_db" --execute="SELECT COUNT(*) FROM information_schema.TABLES
    WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='chunk_vectors'")
[[ "$vectors" == 0 ]] || { printf 'run lesson 15 before vector schema creation\n' >&2; exit 1; }
triggers=$("${client[@]}" "$source_db" --execute="SELECT COUNT(*) FROM information_schema.TRIGGERS
    WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE IN
    ('categories','products','course_meta','documents','product_documents','chunks')")
[[ "$triggers" == 0 ]] || { printf 'triggers outside backup scope\n' >&2; exit 1; }
# Editor has no TRIGGER privilege: teacher must independently attest no hidden
# triggers/routines/events. Visible metadata alone cannot prove their absence.
empty=$("${client[@]}" "$restore_db" --execute="SELECT COUNT(*) FROM information_schema.TABLES
    WHERE TABLE_SCHEMA=DATABASE()")
[[ "$empty" == 0 ]] || { printf 'restore database must be empty; no DROP attempted\n' >&2; exit 1; }
# mkdir fails if the path already exists. Never clobber a previous backup.
mkdir -- "$1"
output=$(realpath -- "$1")
"${dump[@]}" "$source_db" "${tables[@]}" > "$output/core.sql"
[[ -s "$output/core.sql" ]] || { printf 'empty dump\n' >&2; exit 1; }
# A checksum is integrity evidence, not restore evidence.
sha256sum "$output/core.sql" > "$output/core.sql.sha256"
sha256sum --check "$output/core.sql.sha256"
"${client[@]}" "$restore_db" < "$output/core.sql"
"${dump[@]}" "$restore_db" "${tables[@]}" > "$output/restored.sql"
cmp -- "$output/core.sql" "$output/restored.sql"
# Do not print VERIFIED until schema and every deterministic row dump match.
printf 'VERIFIED: six core tables, schema and rows match restored dump\n'
"${client[@]}" "$restore_db" --execute="SELECT
    (SELECT COUNT(*) FROM products), (SELECT COUNT(*) FROM documents),
    (SELECT COUNT(*) FROM chunks), (SELECT COUNT(*) FROM course_meta)"
printf 'Scope: six named ordinary tables only; excludes practice tables, accounts, grants, triggers, routines, events and vectors.\n'

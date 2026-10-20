#!/usr/bin/env bash
set -Eeuo pipefail

# Teacher/course-editor helper: reset only the MariaDB workshop data to the
# Ch24 v1 baseline, re-ingest vectors, ensure vector_idx, then run Ch24.
# It never drops a database and never edits version numbers in place.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
COURSE_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$COURSE_DIR"

ARTIFACT="${ARTIFACT:-$COURSE_DIR/data/mariadb-vectors.json}"
EDITOR_CNF="${EDITOR_CNF:-$HOME/mariadb-course-editor.cnf}"
APP_CONFIG="${APP_CONFIG:-$HOME/mariadb-course-app.json}"
DB="mariadb_workshop_2026"
SOCKET="${MARIADB_SOCKET:-/run/mysqld/mysqld.sock}"

if [[ ! -f "$ARTIFACT" ]]; then echo "ERROR: artifact not found: $ARTIFACT" >&2; exit 2; fi
if [[ ! -f "$EDITOR_CNF" ]]; then echo "ERROR: editor config not found: $EDITOR_CNF" >&2; exit 2; fi
if [[ ! -f "$APP_CONFIG" ]]; then echo "ERROR: app config not found: $APP_CONFIG" >&2; exit 2; fi

if [[ -x "${COURSE_PYTHON:-}" ]]; then PY="$COURSE_PYTHON"
elif [[ -x "$HOME/mariadb-course-venv/bin/python" ]]; then PY="$HOME/mariadb-course-venv/bin/python"
elif [[ -x "/home/timlu/mariadb-course-venv/bin/python" ]]; then PY="/home/timlu/mariadb-course-venv/bin/python"
else PY="$(command -v python3)"; fi

# --defaults-extra-file must be the first option after the executable.
MARIADB=(mariadb --defaults-extra-file="$EDITOR_CNF" --protocol=socket --socket="$SOCKET" "$DB")

printf '%s\n' '這會重置 mariadb_workshop_2026 的課程資料到 Ch24 初始 v1，重新匯入向量，並確保 vector_idx。'
printf '%s' '若確定要繼續，請輸入 RESET-CH24： '
read -r confirmation
[[ "$confirmation" == "RESET-CH24" ]] || { echo '已取消，未修改資料。'; exit 1; }

"${MARIADB[@]}" < "$SCRIPT_DIR/21-reset-baseline.sql"
PYTHONPATH="$COURSE_DIR" "$PY" vector_course.py --config "$APP_CONFIG" ingest --artifact "$ARTIFACT"

if ! "${MARIADB[@]}" -N -B -e "SHOW INDEX FROM chunk_vectors" | awk -F '\t' '$3 == "vector_idx" { found=1 } END { exit !found }'; then
  "${MARIADB[@]}" < "$SCRIPT_DIR/20-ann.sql"
fi

"${MARIADB[@]}" -N -B -e "SELECT document_id, source_version FROM documents ORDER BY document_id; SELECT COUNT(*) FROM chunk_vectors; SHOW INDEX FROM chunk_vectors;"
PYTHONPATH="$COURSE_DIR" "$PY" vector_course.py --config "$APP_CONFIG" check
PYTHONPATH="$COURSE_DIR" "$PY" demo/24-acceptance.py --artifact "$ARTIFACT"

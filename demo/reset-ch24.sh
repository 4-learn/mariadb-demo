#!/usr/bin/env bash
set -Eeuo pipefail

# Ch24 one-command setup/reset. Run from ~/mariadb-demo.
# It supports a clean workshop after prepare_workshop.py and an existing one.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
COURSE_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$COURSE_DIR"
ARTIFACT="${ARTIFACT:-$COURSE_DIR/data/mariadb-vectors.json}"
ARTIFACT_URL="${ARTIFACT_URL:-https://raw.githubusercontent.com/4-learn/mariadb-demo/main/data/mariadb-vectors.json}"
EDITOR_CNF="${EDITOR_CNF:-$HOME/mariadb-course-editor.cnf}"
APP_CONFIG="${APP_CONFIG:-$HOME/mariadb-course-app.json}"
APP_CONFIG_URL="${APP_CONFIG_URL:-https://raw.githubusercontent.com/4-learn/mariadb-demo/main/data/mariadb-course-app.json}"
SOCKET="${MARIADB_SOCKET:-/run/mysqld/mysqld.sock}"
HOST="${MARIADB_HOST:-}"
PORT="${MARIADB_PORT:-3306}"
DB="mariadb_workshop_2026"
PY="${COURSE_PYTHON:-}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

fail(){ echo "FAIL: $*" >&2; exit 1; }
if [[ ! -f "$ARTIFACT" ]]; then
  echo "[0/7] artifact missing: downloading $ARTIFACT"
  mkdir -p "$(dirname "$ARTIFACT")"
  curl --fail --location --silent --show-error --output "$ARTIFACT" "$ARTIFACT_URL"
fi
[[ -f "$ARTIFACT" ]] || fail "artifact not found: $ARTIFACT"
[[ -f "$COURSE_DIR/prepare_workshop.py" ]] || fail "prepare_workshop.py not found"
python3 - "$ARTIFACT" <<'PY'
import json, sys
p = json.load(open(sys.argv[1], encoding="utf-8"))
chunks = p.get("chunks", [])
meta = p.get("metadata", {})
if len(chunks) != 16 or meta.get("dimension") != 512:
    raise SystemExit("artifact must contain 16 chunks and dimension=512")
PY

printf '%s\n' 'This resets mariadb_workshop_2026 to the Ch24 v1 checkpoint.'
printf '%s' 'Type RESET-CH24 to continue: '
read -r confirmation
[[ "$confirmation" == "RESET-CH24" ]] || { echo 'Cancelled; no database changes made.'; exit 1; }

# Detect the workshop with the student's own course account, never MariaDB root:
# on Ubuntu, root only works through sudo, and a refused login must not be
# mistaken for a missing database.
if [[ -f "$EDITOR_CNF" ]]; then
  if [[ -n "$HOST" ]]; then
    PROBE=(mariadb --defaults-extra-file="$EDITOR_CNF" --host="$HOST" --port="$PORT")
  else
    PROBE=(mariadb --defaults-extra-file="$EDITOR_CNF" --protocol=socket --socket="$SOCKET")
  fi
  found="$("${PROBE[@]}" -N -B -e "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$DB'")" \
    || fail "cannot log in with $EDITOR_CNF; see the MariaDB error above. Nothing was changed."
  [[ "$found" == "$DB" ]] \
    || fail "$EDITOR_CNF exists but $DB is missing. Nothing was changed; ask the instructor before rerunning."
  echo '[1/7] workshop database exists: skip bootstrap'
elif [[ -n "$HOST" ]]; then
  fail "missing $EDITOR_CNF for remote host $HOST"
else
  # Clean VM: no course account yet. prepare_workshop.py uses sudo for setup.
  echo '[1/7] clean VM: running prepare_workshop.py (sudo password may be asked)'
  "$PY" prepare_workshop.py --directory "$HOME" --socket "$SOCKET"
fi

if [[ ! -f "$APP_CONFIG" ]]; then
  echo "[0/7] app config missing: downloading template $APP_CONFIG"
  curl --fail --location --silent --show-error --output "$APP_CONFIG" "$APP_CONFIG_URL"
fi
[[ -f "$EDITOR_CNF" ]] || fail "missing $EDITOR_CNF; prepare_workshop.py should create it"
[[ -f "$APP_CONFIG" ]] || fail "missing $APP_CONFIG"
chmod 600 "$EDITOR_CNF" "$APP_CONFIG"
python3 - "$APP_CONFIG" <<'PY'
import json, sys
p = json.load(open(sys.argv[1], encoding="utf-8"))
if p.get("user") != "course_app" or p.get("database") != "mariadb_workshop_2026":
    raise SystemExit("app config must target course_app/mariadb_workshop_2026")
PY
if [[ -n "$HOST" ]]; then
  MARIADB=(mariadb --defaults-extra-file="$EDITOR_CNF" --host="$HOST" --port="$PORT" "$DB")
else
  MARIADB=(mariadb --defaults-extra-file="$EDITOR_CNF" --protocol=socket --socket="$SOCKET" "$DB")
fi
"${MARIADB[@]}" -N -B -e "SELECT VERSION(), DATABASE();" | tee /tmp/ch24-db-check.txt
 grep -q '11\.8\.' /tmp/ch24-db-check.txt || fail 'MariaDB 11.8.x / database check failed'

# Ch18 is skipped only when its table already exists.
if ! "${MARIADB[@]}" -N -B -e "SHOW TABLES LIKE 'chunk_vectors'" | grep -qx chunk_vectors; then
  echo '[2/7] creating Ch18 chunk_vectors table'
  "${MARIADB[@]}" < "$SCRIPT_DIR/18-vector-storage.sql"
else
  echo '[2/7] Ch18 table exists: skip DDL'
fi

echo '[3/7] resetting Ch24 v1 baseline'
"${MARIADB[@]}" < "$SCRIPT_DIR/21-reset-baseline.sql"
echo '[4/7] ingesting artifact'
PYTHONPATH="$COURSE_DIR" "$PY" vector_course.py --config "$APP_CONFIG" ingest --artifact "$ARTIFACT"
PYTHONPATH="$COURSE_DIR" "$PY" vector_course.py --config "$APP_CONFIG" check

if ! "${MARIADB[@]}" -N -B -e "SHOW INDEX FROM chunk_vectors" | awk -F '\t' '$3 == "vector_idx" { found=1 } END { exit !found }'; then
  echo '[5/7] creating Ch20 vector_idx'
  "${MARIADB[@]}" < "$SCRIPT_DIR/20-ann.sql"
else
  echo '[5/7] Ch20 vector_idx exists: skip DDL'
fi

echo '[6/7] verifying ANN plan'
Q=$(PYTHONPATH="$COURSE_DIR" "$PY" vector_course.py --config "$APP_CONFIG" search --case Q01 --artifact "$ARTIFACT" --mode ann --k 3 --explain)
printf '%s\n' "$Q" | grep -q '"key": "vector_idx"' || fail 'ANN plan did not select vector_idx'

echo '[7/7] running Ch24 acceptance'
PYTHONPATH="$COURSE_DIR" "$PY" demo/24-acceptance.py --artifact "$ARTIFACT"
echo 'PASS: Ch24 complete; D001 should now be version 3.'

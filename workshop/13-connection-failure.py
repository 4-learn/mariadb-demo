"""Real driver, deliberately absent socket; no server configuration changed."""
import json
import os
from pathlib import Path
import tempfile
import mariadb
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_db import connect

source = Path(os.environ.get("COURSE_DB_CONFIG") or "~/mariadb-course-app.json").expanduser()
original = source.read_bytes()
config = json.loads(original)
with tempfile.TemporaryDirectory() as folder:
    config["unix_socket"] = str(Path(folder) / "absent.sock")
    private = Path(folder) / "app.json"
    private.touch(mode=0o600)
    private.write_text(json.dumps(config), encoding="utf-8")
    try:
        conn = connect(private)
    except mariadb.OperationalError as exc:
        assert exc.errno == 2002, exc.errno
        print("connection rejected: errno=2002; no connection returned")
    else:
        conn.close()
        raise AssertionError("connection unexpectedly succeeded")
assert source.read_bytes() == original
print("original config unchanged; temporary config removed")

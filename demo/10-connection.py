from contextlib import closing
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_db import checkpoint, connect

with closing(connect()) as conn:
    print(json.dumps(checkpoint(conn), ensure_ascii=False, sort_keys=True))

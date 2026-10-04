from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_db import validate_csv

path = Path(__file__).resolve().parents[1] / "data/import-errors.csv"
report = validate_csv(path, {1, 2, 3})
assert not report["valid"]
assert report["errors"] == [
    {"line": 3, "field": "product_id", "code": "duplicate_id"},
    {"line": 4, "field": "category_id", "code": "unknown_category"},
    {"line": 5, "field": "name", "code": "empty_not_allowed"},
    {"line": 6, "field": "name", "code": "null_not_allowed"},
]
for error in report["errors"]:
    print("{line}:{field}:{code}".format(**error))
print("valid=False; individually_valid_rows=2; import entire batch forbidden")

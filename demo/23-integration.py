"""Small complete CLI: explicit recorded-query retrieval, no answer generation."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_db import connect
from embedding_course import load_artifact
from vector_course import recorded_query, search

parser = argparse.ArgumentParser()
parser.add_argument("--config")
parser.add_argument("--artifact", required=True)
parser.add_argument("--case", default="Q01")
args = parser.parse_args()
artifact = load_artifact(args.artifact)
case, vector = recorded_query(artifact, args.case)
connection = connect(args.config)
try:
    rows = search(connection, vector, k=3, category_id=case["category_id"])
    print(json.dumps({"query": case["query"], "embedding_mode": "recorded-query",
                      "model": artifact["metadata"], "source_hash": artifact["source_hash"],
                      "candidates": rows,
                      "notice": "候選段落不是答案；請核對型號、版本與否定詞。"},
                     ensure_ascii=False, indent=2))
finally:
    connection.close()

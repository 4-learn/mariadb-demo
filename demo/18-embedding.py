"""Run from the course directory: python demo/17-embedding.py --offline."""
import argparse
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from embedding_course import Encoder, metadata

parser = argparse.ArgumentParser()
parser.add_argument("--offline", action="store_true")
args = parser.parse_args()
encoder = Encoder(args.offline)
vector = encoder.encode(["如何恢復出廠設定？"], query=True)[0]
print(metadata())
print({"dimension": len(vector), "norm": math.sqrt(sum(x*x for x in vector)),
       "first_five": vector[:5]})

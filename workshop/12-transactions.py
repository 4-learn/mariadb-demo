"""Worked answer: execute both committed and rolled-back integration cases."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parents[1] / "demo/12-transactions.py"),
               run_name="__main__")

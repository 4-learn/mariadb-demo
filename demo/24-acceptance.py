"""Destructive-to-versions acceptance cycle on a fresh teaching checkpoint.

Prerequisites: original sop-v1, vector DDL, initial ingest; vector_idx optional.
Successful run restores original D001 TEXT/VECTORS but leaves source_version=3.
Never run on production or pretend restored text rewinds the version counter.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_db import connect
from embedding_course import load_artifact, validate_artifact, validate_vector
from vector_course import (VersionConflict, _rows, assert_baseline, check, evaluate,
                           has_vector_index, recorded_query, search, update_document)


def snapshot(conn):
    return _rows(conn, """
        SELECT d.document_id,d.source_version AS document_version,
               c.chunk_id,c.source_version,c.text,c.content_hash,
               v.source_version AS vector_version,v.content_hash AS vector_hash,
               v.model_id,v.model_revision,v.preprocessing_id,
               HEX(v.embedding) AS vector_bytes
        FROM documents d JOIN chunks c ON c.document_id=d.document_id
        JOIN chunk_vectors v ON v.chunk_id=c.chunk_id
        ORDER BY c.chunk_id
        """)


def rejected(call, error_type):
    try:
        call()
    except error_type:
        return
    raise AssertionError(f"expected {error_type.__name__}, but operation succeeded")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config")
    parser.add_argument("--artifact", required=True)
    args = parser.parse_args()
    artifact = load_artifact(args.artifact)
    conn = connect(args.config)
    results = []
    try:
        assert_baseline(conn, artifact)
        check(conn)
        rejected(lambda: validate_vector([1.0] * 511), ValueError)
        bad = copy.deepcopy(artifact)
        bad["metadata"]["model_revision"] = "0" * 40
        rejected(lambda: validate_artifact(bad), ValueError)
        bad = copy.deepcopy(artifact)
        bad["chunks"][0]["text"] += "tampered"
        rejected(lambda: validate_artifact(bad), ValueError)
        results.append("dimension/revision/source tampering rejected")
        _, vector = recorded_query(artifact, "Q01")
        exact = search(conn, vector, k=16, category_id=1)
        assert len(exact) == 10 and len({r["chunk_id"] for r in exact}) == 10
        assert all(r["document_id"] != "D003" for r in exact)
        assert search(conn, vector, category_id=999) == []
        assert [r["chunk_id"] for r in search(conn, vector, k=16, category_id=2)] in (
            ["C003", "C004"], ["C004", "C003"])
        results.append("unique chunks / inactive / category / empty eligibility")
        plans = {"exact": search(conn, vector, explain=True)}
        if has_vector_index(conn):
            plans["ann"] = search(conn, vector, mode="ann", explain=True)
            assert not any(r.get("key") == "vector_idx" for r in plans["exact"])
            # A hinted query that does not actually use the vector index is NOT an ANN demonstration.
            assert any(r.get("key") == "vector_idx" for r in plans["ann"]), plans["ann"]
            results.append("EXPLAIN exact bypass and ANN index selected")
        else:
            results.append("ANN NOT TESTED: no vector_idx")
        evaluation = evaluate(conn, artifact)
        before = snapshot(conn)
        texts = {c["chunk_id"]: c["text"] for c in artifact["updates"]["D001"]["chunks"]}
        rejected(lambda: update_document(conn, "D001", 1, texts, prepared=artifact,
                                         fail_after_first=True), RuntimeError)
        assert snapshot(conn) == before and not conn.in_transaction
        results.append("injected failure rolled back exact bytes and versions")
        update_document(conn, "D001", 1, texts, prepared=artifact)
        after = snapshot(conn)
        own = [r for r in after if r["document_id"] == "D001"]
        assert len(own) == 2
        assert all(r["document_version"] == r["source_version"] == r["vector_version"] == 2
                   and r["text"] == texts[r["chunk_id"]] for r in own)
        assert [r for r in before if r["document_id"] != "D001"] == [
            r for r in after if r["document_id"] != "D001"]
        rejected(lambda: update_document(conn, "D001", 1, texts, prepared=artifact), VersionConflict)
        assert snapshot(conn) == after
        rejected(lambda: evaluate(conn, artifact), ValueError)
        results.append("both chunks committed at v2; stale write and v1 qrels rejected")
        original = {c["chunk_id"]: c["text"] for c in artifact["chunks"] if c["document_id"] == "D001"}
        update_document(conn, "D001", 2, original, prepared=artifact)
        restored = snapshot(conn)
        for old, new in zip(before, restored):
            assert old["text"] == new["text"]
            assert old["content_hash"] == new["content_hash"]
            assert old["vector_bytes"] == new["vector_bytes"]
            if new["document_id"] == "D001":
                assert new["document_version"] == new["source_version"] == new["vector_version"] == 3
        check(conn)
        results.append("original texts/hashes/vector bytes restored as v3, not version rewind")
        print(json.dumps({"checks": results, "plans": plans, "evaluation": evaluation,
                          "final_document_version": 3}, ensure_ascii=False, indent=2, default=str))
    finally:
        conn.close()


if __name__ == "__main__":
    main()

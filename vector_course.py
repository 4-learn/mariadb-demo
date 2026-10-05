"""MariaDB 11.8.9 teaching search; Connector/Python 1.1.14, socket only.

DDL belongs to course_editor. This module only uses course_app DML privileges.
Every public transaction function owns its transaction; pass an idle autocommit
connection from course_db.connect(), not a connection with pending application work.
"""

import argparse
import json

from embedding_course import (Encoder, MODEL_ID, PREPROCESSING_ID, REVISION,
                              load_artifact, metadata, text_hash,
                              validate_artifact, validate_vector)

INDEX_NAME = "vector_idx"
MODEL_FIELDS = (MODEL_ID, REVISION, PREPROCESSING_ID)


class VersionConflict(ValueError):
    pass


def _idle(conn):
    if not conn.autocommit or conn.in_transaction:
        raise ValueError("pass an idle autocommit=True course_db connection")


def _rows(conn, sql, params=()):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()


def has_vector_index(conn):
    rows = _rows(conn, "SHOW INDEX FROM chunk_vectors")
    return any(r["Key_name"] == INDEX_NAME for r in rows)


def check(conn):
    """Refuse a partially ingested or mixed version/hash/model checkpoint."""
    rows = _rows(conn, """
        SELECT c.chunk_id FROM chunks c
        JOIN documents d ON d.document_id=c.document_id
        LEFT JOIN chunk_vectors v ON v.chunk_id=c.chunk_id
        WHERE v.chunk_id IS NULL OR c.source_version<>d.source_version
           OR v.source_version<>c.source_version
           OR BINARY c.content_hash<>BINARY SHA2(c.text,256)
           OR BINARY v.content_hash<>BINARY c.content_hash
           OR v.model_id<>? OR v.model_revision<>? OR v.preprocessing_id<>?
        ORDER BY c.chunk_id
        """, MODEL_FIELDS)
    if rows:
        raise ValueError("inconsistent chunks: " + ",".join(r["chunk_id"] for r in rows))
    count = _rows(conn, "SELECT COUNT(*) AS chunks FROM chunk_vectors")[0]["chunks"]
    if count != 16:
        raise ValueError("expected exactly 16 vectors")
    return {"consistent": True, "chunks": count, "metadata": metadata()}


def _write_vector(cursor, chunk_id, version, content_hash, vector):
    cursor.execute("""
        INSERT INTO chunk_vectors
          (chunk_id,source_version,content_hash,model_id,model_revision,
           preprocessing_id,embedding)
        VALUES (?,?,?,?,?,?,VEC_FromText(?))
        ON DUPLICATE KEY UPDATE source_version=VALUES(source_version),
          content_hash=VALUES(content_hash), model_id=VALUES(model_id),
          model_revision=VALUES(model_revision),
          preprocessing_id=VALUES(preprocessing_id), embedding=VALUES(embedding)
        """, (chunk_id, version, content_hash, *MODEL_FIELDS,
               json.dumps(validate_vector(vector), allow_nan=False)))


def assert_baseline(conn, artifact):
    """Compare DB text, titles, status, versions and links to the exact source."""
    source = artifact["source"]
    docs = _rows(conn, "SELECT document_id,title,source_version,status FROM documents ORDER BY document_id")
    if docs != sorted(source["documents"], key=lambda d: d["document_id"]):
        raise ValueError("documents differ from artifact baseline; restore content is not version 1")
    chunks = _rows(conn, "SELECT chunk_id,document_id,source_version,text,content_hash FROM chunks ORDER BY chunk_id")
    expected = [dict(c, content_hash=text_hash(c["text"])) for c in source["chunks"]]
    if chunks != sorted(expected, key=lambda c: c["chunk_id"]):
        raise ValueError("chunks differ from artifact baseline")
    links = _rows(conn, "SELECT product_id,document_id FROM product_documents ORDER BY product_id,document_id")
    if [[r["product_id"], r["document_id"]] for r in links] != sorted(source["links"]):
        raise ValueError("links differ from artifact baseline")


def ingest(conn, artifact):
    """One atomic initial ingest. Existing vectors are an error, not overwritten."""
    validate_artifact(artifact)
    _idle(conn)
    cursor = conn.cursor()
    try:
        conn.begin()
        cursor.execute("SELECT document_id FROM documents ORDER BY document_id FOR UPDATE")
        cursor.fetchall()
        cursor.execute("SELECT chunk_id FROM chunks ORDER BY chunk_id FOR UPDATE")
        cursor.fetchall()
        assert_baseline(conn, artifact)
        cursor.execute("SELECT COUNT(*) FROM chunk_vectors")
        if cursor.fetchone()[0]:
            raise ValueError("chunk_vectors is not empty; do not overwrite an existing checkpoint")
        for chunk in artifact["chunks"]:
            _write_vector(cursor, chunk["chunk_id"], chunk["source_version"],
                          chunk["content_hash"], chunk["embedding"])
        check(conn)
        conn.commit()
        return {"inserted": len(artifact["chunks"]), "source_hash": artifact["source_hash"]}
    except BaseException:
        conn.rollback()
        raise
    finally:
        cursor.close()


def search(conn, vector, k=3, category_id=None, mode="exact", explain=False):
    """Unique eligible chunks; exact top-k or explicitly approximate ANN.

    ANN ties are sorted within returned candidates only. Its candidate boundary
    cannot promise the exact query's global chunk-ID tie breaking or recall.
    explain=True returns the actual plan rather than search rows.
    """
    validate_vector(vector)
    if type(k) is not int or not 1 <= k <= 16:
        raise ValueError("k must be an integer from 1 to 16")
    if category_id is not None and (type(category_id) is not int or category_id < 1):
        raise ValueError("category must be a positive integer")
    if mode not in ("exact", "ann"):
        raise ValueError("mode must be exact or ann")
    check(conn)
    indexed = has_vector_index(conn)
    if mode == "ann" and not indexed:
        raise ValueError("ANN requires lesson 20 vector_idx")
    hint = " FORCE INDEX (vector_idx)" if mode == "ann" else (
        " IGNORE INDEX (vector_idx)" if indexed else "")
    # No join fanout: eligibility is tested once per chunk before ORDER/LIMIT.
    sql = f"""
        SELECT v.chunk_id,c.document_id,c.text,c.source_version,
               VEC_DISTANCE_COSINE(v.embedding,VEC_FromText(?)) AS distance
        FROM chunk_vectors v{hint}
        JOIN chunks c ON c.chunk_id=v.chunk_id
        JOIN documents d ON d.document_id=c.document_id
        WHERE d.status='active'
          AND c.source_version=d.source_version AND v.source_version=c.source_version
          AND BINARY v.content_hash=BINARY c.content_hash
          AND BINARY c.content_hash=BINARY SHA2(c.text,256)
          AND v.model_id=? AND v.model_revision=? AND v.preprocessing_id=?
          AND EXISTS (
            SELECT 1 FROM product_documents pd
            JOIN products p ON p.product_id=pd.product_id
            WHERE pd.document_id=d.document_id AND p.status='active'
              AND (? IS NULL OR p.category_id=?)
          )
        ORDER BY distance ASC{" ,v.chunk_id ASC" if mode == "exact" else ""}
        LIMIT ?
        """
    rows = _rows(conn, ("EXPLAIN " if explain else "") + sql,
                 (json.dumps(vector, allow_nan=False), *MODEL_FIELDS,
                  category_id, category_id, k))
    if explain:
        return rows
    if len({r["chunk_id"] for r in rows}) != len(rows):
        raise AssertionError("duplicate chunk in search results")
    return sorted(rows, key=lambda r: (r["distance"], r["chunk_id"]))


def recorded_query(artifact, case_id):
    case = next((c for c in artifact["cases"]["cases"] if c["case_id"] == case_id), None)
    if case is None:
        raise ValueError("unknown case ID; precomputed mode cannot encode a new query")
    query = next(q for q in artifact["queries"] if q["case_id"] == case_id)
    return case, query["embedding"]


def evaluate(conn, artifact, k=3):
    """Human-authored qrels, not expected vector scores or guaranteed rankings."""
    validate_artifact(artifact)
    assert_baseline(conn, artifact)
    report = []
    for case in artifact["cases"]["cases"]:
        _, vector = recorded_query(artifact, case["case_id"])
        exact = search(conn, vector, k, case["category_id"])
        ids = [r["chunk_id"] for r in exact]
        relevant = set(case["relevant_chunk_ids"])
        hit = len(set(ids) & relevant)
        item = {"case_id": case["case_id"], "query": case["query"],
                "category_id": case["category_id"], "exact_ids": ids,
                "relevant_ids": sorted(relevant), "no_answer": not bool(relevant),
                "precision_at_k": hit / k if relevant else None,
                "recall_at_k": hit / len(relevant) if relevant else None,
                "returned_on_no_answer": len(ids) if not relevant else None}
        if has_vector_index(conn):
            ann = search(conn, vector, k, case["category_id"], mode="ann")
            ann_ids = [r["chunk_id"] for r in ann]
            item.update(ann_ids=ann_ids,
                        ann_overlap_with_exact=(len(set(ann_ids) & set(ids)) / len(ids)
                                                if ids else None))
        report.append(item)
    return {"source_hash": artifact["source_hash"], "k": k, "cases": report,
            "warning": "Distances are not probabilities; qrels do not implement automatic abstention."}


def update_document(conn, document_id, expected_version, texts, encoder=None,
                    prepared=None, fail_after_first=False):
    """Encode outside the lock; update the complete two-chunk document atomically.

    texts maps both chunk IDs to their new full text. prepared is a validated
    whole artifact; only exact matching recorded texts may reuse its vectors.
    Restoring original texts still increments the current source_version.
    """
    _idle(conn)
    if type(expected_version) is not int or expected_version < 1:
        raise ValueError("expected_version must be a positive integer")
    if len(texts) != 2 or any(not isinstance(t, str) or not t.strip() for t in texts.values()):
        raise ValueError("supply the complete document's two non-empty chunk texts")
    ids = sorted(texts)
    if prepared is not None:
        validate_artifact(prepared)
        candidates = prepared["chunks"] + [c for u in prepared["updates"].values() for c in u["chunks"]]
        vectors = []
        for chunk_id in ids:
            match = next((c for c in candidates if c["document_id"] == document_id
                          and c["chunk_id"] == chunk_id and c["text"] == texts[chunk_id]), None)
            if match is None:
                raise ValueError("new text is not recorded in the explicit precomputed artifact")
            vectors.append(match["embedding"])
    else:
        vectors = (encoder or Encoder()).encode([texts[cid] for cid in ids])
    if len(vectors) != 2:
        raise ValueError("encoder must return both vectors")
    for vector in vectors:
        validate_vector(vector)
    cursor = conn.cursor()
    try:
        conn.begin()
        cursor.execute("SELECT source_version FROM documents WHERE document_id=? FOR UPDATE",
                       (document_id,))
        row = cursor.fetchone()
        if row is None or row[0] != expected_version:
            raise VersionConflict("document version changed or document does not exist")
        cursor.execute("SELECT chunk_id FROM chunks WHERE document_id=? ORDER BY chunk_id FOR UPDATE",
                       (document_id,))
        if [r[0] for r in cursor.fetchall()] != ids:
            raise ValueError("update must cover exactly this document's two chunks")
        check(conn)
        version = expected_version + 1
        for index, (chunk_id, vector) in enumerate(zip(ids, vectors)):
            digest = text_hash(texts[chunk_id])
            cursor.execute("UPDATE chunks SET text=?,content_hash=?,source_version=? WHERE chunk_id=?",
                           (texts[chunk_id], digest, version, chunk_id))
            if cursor.rowcount != 1:
                raise ValueError("chunk update did not affect exactly one row")
            _write_vector(cursor, chunk_id, version, digest, vector)
            if fail_after_first and index == 0:
                raise RuntimeError("injected failure after first chunk/vector write")
        cursor.execute("UPDATE documents SET source_version=? WHERE document_id=? AND source_version=?",
                       (version, document_id, expected_version))
        if cursor.rowcount != 1:
            raise VersionConflict("document version changed during update")
        check(conn)
        conn.commit()
        return {"document_id": document_id, "source_version": version, "chunks": ids}
    except BaseException:
        conn.rollback()
        raise
    finally:
        cursor.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="private course_app JSON, never a command-line password")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("ingest", "evaluate", "update"):
        command = commands.add_parser(name)
        command.add_argument("--artifact", required=True)
        if name == "evaluate":
            command.add_argument("--k", type=int, default=3)
        if name == "update":
            command.add_argument("--document", default="D001")
            command.add_argument("--expected-version", required=True, type=int)
            command.add_argument("--fail-after-first", action="store_true")
    commands.add_parser("check")
    query = commands.add_parser("search")
    source = query.add_mutually_exclusive_group(required=True)
    source.add_argument("--case")
    source.add_argument("--query")
    query.add_argument("--artifact")
    query.add_argument("--offline", action="store_true")
    query.add_argument("--k", type=int, default=3)
    query.add_argument("--category", type=int)
    query.add_argument("--mode", choices=("exact", "ann"), default="exact")
    query.add_argument("--explain", action="store_true")
    args = parser.parse_args()
    artifact = load_artifact(args.artifact) if getattr(args, "artifact", None) else None
    if args.command == "search":
        if args.case:
            if artifact is None:
                parser.error("--case requires an explicit --artifact")
            case, vector = recorded_query(artifact, args.case)
            category = args.category if args.category is not None else case["category_id"]
            query_info = {"mode": "recorded-query", "case_id": args.case, "text": case["query"],
                          "artifact_source_hash": artifact["source_hash"]}
        else:
            if artifact is not None:
                parser.error("--query uses real embedding, not --artifact")
            vector = Encoder(args.offline).encode([args.query], query=True)[0]
            category = args.category
            query_info = {"mode": "live-model", "text": args.query}
    # Lazy import lets students validate artifacts before installing Connector.
    from course_db import connect

    conn = connect(args.config)
    try:
        if args.command == "ingest":
            result = ingest(conn, artifact)
        elif args.command == "check":
            result = check(conn)
        elif args.command == "evaluate":
            result = evaluate(conn, artifact, args.k)
        elif args.command == "update":
            update = artifact["updates"].get(args.document)
            if update is None or args.expected_version != update["expected_version"]:
                raise VersionConflict("recorded update requires its recorded expected version")
            result = update_document(conn, args.document, args.expected_version,
                                     {c["chunk_id"]: c["text"] for c in update["chunks"]},
                                     prepared=artifact, fail_after_first=args.fail_after_first)
        else:
            result = {"query": query_info, "metadata": metadata(), "category_id": category,
                      "search_mode": args.mode, "explain": args.explain,
                      "rows": search(conn, vector, args.k, category, args.mode, args.explain),
                      "notice": "Candidates only, not verified answers; inspect negation and model numbers."}
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str, allow_nan=False))
    finally:
        conn.close()


if __name__ == "__main__":
    main()

"""Pinned CPU BGE embeddings and an explicitly limited teaching artifact.

The Transformers CLS + L2 implementation follows the pinned model card.
No dependency on MariaDB is needed to generate or validate the artifact.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_ID = "BAAI/bge-small-zh-v1.5"
REVISION = "7999e1d3359715c523056ef9478215996d62a620"
DIMENSION = 512
QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："
PREPROCESSING_ID = "bge-zh-cls-l2-query-instruction-v1"


def metadata():
    return {"model_id": MODEL_ID, "model_revision": REVISION,
            "preprocessing_id": PREPROCESSING_ID, "dimension": DIMENSION,
            "normalize_embeddings": True, "query_prefix": QUERY_PREFIX,
            "max_tokens": 512, "pooling": "CLS", "dtype": "float32"}


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def object_hash(value):
    return text_hash(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":"), allow_nan=False))


def validate_vector(vector):
    if not isinstance(vector, list) or len(vector) != DIMENSION:
        raise ValueError("embedding must contain exactly 512 numbers")
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in vector):
        raise ValueError("embedding contains non-finite or non-numeric values")
    norm = math.sqrt(sum(x * x for x in vector))
    if abs(norm - 1.0) > 1e-4:
        raise ValueError("embedding must be L2 normalized")
    return vector


class Encoder:
    def __init__(self, offline=False):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID, revision=REVISION, local_files_only=offline,
            trust_remote_code=False)
        self.model = AutoModel.from_pretrained(
            MODEL_ID, revision=REVISION, local_files_only=offline,
            trust_remote_code=False).to("cpu").float().eval()

    def encode(self, texts, query=False):
        if not texts or any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError("encode requires non-empty text strings")
        inputs = [QUERY_PREFIX + t if query else t for t in texts]
        # Reject rather than silently hash a full text while embedding a truncated one.
        lengths = self.tokenizer(inputs, truncation=False)["input_ids"]
        if any(len(tokens) > 512 for tokens in lengths):
            raise ValueError("text exceeds 512 tokens; split it before embedding")
        result = []
        for start in range(0, len(inputs), 8):
            batch = self.tokenizer(inputs[start:start + 8], padding=True,
                                   truncation=False, return_tensors="pt")
            with self.torch.inference_mode():
                cls = self.model(**batch).last_hidden_state[:, 0]
                vectors = self.torch.nn.functional.normalize(cls, p=2, dim=1)
            result.extend(vectors.cpu().tolist())
        for vector in result:
            validate_vector(vector)
        return result


def validate_corpus(corpus):
    if corpus["dataset_version"] != "sop-v1":
        raise ValueError("expected sop-v1")
    docs = corpus["documents"]
    chunks = corpus["chunks"]
    if len(docs) != 8 or {d["document_id"] for d in docs} != {
            f"D{i:03}" for i in range(1, 9)}:
        raise ValueError("expected D001..D008 exactly once")
    if len(chunks) != 16 or {c["chunk_id"] for c in chunks} != {
            f"C{i:03}" for i in range(1, 17)}:
        raise ValueError("expected C001..C016 exactly once")
    for doc in docs:
        own = [c for c in chunks if c["document_id"] == doc["document_id"]]
        if doc["source_version"] != 1 or len(own) != 2:
            raise ValueError("baseline documents require two chunks and version 1")
        for chunk in own:
            if chunk["source_version"] != 1 or not chunk["text"].strip():
                raise ValueError("invalid baseline chunk")


def validate_artifact(artifact):
    if artifact["metadata"] != metadata() or artifact["format_version"] != 1:
        raise ValueError("artifact model/revision/preprocessing/format mismatch")
    corpus = artifact["source"]
    validate_corpus(corpus)
    if artifact["source_hash"] != object_hash(corpus):
        raise ValueError("source hash mismatch")
    if artifact["cases_hash"] != object_hash(artifact["cases"]):
        raise ValueError("search cases hash mismatch")
    baseline = {c["chunk_id"]: c for c in corpus["chunks"]}
    chunks = artifact["chunks"]
    if len(chunks) != 16 or {c["chunk_id"] for c in chunks} != set(baseline):
        raise ValueError("artifact must embed all 16 unique source chunks")
    for chunk in chunks:
        source = baseline[chunk["chunk_id"]]
        if any(chunk[key] != source[key] for key in
               ("document_id", "source_version", "text")):
            raise ValueError("chunk differs from source")
        if chunk["content_hash"] != text_hash(chunk["text"]):
            raise ValueError("chunk text/hash mismatch")
        validate_vector(chunk["embedding"])
    cases = artifact["cases"]["cases"]
    queries = artifact["queries"]
    if len(cases) < 8 or len(queries) != len(cases):
        raise ValueError("at least eight recorded cases are required")
    if len({q["case_id"] for q in cases}) != len(cases):
        raise ValueError("duplicate case ID")
    if {q["case_id"] for q in queries} != {q["case_id"] for q in cases}:
        raise ValueError("query IDs differ from annotations")
    for case in cases:
        query = next(q for q in queries if q["case_id"] == case["case_id"])
        if query["text"] != case["query"] or query["content_hash"] != text_hash(query["text"]):
            raise ValueError("query text/hash mismatch")
        if not set(case["relevant_chunk_ids"]).issubset(baseline):
            raise ValueError("unknown qrel chunk")
        validate_vector(query["embedding"])
    update = artifact["updates"]["D001"]
    if update["expected_version"] != 1 or update["source_version"] != 2:
        raise ValueError("invalid update version")
    if len(update["chunks"]) != 2 or {c["chunk_id"] for c in update["chunks"]} != {
            c["chunk_id"] for c in chunks if c["document_id"] == "D001"}:
        raise ValueError("D001 update must cover both chunks")
    for chunk in update["chunks"]:
        if chunk["document_id"] != "D001" or chunk["source_version"] != 2:
            raise ValueError("invalid update chunk identity/version")
        if chunk["content_hash"] != text_hash(chunk["text"]):
            raise ValueError("update text/hash mismatch")
        validate_vector(chunk["embedding"])
    if artifact["payload_hash"] != object_hash({k: v for k, v in artifact.items()
                                               if k != "payload_hash"}):
        raise ValueError("artifact payload hash mismatch")
    return artifact


def load_artifact(path):
    return validate_artifact(json.loads(Path(path).read_text(encoding="utf-8")))


def generate_artifact(corpus_path, cases_path, offline=False):
    raw = Path(corpus_path).read_bytes()
    corpus = json.loads(raw)
    validate_corpus(corpus)
    cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    if cases["dataset_version"] != corpus["dataset_version"]:
        raise ValueError("cases dataset version mismatch")
    encoder = Encoder(offline=offline)
    chunks = [dict(c, content_hash=text_hash(c["text"])) for c in corpus["chunks"]]
    vectors = encoder.encode([c["text"] for c in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    queries = [{"case_id": c["case_id"], "text": c["query"],
                "content_hash": text_hash(c["query"])} for c in cases["cases"]]
    for query, vector in zip(queries, encoder.encode([q["text"] for q in queries], query=True)):
        query["embedding"] = vector
    updates = []
    additions = ["第 2 版新增：完成重設後，在教學紀錄填寫操作者與日期。",
                 "第 2 版新增：若配對仍失敗，記錄指示燈狀態並交由教師檢查；不要反覆重設。"]
    for chunk, addition in zip(sorted((c for c in corpus["chunks"]
                                      if c["document_id"] == "D001"),
                                     key=lambda c: c["chunk_id"]), additions):
        text = chunk["text"] + "\n" + addition
        updates.append(dict(chunk, source_version=2, text=text, content_hash=text_hash(text)))
    for chunk, vector in zip(updates, encoder.encode([c["text"] for c in updates])):
        chunk["embedding"] = vector
    artifact = {
        "format_version": 1, "metadata": metadata(), "source": corpus,
        "source_hash": object_hash(corpus), "cases": cases, "cases_hash": object_hash(cases),
        "chunks": chunks, "queries": queries,
        "updates": {"D001": {"expected_version": 1, "source_version": 2, "chunks": updates}},
        "provenance": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_file": str(Path(corpus_path).resolve()),
            "source_file_sha256": hashlib.sha256(raw).hexdigest(),
            "implementation": "transformers AutoModel CLS pooling + torch L2 normalization",
            "device": "cpu", "offline": offline,
            "packages": {p: importlib.metadata.version(p) for p in
                         ("torch", "transformers", "huggingface-hub", "numpy")},
            "model_card": f"https://huggingface.co/{MODEL_ID}/blob/{REVISION}/README.md",
            "limitation": "Only the recorded query texts are precomputed; no arbitrary query fallback."}}
    artifact["payload_hash"] = object_hash(artifact)
    return validate_artifact(artifact)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate")
    generate.add_argument("--corpus", type=Path, default=ROOT / "data/sop_corpus.json")
    generate.add_argument("--cases", type=Path, default=ROOT / "data/search_cases.json")
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument("--offline", action="store_true")
    validate = commands.add_parser("validate")
    validate.add_argument("--artifact", type=Path, required=True)
    query = commands.add_parser("query")
    query.add_argument("--text", required=True)
    query.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.command == "generate":
        artifact = generate_artifact(args.corpus, args.cases, args.offline)
        # Refuse to silently replace a teacher's already distributed artifact.
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(artifact, handle, ensure_ascii=False, allow_nan=False, indent=2)
        print(json.dumps({"artifact": str(args.output), "source_hash": artifact["source_hash"],
                          "chunks": 16, "queries": len(artifact["queries"]), "updated_chunks": 2}))
    elif args.command == "validate":
        artifact = load_artifact(args.artifact)
        print(json.dumps({"valid": True, "metadata": artifact["metadata"],
                          "source_hash": artifact["source_hash"]}, ensure_ascii=False))
    else:
        print(json.dumps({"metadata": metadata(), "text": args.text,
                          "embedding": Encoder(args.offline).encode([args.text], query=True)[0]},
                         ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()

-- Read-only checks; writes belong to update_document's atomic transaction.
SELECT d.document_id,d.source_version AS doc_version,c.chunk_id,
       c.source_version AS chunk_version,v.source_version AS vector_version,
       c.content_hash=SHA2(c.text,256) AS text_hash_ok,
       BINARY v.content_hash=BINARY c.content_hash AS vector_hash_ok,
       v.model_id,v.model_revision,v.preprocessing_id
FROM documents d JOIN chunks c ON c.document_id=d.document_id
LEFT JOIN chunk_vectors v ON v.chunk_id=c.chunk_id
WHERE d.document_id='D001' ORDER BY c.chunk_id;

-- Baseline: two rows, all versions 1, both hash checks 1.
-- After a successful complete update: both rows have all versions 2.
-- After injected failure or stale version: same rows, hashes and versions as before.
-- After restoring original text via API: all versions 3, original hashes.

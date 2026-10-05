-- A stored real C001 vector is used as a SELF-query, not as a user query embedding.
-- Run BEFORE creating the vector index (lesson 20).
SET @q = (SELECT embedding FROM chunk_vectors WHERE chunk_id='C001');
SELECT chunk_id, VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors
ORDER BY distance ASC, chunk_id ASC LIMIT 3;

EXPLAIN SELECT chunk_id, VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors
ORDER BY distance ASC, chunk_id ASC LIMIT 3;

-- This is a raw vector-table demo, including inactive documents.
-- For eligible SOP search use vector_course.search, not this raw query.
-- After lesson 20 the explicit exact reference is:
-- SELECT chunk_id,VEC_DISTANCE_COSINE(embedding,@q) AS distance
-- FROM chunk_vectors IGNORE INDEX (vector_idx)
-- ORDER BY distance ASC,chunk_id ASC LIMIT 3;

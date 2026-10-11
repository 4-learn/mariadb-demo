-- Ch20: create the ANN index, then inspect it with SQL only.
-- Run once as course_editor after Ch18 vectors are loaded.
ALTER TABLE chunk_vectors
    ADD VECTOR INDEX vector_idx (embedding) M=6 DISTANCE=cosine;
SHOW INDEX FROM chunk_vectors;

SET @q = (SELECT embedding FROM query_vectors WHERE case_id='Q01');
EXPLAIN
SELECT chunk_id, VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors FORCE INDEX (vector_idx)
ORDER BY distance ASC LIMIT 3;

SELECT chunk_id, VEC_DISTANCE_COSINE(embedding,@q) AS distance
FROM chunk_vectors FORCE INDEX (vector_idx)
ORDER BY distance ASC LIMIT 3;

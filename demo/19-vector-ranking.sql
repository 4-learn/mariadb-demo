-- Pure SQL exact vector ranking. Query vector is teacher-precomputed Q01.
SET @q = (SELECT embedding FROM query_vectors WHERE case_id = 'Q01');
SELECT c.chunk_id,
       VEC_DISTANCE_COSINE(v.embedding, @q) AS distance
FROM chunk_vectors AS v
JOIN chunks AS c ON c.chunk_id = v.chunk_id
JOIN documents AS d ON d.document_id = c.document_id
WHERE d.status = 'active'
  AND EXISTS (
      SELECT 1
      FROM product_documents AS pd
      JOIN products AS p ON p.product_id = pd.product_id
      WHERE pd.document_id = d.document_id
        AND p.status = 'active'
        AND p.category_id = 1
  )
ORDER BY distance ASC, c.chunk_id ASC
LIMIT 3;

EXPLAIN
SELECT c.chunk_id, VEC_DISTANCE_COSINE(v.embedding, @q) AS distance
FROM chunk_vectors AS v
JOIN chunks AS c ON c.chunk_id = v.chunk_id
JOIN documents AS d ON d.document_id = c.document_id
WHERE d.status = 'active'
ORDER BY distance ASC, c.chunk_id ASC
LIMIT 3;

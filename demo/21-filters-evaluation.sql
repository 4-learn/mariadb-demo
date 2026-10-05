-- Form the unique eligible set BEFORE ranking. No LIMIT here.
SET @category = 1;
SELECT c.chunk_id,c.document_id
FROM chunks c JOIN documents d ON d.document_id=c.document_id
WHERE d.status='active' AND EXISTS (
    SELECT 1 FROM product_documents pd
    JOIN products p ON p.product_id=pd.product_id
    WHERE pd.document_id=d.document_id AND p.status='active'
      AND (@category IS NULL OR p.category_id=@category)
)
ORDER BY c.chunk_id;

-- D001 has two active linked products; it still contributes only C001/C002.
-- Category 1: C001,C002,C007,C008,C009,C010,C011,C012,C015,C016 (10 rows).
-- Category 2: C003,C004. Category 3: C013,C014. Category 999: zero rows.
SELECT d.document_id,COUNT(*) AS joined_rows
FROM documents d JOIN chunks c ON c.document_id=d.document_id
JOIN product_documents pd ON pd.document_id=d.document_id
JOIN products p ON p.product_id=pd.product_id
WHERE d.document_id='D001' AND p.status='active'
GROUP BY d.document_id;
-- joined_rows=4 demonstrates why a direct JOIN can fill top-k with duplicates.

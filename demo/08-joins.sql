USE mariadb_workshop_2026;
SET NAMES utf8mb4;
SELECT p.product_id, p.name, c.name AS category_name
FROM products AS p INNER JOIN categories AS c ON c.category_id = p.category_id
WHERE p.product_id IN ('P001', 'P004', 'P011') ORDER BY p.product_id;
SELECT p.product_id, d.document_id, d.title
FROM products AS p
INNER JOIN product_documents AS pd ON pd.product_id = p.product_id
INNER JOIN documents AS d ON d.document_id = pd.document_id
WHERE p.product_id IN ('P001', 'P010') ORDER BY p.product_id, d.document_id;
SELECT p.product_id, d.document_id
FROM products AS p
LEFT JOIN product_documents AS pd ON pd.product_id = p.product_id
LEFT JOIN documents AS d ON d.document_id = pd.document_id
WHERE p.product_id IN ('P001', 'P010') ORDER BY p.product_id, d.document_id;
-- NULL, not '= NULL', identifies the missing match.
SELECT p.product_id FROM products AS p
LEFT JOIN product_documents AS pd ON pd.product_id = p.product_id
WHERE pd.document_id IS NULL ORDER BY p.product_id;
SELECT p.product_id, d.document_id, ch.chunk_id
FROM products AS p
JOIN product_documents AS pd ON pd.product_id = p.product_id
JOIN documents AS d ON d.document_id = pd.document_id
JOIN chunks AS ch ON ch.document_id = d.document_id
WHERE p.product_id IN ('P001', 'P002') ORDER BY p.product_id, d.document_id, ch.chunk_id;
-- Expected 6 joined rows but only 4 unique chunks for these two products.

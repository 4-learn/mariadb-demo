USE mariadb_workshop_2026;
SET NAMES utf8mb4;
SELECT DATABASE() AS current_database, CURRENT_USER() AS account;
SELECT dataset_version FROM course_meta ORDER BY dataset_version;
SELECT (SELECT COUNT(*) FROM products) AS products,
       (SELECT COUNT(*) FROM documents) AS documents,
       (SELECT COUNT(*) FROM product_documents) AS links,
       (SELECT COUNT(*) FROM chunks) AS chunks;
SHOW CREATE TABLE product_documents;
SELECT product_id, document_id FROM product_documents
WHERE product_id IN ('P001', 'P010') ORDER BY product_id, document_id;
SELECT product_id, document_id FROM product_documents
WHERE document_id = 'D001' ORDER BY product_id;
SELECT chunk_id, document_id, source_version FROM chunks
WHERE document_id = 'D002' ORDER BY chunk_id;
SELECT document_id, status FROM documents WHERE document_id = 'D003';
SELECT COUNT(*) AS bad_hashes FROM chunks
WHERE BINARY content_hash <> BINARY SHA2(`text`, 256);

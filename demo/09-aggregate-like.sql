USE mariadb_workshop_2026;
SET NAMES utf8mb4;
SELECT category_id, COUNT(*) AS product_count, SUM(stock) AS total_stock,
       ROUND(AVG(price), 2) AS average_price
FROM products WHERE status = 'active'
GROUP BY category_id ORDER BY category_id;
SELECT p.product_id, COUNT(d.document_id) AS active_sops
FROM products AS p
LEFT JOIN product_documents AS pd ON pd.product_id = p.product_id
LEFT JOIN documents AS d ON d.document_id = pd.document_id AND d.status = 'active'
GROUP BY p.product_id ORDER BY p.product_id;
SELECT pd.product_id, COUNT(*) AS joined_rows, COUNT(DISTINCT pd.document_id) AS documents
FROM product_documents AS pd JOIN chunks AS ch ON ch.document_id = pd.document_id
WHERE pd.product_id = 'P001' GROUP BY pd.product_id;
SELECT chunk_id FROM chunks WHERE `text` LIKE '%重設%' ORDER BY chunk_id;
SELECT chunk_id FROM chunks WHERE `text` LIKE '%恢復出廠設定%' ORDER BY chunk_id;
SELECT chunk_id, `text` FROM chunks WHERE `text` LIKE '%支援 5 GHz%' ORDER BY chunk_id;
-- Expected groups: 1/7/67/1112.86, 2/2/13/1275.00, 3/1/30/900.00.
-- P001 has 2 active SOPs, P003/P010 have 0, others 1.
-- P001 joined_rows=4, documents=2; LIKE: C001; empty; C003,C004 (NEGATIONS).

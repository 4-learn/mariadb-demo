-- EXPECTED FAILURE ONLY. First run demo/06-insert.sql or workshop/06-insert.sql.
USE mariadb_workshop_2026;
SET NAMES utf8mb4;
START TRANSACTION;
-- P001 exists, but D999 does not exist in practice_documents_06.
-- Expected ERROR 1452, not a permissions error or missing-table error.
INSERT INTO practice_links_06 (product_id, document_id) VALUES ('P001', 'D999');
-- Batch disconnect rolls back; interactive clients must issue ROLLBACK.
ROLLBACK;

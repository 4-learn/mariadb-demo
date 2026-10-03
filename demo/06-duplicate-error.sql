-- EXPECTED FAILURE ONLY. First run demo/06-insert.sql or workshop/06-insert.sql.
USE mariadb_workshop_2026;
SET NAMES utf8mb4;
START TRANSACTION;
INSERT INTO practice_documents_06 (document_id, title) VALUES ('D901', '重複關聯測試');
-- Expected ERROR 1062. One statement is atomic in InnoDB: neither link remains.
INSERT INTO practice_links_06 (product_id, document_id) VALUES
    ('P001', 'D901'), ('P001', 'D901');
-- Batch client exits on the error; disconnect rolls back the uncommitted parent.
-- Interactive clients: issue ROLLBACK manually after observing the error.
ROLLBACK;

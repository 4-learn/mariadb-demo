USE mariadb_workshop_2026;
SET NAMES utf8mb4;
CREATE TABLE IF NOT EXISTS practice_documents_06 (
    document_id VARCHAR(16) PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    source_version INT NOT NULL DEFAULT 1 CHECK (source_version >= 1),
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active'
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS practice_links_06 (
    product_id CHAR(4) NOT NULL,
    document_id VARCHAR(16) NOT NULL,
    PRIMARY KEY (product_id, document_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (document_id) REFERENCES practice_documents_06(document_id)
) ENGINE=InnoDB;
START TRANSACTION;
INSERT INTO practice_documents_06 (document_id, title) VALUES ('D901', '課堂連線草稿');
SELECT ROW_COUNT() AS inserted_documents;
INSERT INTO practice_links_06 (product_id, document_id) VALUES
    ('P001', 'D901'), ('P002', 'D901');
SELECT ROW_COUNT() AS inserted_links;
SELECT document_id, title, source_version, status FROM practice_documents_06 ORDER BY document_id;
SELECT product_id, document_id FROM practice_links_06 ORDER BY product_id, document_id;
ROLLBACK;
SELECT (SELECT COUNT(*) FROM practice_documents_06) AS documents_after,
       (SELECT COUNT(*) FROM practice_links_06) AS links_after;
-- Expected 1, 2; D901/version 1/active; two links; final 0/0.

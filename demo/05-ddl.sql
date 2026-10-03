USE mariadb_workshop_2026;
SET NAMES utf8mb4;
-- DDL persists. IF NOT EXISTS supports reruns, not schema migration/validation.
CREATE TABLE IF NOT EXISTS practice_documents_05 (
    document_id VARCHAR(16) PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    source_version INT NOT NULL DEFAULT 1 CHECK (source_version >= 1),
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active'
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS practice_links_05 (
    product_id CHAR(4) NOT NULL,
    document_id VARCHAR(16) NOT NULL,
    PRIMARY KEY (product_id, document_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (document_id) REFERENCES practice_documents_05(document_id)
) ENGINE=InnoDB;
ALTER TABLE practice_documents_05
    ADD COLUMN IF NOT EXISTS note VARCHAR(200) NULL;
SHOW COLUMNS FROM practice_documents_05;
SHOW CREATE TABLE practice_links_05;
SELECT COUNT(*) AS practice_rows FROM practice_documents_05;

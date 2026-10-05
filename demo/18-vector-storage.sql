-- Run ONCE with course_editor, in mariadb_workshop_2026, after sop-v1 seed.
-- No IF NOT EXISTS: an unexpected existing definition must not be hidden.
CREATE TABLE chunk_vectors (
    chunk_id VARCHAR(16) PRIMARY KEY,
    source_version INT NOT NULL,
    content_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    model_id VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    model_revision CHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    preprocessing_id VARCHAR(80) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    embedding VECTOR(512) NOT NULL,
    CONSTRAINT fk_vector_chunk FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id),
    CONSTRAINT chk_vector_version CHECK (source_version > 0)
) ENGINE=InnoDB;

SHOW CREATE TABLE chunk_vectors;

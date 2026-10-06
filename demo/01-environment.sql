-- Run after logging in as course_reader to mariadb_course.
SELECT VERSION() AS server_version,
       DATABASE() AS current_database,
       CURRENT_USER() AS account;

SHOW TABLES;

SELECT TABLE_NAME,
       ORDINAL_POSITION,
       COLUMN_NAME,
       COLUMN_TYPE,
       IS_NULLABLE,
       COLUMN_KEY
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT * FROM course_meta;

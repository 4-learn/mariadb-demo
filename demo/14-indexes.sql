-- Run as course_editor, never course_app. DDL is not rollback-able.
CREATE TABLE IF NOT EXISTS practice_index_products LIKE products;
DELETE FROM practice_index_products;
INSERT INTO practice_index_products SELECT * FROM products WHERE product_id < 'P900';
-- Before: IGNORE ensures repeat runs still offer a table-scan comparison.
CREATE INDEX IF NOT EXISTS idx_practice_category_status_price
    ON practice_index_products(category_id, status, price, product_id);
EXPLAIN SELECT product_id, price FROM practice_index_products
    IGNORE INDEX (idx_practice_category_status_price)
    WHERE category_id = 1 AND status = 'active' AND price BETWEEN 700 AND 1300
    ORDER BY price, product_id LIMIT 3;
EXPLAIN SELECT product_id, price FROM practice_index_products
    WHERE category_id = 1 AND status = 'active' AND price BETWEEN 700 AND 1300
    ORDER BY price, product_id LIMIT 3;
SHOW INDEX FROM practice_index_products;
SELECT product_id, price FROM practice_index_products
    WHERE category_id = 1 AND status = 'active' AND price BETWEEN 700 AND 1300
    ORDER BY price, product_id LIMIT 3;

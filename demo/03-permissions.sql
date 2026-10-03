-- Run as course_reader, NOT root. This file must fail with ERROR 1142.
SELECT product_id, stock FROM products WHERE product_id = 'P001';
UPDATE products SET stock = stock + 1 WHERE product_id = 'P001';
-- The batch client stops here. Reconnect and SELECT again to verify stock = 10.

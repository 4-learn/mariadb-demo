USE mariadb_workshop_2026;
SET NAMES utf8mb4;
CREATE TABLE IF NOT EXISTS practice_inventory_07 (
    product_id CHAR(4) PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    stock INT UNSIGNED NOT NULL,
    status ENUM('active', 'inactive') NOT NULL
) ENGINE=InnoDB;
START TRANSACTION;
INSERT INTO practice_inventory_07 (product_id, name, stock, status) VALUES
    ('P901', '練習感測器', 10, 'active'), ('P902', '練習配件', 3, 'active');
SELECT product_id, stock FROM practice_inventory_07 WHERE product_id = 'P901' AND stock >= 2;
UPDATE practice_inventory_07 SET stock = stock - 2 WHERE product_id = 'P901' AND stock >= 2;
SELECT ROW_COUNT() AS changed_rows;
SELECT product_id, stock FROM practice_inventory_07 ORDER BY product_id;
UPDATE practice_inventory_07 SET status = 'inactive' WHERE product_id = 'P902' AND status = 'active';
SELECT ROW_COUNT() AS deactivated_rows;
SELECT product_id, status FROM practice_inventory_07 WHERE product_id = 'P902' AND status = 'inactive';
DELETE FROM practice_inventory_07 WHERE product_id = 'P902' AND status = 'inactive';
SELECT ROW_COUNT() AS deleted_rows;
SELECT product_id, stock, status FROM practice_inventory_07 ORDER BY product_id;
ROLLBACK;
SELECT COUNT(*) AS remaining_rows FROM practice_inventory_07;
-- Expected preview P901/10; changed 1; stocks P901/8,P902/3;
-- deactivated 1; deleted 1; only P901/8/active; remaining_rows=0.

-- Synthetic teaching data only. Run through prepare_lab.py, not by hand.
-- Existing databases must fail rather than being dropped or overwritten.
CREATE DATABASE mariadb_course CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mariadb_course;

CREATE TABLE course_meta (
    dataset_version VARCHAR(40) PRIMARY KEY
) ENGINE=InnoDB;
INSERT INTO course_meta VALUES ('products-v1');

CREATE TABLE categories (
    category_id INT PRIMARY KEY,
    name VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE products (
    product_id CHAR(4) PRIMARY KEY,
    category_id INT NOT NULL,
    name VARCHAR(80) NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    stock INT UNSIGNED NOT NULL,
    status ENUM('active', 'inactive') NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
) ENGINE=InnoDB;

INSERT INTO categories VALUES (1, '感測器'), (2, '網關'), (3, '配件');
INSERT INTO products (product_id, name, category_id, price, stock, status) VALUES
    ('P001', '教學感測器 A', 1, 800.00, 10, 'active'),
    ('P002', '教學感測器 B', 1, 1200.00, 20, 'active'),
    ('P003', '教學感測器 C', 1, 1500.00, 0, 'inactive'),
    ('P004', '教學網關 A', 2, 1800.00, 5, 'active'),
    ('P005', '教學網關 B', 2, 750.00, 8, 'active'),
    ('P006', '教學感測器 D', 1, 780.00, 0, 'inactive'),
    ('P007', '教學感測器 E', 1, 650.00, 9, 'active'),
    ('P008', '教學感測器 F', 1, 1250.00, 7, 'active'),
    ('P009', '教學感測器 G', 1, 1350.00, 6, 'active'),
    ('P010', '教學感測器 H', 1, 1250.00, 11, 'active'),
    ('P011', '教學配件 A', 3, 900.00, 30, 'active'),
    ('P012', '教學感測器 I', 1, 1290.00, 4, 'active');

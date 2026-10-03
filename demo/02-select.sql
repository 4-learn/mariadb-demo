SELECT product_id, name, category_id, price, stock, status
FROM products
ORDER BY product_id;

SELECT product_id, name, price
FROM products
WHERE category_id = 1
  AND status = 'active'
  AND price >= 700
  AND price <= 1300
ORDER BY price ASC, product_id ASC
LIMIT 2;

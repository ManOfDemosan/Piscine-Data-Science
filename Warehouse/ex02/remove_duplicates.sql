CREATE TABLE temp_customers AS
SELECT DISTINCT ON (event_time, event_type, product_id, price, user_id, user_session) 
    event_time,
    event_type,
    product_id,
    price,
    user_id,
    user_session
FROM customers;

TRUNCATE TABLE customers;

INSERT INTO customers
SELECT * FROM temp_customers;

DROP TABLE temp_customers; 
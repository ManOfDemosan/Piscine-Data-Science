-- Remove duplicate rows from customers table
-- Create a temporary table with distinct rows
CREATE TABLE temp_customers AS
SELECT DISTINCT ON (event_time, event_type, product_id, price, user_id, user_session) 
    event_time,
    event_type,
    product_id,
    price,
    user_id,
    user_session
FROM customers;

-- Delete all rows from the original table
TRUNCATE TABLE customers;

-- Copy back the distinct rows
INSERT INTO customers
SELECT * FROM temp_customers;

-- Drop the temporary table
DROP TABLE temp_customers; 

/*
     psql -U jaehwkim -d piscineds -f ex02/remove_duplicates.sql
*/
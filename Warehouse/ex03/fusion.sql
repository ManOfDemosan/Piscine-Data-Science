-- Step 1: Drop tables if they exist to start fresh
DROP TABLE IF EXISTS customers_with_items;
DROP TABLE IF EXISTS items;

-- Step 2: Create items table
CREATE TABLE items (
    product_id INTEGER PRIMARY KEY,
    category_id BIGINT,
    category_code VARCHAR(255),
    brand VARCHAR(255)
);

-- Step 3: Create a temporary table to load data first
CREATE TEMP TABLE temp_items (
    product_id INTEGER,
    category_id BIGINT,
    category_code VARCHAR(255),
    brand VARCHAR(255)
);

-- Load data into temp table
\copy temp_items FROM '/Users/jaehwankim/Piscine-Data-Science/Warehouse/item.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',')

-- Insert distinct records into items table
INSERT INTO items
SELECT DISTINCT ON (product_id) 
    product_id, 
    category_id, 
    category_code, 
    brand
FROM temp_items;

-- Step 4: Create a new table that joins customers and items
CREATE TABLE customers_with_items AS
SELECT 
    c.event_time,
    c.event_type,
    c.product_id,
    c.price,
    c.user_id,
    c.user_session,
    i.category_id,
    i.category_code,
    i.brand
FROM 
    customers c
LEFT JOIN 
    items i ON c.product_id = i.product_id;

-- Grant permissions
GRANT ALL PRIVILEGES ON customers_with_items TO jaehwkim;
GRANT ALL PRIVILEGES ON items TO jaehwkim;

/*
   psql -U jaehwkim -d piscineds -f ex03/fusion.sql
*/
-- Step 1: Drop items table if it exists to start fresh
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
\copy temp_items FROM '/csv_data/subject/item/item.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',')

-- Insert distinct records into items table
INSERT INTO items
SELECT DISTINCT ON (product_id) 
    product_id, 
    category_id, 
    category_code, 
    brand
FROM temp_items;

-- Step 4: Alter customers table to add new columns from items
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS category_id BIGINT,
ADD COLUMN IF NOT EXISTS category_code VARCHAR(255),
ADD COLUMN IF NOT EXISTS brand VARCHAR(255);

-- Step 5: Update customers table with data from items
UPDATE customers c
SET 
    category_id = i.category_id,
    category_code = i.category_code,
    brand = i.brand
FROM 
    items i
WHERE 
    c.product_id = i.product_id;

-- Grant permissions
GRANT ALL PRIVILEGES ON items TO jaehwkim;

-- Create customers table with the same structure as data_2023_feb
CREATE TABLE IF NOT EXISTS customers (
    event_time TIMESTAMP,
    event_type VARCHAR(255),
    product_id INTEGER,
    price DECIMAL,
    user_id INTEGER,
    user_session VARCHAR(255)
);

-- Insert data from data_2023_feb into customers
INSERT INTO customers
SELECT * FROM data_2023_febㅇ;

/*
   psql -U jaehwkim -d piscineds -f ex01/customers_table.sql
*/
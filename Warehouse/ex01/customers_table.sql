CREATE TABLE IF NOT EXISTS customers (
    event_time TIMESTAMP,
    event_type VARCHAR(255),
    product_id INTEGER,
    price DECIMAL,
    user_id INTEGER,
    user_session VARCHAR(255)
);

TRUNCATE TABLE customers;
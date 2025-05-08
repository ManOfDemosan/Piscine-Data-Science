-- Create tables for each CSV file with proper data types
-- First column must be DATETIME

-- Table for data_2022_oct
CREATE TABLE IF NOT EXISTS data_2022_oct (
    event_time TIMESTAMP, -- DATETIME as first column
    event_type VARCHAR(50),
    product_id VARCHAR(50),
    price NUMERIC(10,2),
    user_id BIGINT,
    user_session UUID
);

-- Table for data_2022_nov
CREATE TABLE IF NOT EXISTS data_2022_nov (
    event_time TIMESTAMP, -- DATETIME as first column
    event_type VARCHAR(50),
    product_id VARCHAR(50),
    price NUMERIC(10,2),
    user_id BIGINT,
    user_session UUID
);

-- Table for data_2022_dec
CREATE TABLE IF NOT EXISTS data_2022_dec (
    event_time TIMESTAMP, -- DATETIME as first column
    event_type VARCHAR(50),
    product_id VARCHAR(50),
    price NUMERIC(10,2),
    user_id BIGINT,
    user_session UUID
);

-- Table for data_2023_jan
CREATE TABLE IF NOT EXISTS data_2023_jan (
    event_time TIMESTAMP, -- DATETIME as first column
    event_type VARCHAR(50),
    product_id VARCHAR(50),
    price NUMERIC(10,2),
    user_id BIGINT,
    user_session UUID
); 
CREATE TABLE data_2023_feb (
    event_time TIMESTAMP,
    event_type VARCHAR(255),
    product_id INTEGER,
    price DECIMAL,
    user_id INTEGER,
    user_session VARCHAR(255)
);


/*
psql -U jaehwkim  -d piscineds -c "\COPY data_2023_feb FROM '/Users/jaehwankim/Piscine-Data-Science/Warehouse/data_2023_feb.csv' WITH CSV HEADER"
COPY 4156682
*/
#!/bin/bash

# database config
DB_NAME="piscineds"
DB_USER="jaehwkim"
DB_PASSWORD="postgres"
DB_HOST="localhost"



# items table
echo "Creating items table..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS items (
    product_id INT,
    category_id BIGINT,
    category_code VARCHAR(100),
    brand VARCHAR(100)
);"

# CSV PATH
ITEM_CSV="../subject/item/item.csv"

# import csv to table
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\COPY items FROM '$ITEM_CSV' WITH (FORMAT csv, HEADER true);"

echo "Items table created and data imported successfully!" 
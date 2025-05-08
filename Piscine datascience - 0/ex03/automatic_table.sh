#!/bin/bash

# database config
DB_NAME="piscineds"
DB_USER="jaehwkim"
DB_PASSWORD="postgres"
DB_HOST="localhost"


# create table using ex02/table.sql
echo "Creating tables using ex02/table.sql..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f "../ex02/table.sql"

# CSV PATH
CSV_DIR="../subject/customer"

# import csv to table
for CSV_FILE in "$CSV_DIR"/*.csv; do
    FILENAME=$(basename "$CSV_FILE")
    TABLE_NAME="${FILENAME%.*}"
    
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\COPY $TABLE_NAME FROM '$CSV_FILE' WITH (FORMAT csv, HEADER true);"
done

echo "All tables created and data imported successfully!" 
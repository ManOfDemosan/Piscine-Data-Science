#!/bin/bash

set -e

echo "--- Starting customers table creation and data loading ---"

DB_USER="jaehwkim"
DB_NAME="piscineds"
DB_CONTAINER="postgresForDb" 
DB_PASSWORD="mysecretpassword" 

CONTAINER_PROJECT_ROOT_MOUNT_PATH="/csv_data"
CSV_HOST_DIR="../subject/customer"
CSV_CONTAINER_DIR="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/subject/customer"

echo "--- Creating customers table ---"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\"" << EOF
CREATE TABLE IF NOT EXISTS customers (
    event_time TIMESTAMP,
    event_type VARCHAR(255),
    product_id INTEGER,
    price DECIMAL,
    user_id INTEGER,
    user_session VARCHAR(255)
);

TRUNCATE TABLE customers;
EOF

echo "Customers table created successfully."

echo "--- Importing data from CSV files directly into customers table ---"

TEMP_COPY_SQL_HOST="temp_customers_import.sql"
> "$TEMP_COPY_SQL_HOST"

CSV_FILES=(
  "data_2022_oct.csv"
  "data_2022_nov.csv"
  "data_2022_dec.csv"
  "data_2023_jan.csv"
  "data_2023_feb.csv"
)

for FILENAME in "${CSV_FILES[@]}"; do
    CSV_CONTAINER_FILE_PATH="${CSV_CONTAINER_DIR}/${FILENAME}"
    
    echo "\\echo 'Loading ${FILENAME} into customers table...'" >> "$TEMP_COPY_SQL_HOST"
    echo "\\copy customers FROM '${CSV_CONTAINER_FILE_PATH}' WITH (FORMAT csv, HEADER true);" >> "$TEMP_COPY_SQL_HOST"
    echo "-> Command generated for ${FILENAME}"
done

echo "--- Running import commands inside container ---"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\"" < "$TEMP_COPY_SQL_HOST"

if [ $? -eq 0 ]; then
  echo "--- All data imported successfully into customers table ---"
  echo "--- Checking row count of customers table ---"
  
  docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT COUNT(*) AS total_rows FROM customers;\""
else
  echo "--- Error occurred during data import ---"
  exit 1
fi

echo "--- Cleaning up temporary script file ---"
rm "$TEMP_COPY_SQL_HOST"
echo "Temporary script file cleanup complete."

echo "--- Script execution complete ---"
exit 0 
#!/bin/bash

# 스크립트 실행 중 오류 발생 시 즉시 중단
set -e

echo "--- Starting creation and import for items table ---"

DB_USER="jaehwkim"
DB_NAME="piscineds"
DB_CONTAINER="postgresForDb" 
DB_PASSWORD="mysecretpassword" 


ITEM_CSV_HOST_PATH="../subject/item/item.csv" 

CONTAINER_PROJECT_ROOT_MOUNT_PATH="/csv_data" 

ITEM_CSV_CONTAINER_PATH="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/subject/item/item.csv"


echo "--- Creating items table ---"
PGPASSWORD="$DB_PASSWORD" docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
CREATE TABLE IF NOT EXISTS items (
    product_id INT,
    category_id BIGINT,
    category_code VARCHAR(100),
    brand VARCHAR(100)
);"
echo "Items table created (skipped if already exists)."


echo "--- Importing data from ${ITEM_CSV_HOST_PATH} ---"

TEMP_COPY_SQL_HOST="temp_item_import_command.sql"
echo "\\copy items FROM '${ITEM_CSV_CONTAINER_PATH}' WITH (FORMAT csv, HEADER true);" > "$TEMP_COPY_SQL_HOST"

echo "--- Running import command inside container (using \\copy) ---"
PGPASSWORD="$DB_PASSWORD" docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$TEMP_COPY_SQL_HOST"
echo "Data imported into items table."

echo "--- Checking row count in items table ---"
PGPASSWORD="$DB_PASSWORD" docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) FROM items;"


echo "--- Cleaning up temporary script file (host) ---"
rm "$TEMP_COPY_SQL_HOST"
echo "Temporary script file cleanup complete."

echo "--- Script execution complete ---"
exit 0
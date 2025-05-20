#!/bin/bash

set -e

echo "--- Starting fusion of customers and items data ---"

DB_USER="jaehwkim"
DB_NAME="piscineds"
DB_CONTAINER="postgresForDb" 
DB_PASSWORD="mysecretpassword" 

CONTAINER_PROJECT_ROOT_MOUNT_PATH="/csv_data"
SQL_HOST_PATH="./ex03/fusion.sql"
SQL_CONTAINER_PATH="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/ex03/fusion.sql"

echo "--- Checking if customers table exists ---"
CUSTOMERS_COUNT=$(docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -t -c \"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers';\"")

if [ "$CUSTOMERS_COUNT" -eq 0 ]; then
  echo "!!! Error: customers table doesn't exist. Please create it first !!!"
  exit 1
fi

echo "--- Running fusion SQL script ---"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -f \"$SQL_CONTAINER_PATH\""

if [ $? -eq 0 ]; then
  echo "--- Fusion completed successfully ---"
  echo "--- Checking tables and row counts ---"
  
  echo "--- Items table count ---"
  docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT COUNT(*) AS items_count FROM items;\""
  
  echo "--- Customers table count (with item data) ---"
  docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT COUNT(*) AS customers_count FROM customers;\""
  
  echo "--- Sample data from updated customers table (first 5 rows) ---"
  docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT * FROM customers LIMIT 5;\""
else
  echo "--- Error occurred during fusion ---"
  exit 1
fi

echo "--- Script execution complete ---"
exit 0 
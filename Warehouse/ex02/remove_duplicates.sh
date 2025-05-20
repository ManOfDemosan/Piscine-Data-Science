#!/bin/bash

set -e

echo "--- Starting duplicate removal from customers table ---"

DB_USER="jaehwkim"
DB_NAME="piscineds"
DB_CONTAINER="postgresForDb" 
DB_PASSWORD="mysecretpassword" 

CONTAINER_PROJECT_ROOT_MOUNT_PATH="/csv_data"
SQL_HOST_PATH="./ex02/remove_duplicates.sql"
SQL_CONTAINER_PATH="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/ex02/remove_duplicates.sql"

echo "--- Getting row count before duplicate removal ---"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT COUNT(*) AS total_rows_before FROM customers;\""

echo "--- Running duplicate removal SQL script ---"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -f \"$SQL_CONTAINER_PATH\""

if [ $? -eq 0 ]; then
  echo "--- Duplicate removal completed successfully ---"
  echo "--- Getting row count after duplicate removal ---"
  docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT COUNT(*) AS total_rows_after FROM customers;\""
else
  echo "--- Error occurred during duplicate removal ---"
  exit 1
fi

echo "--- Script execution complete ---"
exit 0 
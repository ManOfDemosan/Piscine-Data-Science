#!/bin/bash

DB_USER="jaehwkim"
DB_NAME="piscineds"
DB_PASSWORD="mysecretpassword"
CONTAINER_NAME="postgresForDb"

echo "--- Creating tables ---"

docker exec -i $CONTAINER_NAME bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U $DB_USER -d $DB_NAME" < $(dirname "$0")/table.sql

if [ $? -eq 0 ]; then
  echo "Tables created successfully."
else
  echo "Error occurred while creating tables."
fi 
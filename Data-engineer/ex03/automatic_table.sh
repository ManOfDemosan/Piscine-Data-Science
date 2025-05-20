#!/bin/bash

set -e

echo "--- Starting initial database setup and load ---"

DB_USER="jaehwkim"
DB_NAME="piscineds"
DB_CONTAINER="postgresForDb" 
DB_PASSWORD="mysecretpassword" 

CONTAINER_PROJECT_ROOT_MOUNT_PATH="/csv_data" 

TABLE_SQL_HOST_PATH="./ex02/table.sql" 
CSV_HOST_DIR="../subject/customer" 

TABLE_SQL_CONTAINER_PATH="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/ex02/table.sql"

CSV_CONTAINER_DIR="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/subject/customer"


echo "--- Creating tables (using ${TABLE_SQL_HOST_PATH}) ---"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -f \"$TABLE_SQL_CONTAINER_PATH\""
echo "Tables created (skipped if already exist)."


echo "--- Importing data from CSV files (${CSV_HOST_DIR}) ---"

TEMP_COPY_SQL_HOST="temp_import_commands.sql"
> "$TEMP_COPY_SQL_HOST" 

echo "--- Generating import commands ---"
find "$CSV_HOST_DIR" -maxdepth 1 -name "*.csv" -print0 | while IFS= read -r -d $'\0' CSV_HOST_FILE; do
    FILENAME=$(basename "$CSV_HOST_FILE") 
    TABLE_NAME="${FILENAME%.*}"         
    
    CSV_CONTAINER_FILE_PATH="${CSV_CONTAINER_DIR}/${FILENAME}"

    echo "\\copy ${TABLE_NAME} FROM '${CSV_CONTAINER_FILE_PATH}' WITH (FORMAT csv, HEADER true);" >> "$TEMP_COPY_SQL_HOST"
    echo "-> Command generated: ${FILENAME} -> ${TABLE_NAME}"
done

echo "--- Generated import script content (host temp file: ${TEMP_COPY_SQL_HOST}) ---"
cat "$TEMP_COPY_SQL_HOST"
echo "-------------------------------------"

echo "--- Running import commands inside container ---"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\"" < "$TEMP_COPY_SQL_HOST"

if [ $? -eq 0 ]; then
  echo "--- All table data imported successfully ---"
  echo "--- Checking row count for each table ---"
  VERIFY_TABLES=()
  find "$CSV_HOST_DIR" -maxdepth 1 -name "*.csv" -print0 | while IFS= read -r -d $'\0' CSV_HOST_FILE; do
      FILENAME=$(basename "$CSV_HOST_FILE")
      VERIFY_TABLES+=("${FILENAME%.*}")
  done

  if [ ${#VERIFY_TABLES[@]} -gt 0 ]; then
      VERIFY_SQL="SELECT table_name, pg_relation_size(table_name) AS total_bytes, pg_class.reltuples AS estimated_rows FROM pg_tables JOIN pg_class ON pg_tables.tablename = pg_class.relname WHERE schemaname = 'public' AND tablename IN ("
      for i in "${!VERIFY_TABLES[@]}"; do
          VERIFY_SQL+="'${VERIFY_TABLES[$i]}'"
          if [[ $i -lt $((${#VERIFY_TABLES[@]} - 1)) ]]; then
              VERIFY_SQL+=", "
          fi
      done
      VERIFY_SQL+=");"

      docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"$VERIFY_SQL\""
  else
      echo "No CSV files found to verify."
  fi
else
  echo "--- Error occurred during data import ---"
  exit 1
fi

echo "--- Cleaning up temporary script file (host) ---"
rm "$TEMP_COPY_SQL_HOST"
echo "Temporary script file cleanup complete."

echo "--- Script execution complete ---"
exit 0
#!/bin/bash

# 데이터베이스 연결 정보
DB_NAME="piscineds"
DB_USER="jaehwkim"
DB_PASSWORD="mysecretpassword"
DB_HOST="localhost"

# 테이블 생성 스크립트 실행
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f table.sql

# CSV 파일 위치
CSV_DIR="../Piscine datascience - 0/subject/customer"

# 각 CSV 파일을 해당 테이블로 가져오기
echo "Importing data_2022_oct.csv..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\COPY data_2022_oct FROM '$CSV_DIR/data_2022_oct.csv' DELIMITER ',' CSV HEADER;"

echo "Importing data_2022_nov.csv..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\COPY data_2022_nov FROM '$CSV_DIR/data_2022_nov.csv' DELIMITER ',' CSV HEADER;"

echo "Importing data_2022_dec.csv..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\COPY data_2022_dec FROM '$CSV_DIR/data_2022_dec.csv' DELIMITER ',' CSV HEADER;"

echo "Importing data_2023_jan.csv..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\COPY data_2023_jan FROM '$CSV_DIR/data_2023_jan.csv' DELIMITER ',' CSV HEADER;"

echo "Import completed!"
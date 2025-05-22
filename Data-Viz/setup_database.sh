#!/bin/bash

set -e

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 작업 디렉토리 설정
WORKSPACE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$WORKSPACE_DIR"

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}데이터베이스 초기화 및 데이터 로드 통합 스크립트${NC}"
echo -e "${BLUE}=========================================${NC}"

# 데이터베이스 연결 설정
DB_USER="jaehwkim"
DB_NAME="piscineds"
DB_CONTAINER="postgresForDb" 
DB_PASSWORD="mysecretpassword" 
CONTAINER_PROJECT_ROOT_MOUNT_PATH="/csv_data"

# Docker 컨테이너 상태 확인 및 시작
echo -e "\n${YELLOW}1. Docker 컨테이너 상태 확인 및 시작${NC}"
if [ "$(docker ps -q -f name=$DB_CONTAINER)" ]; then
    echo "PostgreSQL 컨테이너가 이미 실행 중입니다."
else
    echo "PostgreSQL 컨테이너를 시작합니다..."
    docker-compose up -d
    
    # 데이터베이스 초기화 대기
    echo "데이터베이스 초기화 대기 중... (10초)"
    sleep 10
fi

# 1. customers 테이블 생성 및 데이터 로드
echo -e "\n${YELLOW}2. customers 테이블 생성 및 데이터 로드${NC}"
echo "테이블 생성 중..."

# customers 테이블 생성
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

echo "customers 테이블이 생성되었습니다."

# CSV 파일 목록
CSV_FILES=(
  "data_2022_oct.csv"
  "data_2022_nov.csv"
  "data_2022_dec.csv"
  "data_2023_jan.csv"
  "data_2023_feb.csv"
)

# 임시 SQL 파일 생성
TEMP_COPY_SQL="$WORKSPACE_DIR/temp_import_commands.sql"
> "$TEMP_COPY_SQL"

# 각 CSV 파일에 대한 import 명령 생성
echo "데이터 로드 명령 생성 중..."
for FILENAME in "${CSV_FILES[@]}"; do
    CSV_CONTAINER_PATH="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/subject/customer/${FILENAME}"
    
    echo "\\echo '${FILENAME} 로드 중...'" >> "$TEMP_COPY_SQL"
    echo "\\copy customers(event_time, event_type, product_id, price, user_id, user_session) FROM '${CSV_CONTAINER_PATH}' WITH (FORMAT csv, HEADER true);" >> "$TEMP_COPY_SQL"
    echo "-> ${FILENAME} 로드 명령 생성 완료"
done

# 데이터 로드 실행
echo "데이터 로드 중..."
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\"" < "$TEMP_COPY_SQL"

# 로드된 데이터 확인
echo "로드된 데이터 확인 중..."
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT COUNT(*) AS total_rows FROM customers;\""

# 임시 파일 삭제
rm "$TEMP_COPY_SQL"

# 2. 중복 데이터 제거
echo -e "\n${YELLOW}3. 중복 데이터 제거${NC}"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\"" << EOF
-- 중복 행 제거를 위한 임시 테이블 생성
CREATE TABLE temp_customers AS
SELECT DISTINCT ON (event_time, event_type, product_id, price, user_id, user_session) 
    event_time,
    event_type,
    product_id,
    price,
    user_id,
    user_session
FROM customers;

-- 원본 테이블 비우기
TRUNCATE TABLE customers;

-- 중복이 제거된 데이터 복사
INSERT INTO customers
SELECT * FROM temp_customers;

-- 임시 테이블 삭제
DROP TABLE temp_customers;
EOF

# 중복 제거 후 행 수 확인
echo "중복 제거 후 행 수 확인 중..."
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT COUNT(*) AS total_rows_after_dedup FROM customers;\""

# 3. items 테이블 생성 및 customers 테이블과 통합
echo -e "\n${YELLOW}4. items 테이블 생성 및 customers 테이블과 통합${NC}"

# items 테이블 생성 및 데이터 로드
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\"" << EOF
-- items 테이블 생성
DROP TABLE IF EXISTS items;

CREATE TABLE items (
    product_id INTEGER PRIMARY KEY,
    category_id BIGINT,
    category_code VARCHAR(255),
    brand VARCHAR(255)
);

-- 임시 테이블 생성
CREATE TEMP TABLE temp_items (
    product_id INTEGER,
    category_id BIGINT,
    category_code VARCHAR(255),
    brand VARCHAR(255)
);

-- item.csv 파일에서 데이터 로드
\copy temp_items FROM '${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/subject/item/item.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',')

-- 고유한 product_id만 items 테이블에 삽입
INSERT INTO items
SELECT DISTINCT ON (product_id) 
    product_id, 
    category_id, 
    category_code, 
    brand
FROM temp_items;
EOF

# items 테이블 행 수 확인
echo "items 테이블 행 수 확인 중..."
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT COUNT(*) AS items_count FROM items;\""

# customers 테이블에 items 데이터 통합
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\"" << EOF
-- customers 테이블에 items 컬럼 추가
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS category_id BIGINT,
ADD COLUMN IF NOT EXISTS category_code VARCHAR(255),
ADD COLUMN IF NOT EXISTS brand VARCHAR(255);

-- items 데이터로 customers 테이블 업데이트
UPDATE customers c
SET 
    category_id = i.category_id,
    category_code = i.category_code,
    brand = i.brand
FROM 
    items i
WHERE 
    c.product_id = i.product_id;
EOF

# 통합 결과 확인
echo "customers 테이블 확인 중..."
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT COUNT(*) AS rows_with_category FROM customers WHERE category_id IS NOT NULL;\""

echo -e "\n${GREEN}데이터베이스 설정이 완료되었습니다!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo "- 테이블 customers: 모든 고객 이벤트 데이터"
echo "- 테이블 items: 상품 정보"
echo -e "${BLUE}=========================================${NC}"

# 월별 데이터 확인 (디버깅용)
echo -e "\n${YELLOW}5. 월별 데이터 확인${NC}"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT TO_CHAR(event_time, 'YYYY-MM') as month, COUNT(*) as count FROM customers GROUP BY month ORDER BY month;\""

# 이벤트 타입별 데이터 확인
echo -e "\n${YELLOW}6. 이벤트 타입별 데이터 확인${NC}"
docker exec -i "$DB_CONTAINER" bash -c "PGPASSWORD=\"$DB_PASSWORD\" psql -U \"$DB_USER\" -d \"$DB_NAME\" -c \"SELECT event_type, COUNT(*) as count FROM customers GROUP BY event_type ORDER BY count DESC;\"" 
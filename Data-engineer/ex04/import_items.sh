#!/bin/bash

# 스크립트 실행 중 오류 발생 시 즉시 중단
set -e

echo "--- items 테이블 생성 및 데이터 임포트 시작 ---"

# 데이터베이스 연결 정보
DB_USER="jaehwkim"
DB_NAME="piscineds"
DB_CONTAINER="postgresForDb" # 실행 중인 PostgreSQL 컨테이너 이름 (여러분의 컨테이너 이름과 일치해야 함)
DB_PASSWORD="mysecretpassword" # **### 중요: 여러분의 실제 PostgreSQL 비밀번호로 변경하세요! ###**

# 이 스크립트는 ex04/ 디렉토리에서 실행된다고 가정합니다.

# 호스트 컴퓨터 (스크립트 실행 위치, 즉 ex04/) 기준 item.csv 파일의 경로
ITEM_CSV_HOST_PATH="../subject/item/item.csv" 

# Docker Compose 파일이 있는 디렉토리 (프로젝트 루트)가 컨테이너 내부 어디로 마운트되었는지
# **여러분의 docker-compose.yml 에 volumes: - .:/csv_data 로 설정했다면 /csv_data 입니다.**
CONTAINER_PROJECT_ROOT_MOUNT_PATH="/csv_data" 

# 컨테이너 내부에서 item.csv 파일에 접근할 경로 (마운트된 경로 기준)
# 예: item.csv 가 호스트에서 ./subject/item/item.csv (프로젝트 루트 기준) 에 있고 프로젝트 루트가 /csv_data 에 마운트되었다면, 컨테이너 내 경로는 /csv_data/subject/item/item.csv 가 됩니다.
ITEM_CSV_CONTAINER_PATH="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/subject/item/item.csv"


# --- Step 1: Create items table ---
echo "--- items 테이블 생성 중 ---"
# CREATE TABLE 명령은 표준 SQL이므로 psql -c 로 실행해도 됩니다.
PGPASSWORD="$DB_PASSWORD" docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
CREATE TABLE IF NOT EXISTS items (
    product_id INT,
    category_id BIGINT,
    category_code VARCHAR(100),
    brand VARCHAR(100)
);"
echo "items 테이블 생성 완료 (이미 존재하면 건너뜁니다)."


# --- Step 2: Import data from item.csv ---
echo "--- ${ITEM_CSV_HOST_PATH} 파일에서 데이터 임포트 시작 ---"

# **\COPY 명령을 실행하기 위해 임시 SQL 스크립트 파일 생성 (호스트에 생성)**
TEMP_COPY_SQL_HOST="temp_item_import_command.sql"
# \COPY 명령 한 줄을 파일에 작성합니다.
echo "\\copy items FROM '${ITEM_CSV_CONTAINER_PATH}' WITH (FORMAT csv, HEADER true);" > "$TEMP_COPY_SQL_HOST"

# 생성된 임시 SQL 스크립트 파일 내용을 컨테이너 내부의 psql로 파이프하여 실행합니다.
# -c 옵션 없이 psql을 실행하면 표준 입력(파이프된 내용)에서 명령을 읽어오고 \COPY를 처리합니다.
echo "--- 컨테이너 내부에서 임포트 명령어 실행 중 (\copy 사용) ---"
PGPASSWORD="$DB_PASSWORD" docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$TEMP_COPY_SQL_HOST"
echo "Data imported into items table."

# (선택 사항) 임포트 후 행 수 확인
echo "--- items 테이블 행 수 확인 ---"
# SELECT 명령은 표준 SQL이므로 다시 psql -c 로 실행합니다.
PGPASSWORD="$DB_PASSWORD" docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) FROM items;"


# --- 임시 스크립트 파일 정리 (호스트) ---
echo "--- 임시 스크립트 파일 정리 중 (호스트) ---"
rm "$TEMP_COPY_SQL_HOST"
echo "임시 스크립트 파일 정리 완료."

echo "--- 스크립트 실행 완료 ---"
exit 0
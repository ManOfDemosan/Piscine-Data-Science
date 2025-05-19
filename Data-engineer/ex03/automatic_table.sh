#!/bin/bash

# 스크립트 실행 중 오류 발생 시 즉시 중단
set -e

echo "--- 데이터베이스 초기 설정 및 로드 시작 ---"

# 데이터베이스 연결 정보
DB_USER="jaehwkim"
DB_NAME="piscineds"
DB_CONTAINER="postgresForDb" # 실행 중인 PostgreSQL 컨테이너 이름 (여러분의 컨테이너 이름과 일치해야 함)
DB_PASSWORD="mysecretpassword" # **여러분의 실제 PostgreSQL 비밀번호로 변경**

# 이 스크립트는 docker-compose.yml 파일이 있는 디렉토리에서 실행된다고 가정합니다.
# 해당 디렉토리를 컨테이너 내부 어디로 마운트했는지 설정합니다.
# **여러분의 docker-compose.yml 에 volumes: - .:/csv_data 로 설정했다면 /csv_data 입니다.**
CONTAINER_PROJECT_ROOT_MOUNT_PATH="/csv_data" 

# 호스트 컴퓨터 (스크립트 실행 위치) 기준 파일 경로
TABLE_SQL_HOST_PATH="./ex02/table.sql" 
CSV_HOST_DIR="../subject/customer" 

# 컨테이너 내부에서 파일에 접근할 경로 (마운트된 경로 기준)
# 예: table.sql 이 호스트에서 ./ex02/table.sql 에 있고 프로젝트 루트가 /csv_data 에 마운트되었다면, 컨테이너 내 경로는 /csv_data/ex02/table.sql 입니다.
TABLE_SQL_CONTAINER_PATH="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/ex02/table.sql"

# 예: CSVs가 호스트에서 ./subject/customer 에 있고 프로젝트 루트가 /csv_data 에 마운트되었다면, 컨테이너 내 경로는 /csv_data/subject/customer 입니다.
CSV_CONTAINER_DIR="${CONTAINER_PROJECT_ROOT_MOUNT_PATH}/subject/customer"


# --- Step 1: Create tables using table.sql ---
echo "--- 테이블 생성 (${TABLE_SQL_HOST_PATH} 사용) ---"
# table.sql 파일을 컨테이너 내부에서 실행합니다.
# -f 옵션에 지정하는 경로는 컨테이너 내부에서 table.sql 파일이 보이는 경로입니다.
# PGPASSWORD 환경 변수를 설정하여 비밀번호를 넘겨줍니다.
PGPASSWORD="$DB_PASSWORD" docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -f "$TABLE_SQL_CONTAINER_PATH"
echo "테이블 생성 완료 (이미 존재하면 건너뜁니다)."


# --- Step 2: Import data from CSV files ---
echo "--- CSV 파일 (${CSV_HOST_DIR})에서 데이터 임포트 시작 ---"

# \copy 명령어를 담을 임시 SQL 스크립트 파일 생성 (이 파일은 호스트에 생성)
TEMP_COPY_SQL_HOST="temp_import_commands.sql"
> "$TEMP_COPY_SQL_HOST" # 파일 내용을 비웁니다.

echo "--- 임포트 명령어 생성 중 ---"
# 호스트의 CSV 디렉토리에서 .csv 파일을 찾아 각 파일에 대한 \copy 명령어 생성
# find 명령은 호스트에서 실행됩니다.
find "$CSV_HOST_DIR" -maxdepth 1 -name "*.csv" -print0 | while IFS= read -r -d $'\0' CSV_HOST_FILE; do
    FILENAME=$(basename "$CSV_HOST_FILE") # 예: data_2022_oct.csv
    TABLE_NAME="${FILENAME%.*}"         # 예: data_2022_oct
    
    # 컨테이너 내부에서 파일에 접근할 경로를 구성 (마운트된 경로 기준)
    CSV_CONTAINER_FILE_PATH="${CSV_CONTAINER_DIR}/${FILENAME}"

    # \copy 명령어를 호스트의 임시 SQL 파일에 추가
    # \copy는 컨테이너 내부 psql에서 실행되므로, 파일 경로는 컨테이너 내부 경로를 가리킵니다.
    echo "\\copy ${TABLE_NAME} FROM '${CSV_CONTAINER_FILE_PATH}' WITH (FORMAT csv, HEADER true);" >> "$TEMP_COPY_SQL_HOST"
    echo "-> 명령어 생성: ${FILENAME} -> ${TABLE_NAME}"
done

# 생성된 임포트 스크립트 내용 확인 (호스트의 임시 파일)
echo "--- 생성된 임포트 스크립트 내용 (호스트의 임시 파일: ${TEMP_COPY_SQL_HOST}) ---"
cat "$TEMP_COPY_SQL_HOST"
echo "-------------------------------------"

echo "--- 컨테이너 내부에서 임포트 명령어 실행 중 ---"
# 임시 SQL 파일을 컨테이너 내부 psql로 파이프하여 실행
# PGPASSWORD 환경 변수를 설정하여 비밀번호를 넘겨줍니다.
PGPASSWORD="$DB_PASSWORD" docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$TEMP_COPY_SQL_HOST"

# Check if the import was successful
if [ $? -eq 0 ]; then
  echo "--- 모든 테이블 데이터 임포트 성공 ---"
  # (선택 사항) 임포트 후 각 테이블의 행 수를 확인
  echo "--- 각 테이블 행 수 확인 ---"
  # 확인하고 싶은 테이블 목록 (CSV 파일 이름 기반)
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

      PGPASSWORD="$DB_PASSWORD" docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "$VERIFY_SQL"
  else
      echo "확인할 CSV 파일을 찾을 수 없습니다."
  fi
else
  echo "--- 데이터 임포트 중 오류 발생 ---"
  exit 1
fi

# 임시 스크립트 파일 정리 (호스트의 임시 스크립트 파일)
echo "--- 임시 스크립트 파일 정리 중 (호스트) ---"
rm "$TEMP_COPY_SQL_HOST"
echo "임시 스크립트 파일 정리 완료."

echo "--- 스크립트 실행 완료 ---"
exit 0
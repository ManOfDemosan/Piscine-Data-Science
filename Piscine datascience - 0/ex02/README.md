# Exercise 02: 첫 번째 테이블

이 과제는 CSV 파일에서 PostgreSQL 테이블을 생성하는 방법을 다룹니다.

## 사용 방법

1. `ex02` 디렉토리로 이동합니다:
   ```bash
   cd ex02
   ```

2. 테이블 생성 및 데이터 가져오기를 실행합니다:
   ```bash
   ./import.sh
   ```

3. 데이터가 성공적으로 가져와졌는지 확인합니다:
   ```bash
   psql -U jaehwkim -d piscineds -c "SELECT COUNT(*) FROM data_2022_oct;"
   ```

## 파일 설명

- `table.sql`: CSV 파일에 해당하는 PostgreSQL 테이블을 생성하는 SQL 스크립트
- `import.sh`: CSV 파일의 데이터를 테이블로 가져오는 쉘 스크립트

## 테이블 구조

각 테이블은 다음과 같은 구조를 가집니다:
- `event_time`: TIMESTAMP (DATETIME) - 첫 번째 열
- `event_type`: VARCHAR(50) - 이벤트 유형
- `product_id`: VARCHAR(50) - 제품 ID
- `price`: NUMERIC(10,2) - 가격
- `user_id`: BIGINT - 사용자 ID
- `user_session`: UUID - 사용자 세션 ID

## 데이터 유형 설명 (최소 6개의 다른 데이터 유형 사용)

1. `TIMESTAMP`: 날짜와 시간 정보를 저장하는 데이터 유형
2. `VARCHAR`: 가변 길이 문자열을 저장하는 데이터 유형
3. `NUMERIC`: 정확한 소수점 숫자를 저장하는 데이터 유형
4. `BIGINT`: 큰 정수 값을 저장하는 데이터 유형
5. `UUID`: 범용 고유 식별자를 저장하는 데이터 유형
6. `BOOLEAN`: 참/거짓 값을 저장하는 데이터 유형 (테이블에는 사용되지 않았지만 PostgreSQL에서 지원)

## 참고 사항

- PostgreSQL의 데이터 유형은 MariaDB의 데이터 유형과 다르므로 주의가 필요합니다.
- 테이블 이름은 CSV 파일 이름에서 확장자를 제외한 형태로 지정했습니다 (예: `data_2022_oct`).
- 열 이름은 CSV 파일의 열 이름과 동일하게 유지했습니다. 
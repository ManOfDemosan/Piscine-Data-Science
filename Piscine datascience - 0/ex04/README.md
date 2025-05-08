# Items Table 생성 스크립트

이 스크립트는 item.csv 파일에서 데이터를 가져와 PostgreSQL 데이터베이스에 items 테이블을 생성합니다.

## 기능
- 3가지 데이터 타입(INT, BIGINT, VARCHAR)을 사용하여 items 테이블 생성
- item.csv 파일의 데이터를 테이블로 자동 가져오기

## 실행 전 준비사항
1. PostgreSQL이 설치되어 있어야 합니다.
2. piscineds 데이터베이스가 생성되어 있어야 합니다:
   ```
   createdb piscineds
   ```
3. 필요한 경우 스크립트의 데이터베이스 설정을 수정하세요:
   ```bash
   DB_NAME="piscineds"
   DB_USER="jaehwkim"
   DB_PASSWORD="postgres"
   DB_HOST="localhost"
   ```

## 실행 방법
```bash
cd ex04
./import_items.sh
``` 
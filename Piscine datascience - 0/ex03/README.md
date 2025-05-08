# Automatic Table 생성 스크립트

이 스크립트는 ex02의 table.sql을 사용하여 테이블을 생성하고, CSV 파일에서 데이터를 자동으로 가져옵니다.

## 기능
- ex02의 table.sql을 사용하여 미리 정의된 테이블 스키마 생성
- customer 폴더의 모든 CSV 파일을 자동으로 해당 테이블로 가져오기

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
cd ex03
./automatic_table.sh
``` 
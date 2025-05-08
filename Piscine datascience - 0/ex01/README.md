# pgAdmin 설치 및 데이터베이스 연결 가이드 (Ubuntu)

이 가이드는 Ubuntu 환경에서 pgAdmin을 설치하고 piscineds 데이터베이스에 연결하는 방법을 설명합니다.

## pgAdmin 설치 (Ubuntu)

### 1. pgAdmin 저장소 추가 및 설치

```bash
# 필요한 패키지 설치
sudo apt update
sudo apt install -y curl gnupg

# pgAdmin 저장소 설정
curl https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo apt-key add -
sudo sh -c 'echo "deb https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list'

# 패키지 업데이트 및 pgAdmin 설치
sudo apt update
sudo apt install -y pgadmin4

# 웹 모드 설정 (선택사항)
sudo /usr/pgadmin4/bin/setup-web.sh
```

### 2. pgAdmin 실행

- **Desktop 모드**: 애플리케이션 메뉴에서 pgAdmin 4를 찾아 실행하거나 터미널에서 `pgadmin4` 명령어로 실행
- **Web 모드**: 웹 브라우저에서 `http://127.0.0.1/pgadmin4` 접속

## pgAdmin에서 piscineds 데이터베이스 연결하기

1. pgAdmin을 실행합니다.
2. 처음 실행 시 마스터 비밀번호를 설정합니다 (pgAdmin 자체 비밀번호).
3. 좌측 패널에서 "Servers"를 오른쪽 클릭하고 "Create" → "Server..."를 선택합니다.
4. "General" 탭에서 서버 이름을 "Local PostgreSQL"로 입력합니다.
5. "Connection" 탭에서 다음과 같이 입력합니다:
   - Host name/address: localhost
   - Port: 5432
   - Maintenance database: postgres
   - Username: jaehwkim (본인의 사용자 이름)
   - Password: mysecretpassword
   - Save password: 체크 (선택사항)
6. "Save" 버튼을 클릭합니다.
7. 연결이 성공하면 좌측 패널에 서버가 나타나고, "Databases" → "piscineds"를 통해 데이터베이스를 볼 수 있습니다.

## pgAdmin 사용 방법

- **데이터베이스 구조 보기**: 좌측 패널에서 데이터베이스 객체(테이블, 뷰, 함수 등) 탐색
- **SQL 쿼리 실행**: "Tools" → "Query Tool"을 선택하거나 데이터베이스를 우클릭하여 "Query Tool" 선택
- **테이블 데이터 보기/편집**: 테이블을 우클릭하고 "View/Edit Data" → "All Rows" 선택

이 설정을 통해 piscineds 데이터베이스를 쉽게 시각화하고 관리할 수 있습니다. 

## 데이터베이스 생성 및 데이터 삽입

1. pgAdmin을 실행합니다.
2. 좌측 패널에서 "Databases"를 오른쪽 클릭하고 "Create" → "Database..."를 선택합니다.
3. 데이터베이스 이름을 "piscineds"로 입력합니다.
4. "Save" 버튼을 클릭합니다.
5. 데이터베이스가 생성되면 좌측 패널에 서버가 나타나고, "Tables" → "piscineds"를 통해 테이블을 볼 수 있습니다.
6. 테이블을 우클릭하고 "Create" → "Table..."를 선택합니다.
7. 테이블 스키마를 입력합니다. 예를 들어:

```sql
CREATE TABLE cart (
    event_time TIMESTAMP,
    event_type TEXT,
    product_id TEXT,
    category_id TEXT,
    category_code TEXT,
    brand TEXT,
    price NUMERIC,
    user_id TEXT,
    user_session TEXT
);

-- 샘플 데이터 삽입
INSERT INTO cart VALUES 
('2022-10-01 09:00:00', 'cart', '5773203', '1407580091522154466', 'null', 'rwmall', 2.42, '66320e86-640e-4770-b02c-75e1efa088d5', 'null');
```

8. 테이블이 생성되면 좌측 패널에 테이블이 나타나고, 데이터를 볼 수 있습니다. 
# PostgreSQL 설정 가이드 (Ubuntu)

이 가이드는 Ubuntu 환경에서 PostgreSQL을 설치하고 필요한 데이터베이스와 사용자를 설정하는 방법을 설명합니다.

## 1. PostgreSQL 설치

```bash
# 패키지 업데이트
sudo apt update

# PostgreSQL 설치
sudo apt install -y postgresql postgresql-contrib
```

## 2. PostgreSQL 서비스 시작

```bash
# PostgreSQL 서비스 상태 확인
sudo systemctl status postgresql

# 서비스가 실행 중이 아니라면 시작
sudo systemctl start postgresql
```

## 3. 데이터베이스 및 사용자 설정

```bash
# postgres 사용자로 전환
sudo -i -u postgres

# PostgreSQL 쉘 실행
psql

# 데이터베이스 생성
CREATE DATABASE piscineds;

# 사용자 생성 (내 학생 로그인 ID 사용)
CREATE USER jaehwkim WITH PASSWORD 'mysecretpassword';

# 사용자에게 데이터베이스 권한 부여
GRANT ALL PRIVILEGES ON DATABASE piscineds TO jaehwkim;

# PostgreSQL 쉘 종료
\q

# postgres 사용자에서 로그아웃
exit
```

## 4. 연결 테스트

```bash
# 생성한 사용자와 데이터베이스로 연결
psql -U jaehwkim -d piscineds -h localhost -W

# 프롬프트에서 비밀번호 입력: mysecretpassword
```

성공적으로 연결되면 `piscineds=>` 프롬프트가 표시됩니다.

## 참고사항

- 보안 설정에 따라 pg_hba.conf 파일을 수정해야 할 수도 있습니다:
  ```bash
  sudo nano /etc/postgresql/[버전]/main/pg_hba.conf
  ```
  
  local 연결 방식을 `md5`로 변경:
  ```
  local   all             all                                     md5
  ```
  
  변경 후 PostgreSQL 서비스 재시작:
  ```bash
  sudo systemctl restart postgresql
  ```
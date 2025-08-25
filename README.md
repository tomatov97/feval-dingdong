# 인스타그램 계정 크롤링 시스템

주기적으로 특정 인스타그램 계정을 크롤링하여 데이터를 수집하고 저장하는 시스템입니다.

## 주요 기능

- **자동 크롤링**: 설정된 간격으로 자동 크롤링 실행
- **데이터 수집**: 프로필 정보, 팔로워 수, 최근 게시물 상세 내용 등
- **스마트 저장**: 새로운 게시글만 자동으로 감지하여 저장
- **데이터 저장**: SQLite 데이터베이스에 체계적 저장
- **스케줄링**: 24시간 간격 등 원하는 주기로 실행
- **로깅**: 상세한 실행 로그 기록
- **데이터 내보내기**: JSON 형태로 데이터 내보내기

## 설치 방법

### 1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. Chrome WebDriver 설치

Chrome 브라우저가 설치되어 있어야 하며, ChromeDriver가 필요합니다.

## 사용 방법

### 기본 실행

```bash
# 특정 계정들을 24시간 간격으로 크롤링
python main.py --accounts username1 username2 username3

# 12시간 간격으로 크롤링
python main.py --accounts username1 --interval 12

# 즉시 한 번만 크롤링
python main.py --accounts username1 --once
```

### 계정 관리

```bash
# 계정 추가
python main.py --add-account new_username

# 계정 제거
python main.py --remove-account username

# 계정 목록 조회
python main.py --list-accounts
```

### 상태 및 통계 조회

```bash
# 스케줄러 상태 조회
python main.py --status

# 크롤링 통계 조회
python main.py --statistics

# 현재 설정 조회
python main.py --config
```

### 데이터 내보내기

```bash
# 특정 계정의 데이터를 JSON으로 내보내기
python main.py --export username
```

### 데이터베이스 관리

```bash
# 데이터베이스 백업
python main.py --backup

# 데이터베이스 복원
python main.py --restore backup_file.db

# 데이터베이스 정보 조회
python main.py --db-info

# 데이터베이스 초기화 (데이터만 삭제)
python main.py --db-init

# 데이터베이스 완전 초기화 (백업 후 모든 데이터 삭제)
python main.py --db-reset

# 새 게시물 수 조회
python main.py --new-posts username

# 최신 게시물 조회
python main.py --latest-posts username
```

## 설정 파일

`config.py` 파일에서 기본 설정을 변경할 수 있습니다:

```python
# 크롤링 간격 (시간)
CRAWL_INTERVAL_HOURS = 24

# 브라우저 헤드리스 모드
HEADLESS_MODE = True

# 기본 크롤링 계정 목록
DEFAULT_ACCOUNTS = [
    'example_user1',
    'example_user2',
]
```

## 환경 변수

`.env` 파일을 생성하여 환경 변수를 설정할 수 있습니다:

```bash
# 인스타그램 로그인 정보 (필수!)
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password

# 크롤링 설정
CRAWL_INTERVAL_HOURS=24
HEADLESS_MODE=false
LOG_LEVEL=INFO
```

### ⚠️ **중요: 로그인 정보 설정**

크롤링을 위해서는 반드시 `.env` 파일에 인스타그램 계정 정보를 설정해야 합니다:

1. 프로젝트 루트에 `.env` 파일 생성
2. `INSTAGRAM_USERNAME`에 인스타그램 사용자명 입력
3. `INSTAGRAM_PASSWORD`에 인스타그램 비밀번호 입력
4. 파일 저장 후 크롤링 실행

## 데이터베이스 구조

### account_data 테이블
- 계정 기본 정보 (프로필 이미지, 바이오, 팔로워 수 등)
- 크롤링 시간 기록

### post_data 테이블
- 최근 게시물 상세 정보 (이미지 URL, 캡션, 좋아요 수, 댓글 수, 해시태그, 멘션 등)
- 게시물 URL을 고유 식별자로 사용하여 중복 저장 방지

### crawl_history 테이블
- 크롤링 실행 히스토리 및 오류 기록

## 데이터 보존

이 시스템은 **기존 데이터를 보존**합니다:

- **자동 보존**: 프로그램을 다시 실행해도 기존 데이터베이스가 유지됩니다
- **스마트 저장**: 새로운 게시글만 자동으로 감지하여 저장 (중복 방지)
- **백업 기능**: `--backup` 옵션으로 데이터베이스를 백업할 수 있습니다
- **복원 기능**: `--restore` 옵션으로 백업 파일에서 데이터를 복원할 수 있습니다
- **데이터 정보**: `--db-info` 옵션으로 데이터베이스 상태를 확인할 수 있습니다
- **데이터 초기화**: `--db-init` 옵션으로 모든 데이터를 삭제할 수 있습니다
- **완전 초기화**: `--db-reset` 옵션으로 백업 후 데이터베이스를 완전히 새로 만들 수 있습니다

데이터베이스 파일(`instagram_data.db`)은 프로젝트 폴더에 저장되며, 프로그램을 삭제하지 않는 한 계속 유지됩니다.

## 스마트 저장 시스템

### 중복 방지
- 게시물 URL을 고유 식별자로 사용
- 이미 저장된 게시물은 자동으로 건너뛰기
- 새로운 게시물만 데이터베이스에 저장

### 상세 정보 수집
- 게시물 이미지 URL
- 캡션 내용 (텍스트)
- 게시 시간
- 해시태그 및 멘션 추출

## 주의사항

1. **인스타그램 정책 준수**: 과도한 크롤링은 계정 제재를 받을 수 있습니다.
2. **적절한 간격 설정**: 최소 1시간 이상의 간격을 권장합니다.
3. **법적 고려사항**: 개인정보 보호법 및 웹사이트 이용약관을 준수하세요.
4. **서버 부하 방지**: 계정 간 적절한 간격을 두어 서버에 부하를 주지 마세요.

## 로그 파일

크롤링 실행 로그는 `instagram_crawler.log` 파일에 저장됩니다.

## 문제 해결

### Chrome WebDriver 오류
- Chrome 브라우저가 설치되어 있는지 확인
- ChromeDriver 버전이 Chrome 브라우저 버전과 호환되는지 확인

### 크롤링 실패
- 인터넷 연결 상태 확인
- 인스타그램 계정이 존재하는지 확인
- 로그 파일에서 상세 오류 내용 확인

## 라이선스

이 프로젝트는 교육 및 개인 사용 목적으로만 사용하시기 바랍니다.

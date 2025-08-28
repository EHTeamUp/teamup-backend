
# TeamUp - 팀 프로젝트 매칭 플랫폼

## 🚀 프로젝트 개요

 머신러닝 기반 시너지 분석을 통해 최적의 팀원 매칭을 도와, 공모전 팀 구성 과정에서 팀원 모집의 어려움을 해결하도록 돕는 팀 매칭 플랫폼입니다.

## ✨ 주요 기능

### 🤖 AI 기반 시너지 분석
- **머신러닝 모델**: 팀 구성원 간 시너지 점수 예측
- **스킬 매칭**: 역할별 스킬 호환성 분석
- **성향 분석**: 성향 테스트 기반 팀 시너지 분석
- **포트폴리오 기반 추천**: 과거 경험을 통한 최적 매칭

### 🕷️ 자동 공모전 크롤링
- **다중 사이트 크롤링**: 콘테스트코리아, 링커리어, 씽크유 등
- **AI 이미지 분석**: Ollama LLaVA 모델을 통한 포스터 분석
- **자동 태그 생성**: 공모전 분류 및 필터링
- **실시간 업데이트**: 스케줄러를 통한 정기적인 데이터 수집

### 👥 팀 매칭 시스템
- **다단계 회원가입**: 기본정보 → 스킬/역할 → 경험 → 성향테스트
- **스마트 매칭**: AI 알고리즘 기반 팀 추천
- **역할 기반 매칭**: 개발자, 디자이너, 기획자 등 역할별 매칭
- **스킬 호환성**: 기술 스택 간 시너지 분석

### 📢 모집 공고 관리
- **공고 작성**: 상세한 프로젝트 정보 등록
- **지원 관리**: 지원자 관리 및 상태 추적
- **댓글 시스템**: 팀원 간 소통 채널
- **알림 시스템**: FCM 기반 실시간 알림

### 🔔 스마트 알림 시스템
- **마감일 알림**: 공모전 마감일 자동 알림
- **매칭 알림**: 새로운 팀 매칭 제안 알림
- **지원 상태 알림**: 지원 결과 실시간 알림
- **FCM 푸시 알림**: 모바일 푸시 알림 지원

### 🔐 보안 및 인증
- **이메일 인증**: Gmail SMTP를 통한 안전한 인증
- **JWT 토큰**: 보안성 높은 인증 시스템
- **비밀번호 해싱**: bcrypt를 통한 안전한 비밀번호 저장
- **Firebase Admin**: 추가 보안 레이어

## 🏗️ 프로젝트 구조

```
TeamUp/
├── main.py                     # FastAPI 앱 메인 파일
├── config.py                   # 설정 파일
├── database.py                 # 데이터베이스 연결
├── requirements.txt            # 의존성 패키지
├── routers/                    # API 라우터들
│   ├── users.py               # 사용자 관리
│   ├── registration.py        # 회원가입 관련
│   ├── profile.py             # 프로필 관리
│   ├── contests.py            # 공모전 관리
│   ├── recruitments.py        # 모집 공고 관리
│   ├── applications.py        # 지원 관리
│   ├── comments.py            # 댓글 시스템
│   ├── personality.py         # 성향 분석
│   ├── synergy.py             # AI 시너지 분석
│   └── notifications.py       # 알림 시스템
├── models/                     # 데이터베이스 모델들
│   ├── user.py                # 사용자 모델
│   ├── skill.py               # 스킬 모델
│   ├── role.py                # 역할 모델
│   ├── contest.py             # 공모전 모델
│   ├── recruitment.py         # 모집 공고 모델
│   ├── personality.py         # 성향 모델
│   └── ...                    # 기타 모델들
├── schemas/                    # Pydantic 스키마들
│   ├── user.py                # 사용자 스키마
│   ├── contest.py             # 공모전 스키마
│   ├── recruitment.py         # 모집 공고 스키마
│   ├── synergy.py             # 시너지 분석 스키마
│   └── ...                    # 기타 스키마들
├── jobs/                       # 백그라운드 작업
│   ├── analyzer.py            # AI 이미지 분석기
│   ├── crawler.py             # 공모전 크롤러
│   ├── crawler_limited.py     # 제한적 크롤러
│   └── crawling/              # 크롤링 모듈들
│       ├── contestkorea.py    # 콘테스트코리아 크롤러
│       ├── linkareer.py       # 링커리어 크롤러
│       └── thinkyou.py        # 씽크유 크롤러
├── ml/                        # 머신러닝 모듈
│   ├── synergy_service.py     # 시너지 분석 서비스
│   ├── predict.py             # 예측 모델
│   ├── preprocessing.py       # 데이터 전처리
│   └── message_generator.py   # 메시지 생성기
├── utils/                     # 유틸리티 함수들
│   ├── auth.py                # 인증 유틸리티
│   ├── email_auth.py          # 이메일 인증
│   ├── fcm_service.py         # FCM 알림 서비스
│   ├── notification_service.py # 알림 서비스
│   └── scheduler.py           # 스케줄러
├── data/                      # 데이터 파일들
│   ├── role_skill_matching_matrix.csv
│   ├── updated_role_matrix.csv
│   └── updated_skill_matrix.csv
├── artifacts/                 # ML 모델 아티팩트
│   └── predictor.joblib       # 시너지 예측 모델
└── jobs/data/                 # 크롤링 데이터
    ├── all_contests.json
    ├── contest_with_tags.json
    └── ...
```

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# Python 3.12.6으로 teamup 환경 생성
conda create -n teamup python=3.12.6

# 환경 활성화
conda activate teamup

# 또는 venv 사용
python -m venv teamup
source teamup/bin/activate  # Linux/Mac
teamup\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일 생성:
```env
# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@localhost/teamup_db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
VERIFICATION_CODE_EXPIRE_MINUTES=10

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=path/to/your/firebase-credentials.json

# AI Model Configuration 
OLLAMA_HOST=http://localhost:11434
```

### 3. AI 모델 설정 (선택사항)
```bash
# Ollama 설치 (이미지 분석용)
curl -fsSL https://ollama.ai/install.sh | sh

# LLaVA 모델 다운로드
ollama pull llava:7b
```

### 4. 데이터베이스 설정
```sql
-- MySQL 데이터베이스 생성
CREATE DATABASE your_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. 서버 실행
```bash
# 개발 모드
uvicorn main:app --reload

# 프로덕션 모드
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📱 API 엔드포인트

### 🔐 인증 관련 (`/api/v1/users`)
```bash
POST /users/login              # 로그인
GET  /users/me                 # 현재 사용자 정보 조회
PUT  /users/mypage             # 회원정보 수정
```

### 📝 회원가입 관련 (`/api/v1/registration`)
```bash
POST /registration/send-verification    # 이메일 인증번호 발송
POST /registration/verify-email         # 이메일 인증번호 검증
POST /registration/register             # 회원가입
POST /registration/step1                # 1단계: 기본정보
POST /registration/step2                # 2단계: 스킬/역할
POST /registration/step3                # 3단계: 경험
POST /registration/step4                # 4단계: 성향테스트
GET  /registration/status/{user_id}     # 진행 상태
```

### 👤 프로필 관리 (`/api/v1/profile`)
```bash
PUT  /profile/skills          # 스킬 수정
GET  /profile/skills          # 스킬 조회
PUT  /profile/roles           # 역할 수정
GET  /profile/roles           # 역할 조회
PUT  /profile/experiences     # 경험 수정
GET  /profile/experiences     # 경험 조회
```

### 🏆 공모전 관리 (`/api/v1/contests`)
```bash
GET  /contests                # 공모전 목록 조회
GET  /contests/{contest_id}   # 공모전 상세 조회
GET  /contests/filters        # 필터 옵션 조회
POST /contests/search         # 공모전 검색
```

### 📢 모집 게시글 관리 (`/api/v1/recruitments`)
```bash
POST /recruitments            # 게시글 작성
GET  /recruitments            # 게시글 목록 조회
GET  /recruitments/{id}       # 게시글 상세 조회
PUT  /recruitments/{id}       # 게시글 수정
DELETE /recruitments/{id}     # 게시글 삭제
```

### 📝 지원 관리 (`/api/v1/applications`)
```bash
POST /applications            # 지원하기
GET  /applications            # 지원 목록 조회
PUT  /applications/{id}       # 지원 상태 변경
DELETE /applications/{id}     # 지원 취소
```

### 💬 댓글 시스템 (`/api/v1/comments`)
```bash
POST /comments                # 댓글 작성
GET  /comments/{recruitment_id} # 댓글 목록 조회
PUT  /comments/{id}           # 댓글 수정
DELETE /comments/{id}         # 댓글 삭제
```

### 🧠 성향 분석 (`/api/v1/personality`)
```bash
POST /personality/test        # 성향 테스트
GET  /personality/{user_id}   # 성향 결과 조회
PUT  /personality             # 성향 정보 수정
```

### 🤖 AI 시너지 분석 (`/api/v1/synergy`)
```bash
POST /synergy/analyze         # 팀 시너지 분석
GET  /synergy/recommendations # 팀 추천
POST /synergy/predict         # 시너지 점수 예측
```

### 🔔 알림 시스템 (`/api/v1/notifications`)
```bash
GET  /notifications           # 알림 목록 조회
PUT  /notifications/{id}      # 알림 읽음 처리
DELETE /notifications/{id}    # 알림 삭제
```

## 🤖 AI 기능 상세

### 시너지 분석 모델
- **XGBoost 기반**: 팀 구성원 간 호환성 예측
- **특성 엔지니어링**: 스킬, 역할, 성향, 경험 기반 분석
- **SHAP 설명**: 예측 결과에 대한 설명 제공
- **실시간 추천**: 사용자 프로필 기반 팀 추천

### 이미지 분석 시스템
- **Ollama LLaVA**: 공모전 포스터 자동 분석
- **태그 생성**: AI 기반 공모전 분류
- **필터링**: 카테고리별 자동 분류

## 🔄 백그라운드 작업

#### 자동 크롤링 설정 (Crontab)
```bash
# 1. crontab 설치 확인
sudo apt install cron -y

# 2. crontab 편집
crontab -e

# 3. 2주마다 월요일 오전 9시에 크롤링 실행
0 9 * * 1 [ $(( $(date +\%V) % 2 )) -eq 0 ] && cd /path/to/your/project && python main_crawler.py >> /var/log/teamup/crawler.log 2>&1

# 4. 실행 권한 부여
chmod +x main_crawler.py

# 5. 로그 디렉토리 생성
sudo mkdir -p /var/log/teamup

# 6. 현재 crontab 목록 확인
crontab -l

# 7. 수동 테스트
python main_crawler.py
```

### 알림 스케줄러
- **매일 자정**: 공모전 마감일 알림 확인
- **실시간**: 팀 지원, 수락, 거절 등 실시간 상태 알림
- **FCM 푸시**: 모바일 푸시 알림

## 🛠️ 기술 스택

### Backend
<img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/fastapi-009688?style=for-the-badge&logo=fastapi&logoColor=white"> 
<img src="https://img.shields.io/badge/sqlalchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white"> 
<img src="https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=white">
<img src="https://img.shields.io/badge/pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white">

- **Python**: 개발 언어
- **FastAPI**: 고성능 Python 웹 프레임워크
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **MySQL**: 메인 데이터베이스
- **Pydantic**: 데이터 검증 및 직렬화


### AI & ML
<img src="https://img.shields.io/badge/ollama-000000?style=for-the-badge&logo=ollama&logoColor=white">
<img src="https://img.shields.io/badge/scikitlearn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white">
<img src="https://img.shields.io/badge/xgboost-150458?style=for-the-badge&logo=xgboost&logoColor=white">
<img src="https://img.shields.io/badge/shap-150458?style=for-the-badge&logo=shap&logoColor=white">
<img src="https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white">
<img src="https://img.shields.io/badge/numpy-013243?style=for-the-badge&logo=numpy&logoColor=white">

- **Ollama**: 로컬 AI 모델 (LLaVA)
- **Scikit-learn**: 머신러닝 라이브러리
- **XGBoost**: 시너지 예측 모델
- **SHAP**: 모델 설명 가능성
- **Pandas/Numpy**: 데이터 처리

### 크롤링 & 데이터 수집
<img src="https://img.shields.io/badge/selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white">
<img src="https://img.shields.io/badge/beautifulsoup-000000?style=for-the-badge&logo=beautifulsoup&logoColor=white">

- **Selenium**: 동적 웹페이지 크롤링
- **BeautifulSoup**: HTML 파싱

### 인증 & 보안
<img src="https://img.shields.io/badge/jwt-40AEF0?style=for-the-badge&logo=jwt&logoColor=white">
<img src="https://img.shields.io/badge/bcrypt-232F3E?style=for-the-badge&logo=bcrpt&logoColor=white">
<img src="https://img.shields.io/badge/firebase-DD2C00?style=for-the-badge&logo=firebase&logoColor=white">
<img src="https://img.shields.io/badge/gmail-EA4335?style=for-the-badge&logo=gmail&logoColor=white">


- **JWT**: 토큰 기반 인증
- **bcrypt**: 비밀번호 해싱
- **Firebase Admin**: 추가 보안 레이어
- **Gmail SMTP**: 이메일 인증

### 알림 & 통신
<img src="https://img.shields.io/badge/firebase-DD2C00?style=for-the-badge&logo=firebase&logoColor=white">
<img src="https://img.shields.io/badge/APScheduler-3776AB?style=for-the-badge&logo=APScheduler&logoColor=white">

- **FCM**: Firebase Cloud Messaging
- **APScheduler**: 백그라운드 작업 스케줄링

### 서버  & 배포
<img src="https://img.shields.io/badge/EC2-FF9E0F?style=for-the-badge&logo=EC2&logoColor=white"> 

- **AWS EC2**: 서버 호스팅  및 배포

### 협업 도구
<img src="https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white"> 
<img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white">
<img src="https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=Notion&logoColor=white">

- **Git**: 버전 관리
- **GitHub**: 코드 저장소 및 협업
- **Notion**: 프로젝트 문서화 및 협업



## 📊 데이터베이스 ERD

<img width="830" height="680" alt="Image" src="https://github.com/user-attachments/assets/980fd370-bd8e-4ef5-a02c-f8e8c734f0cc" />

## 📚 API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

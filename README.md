# TeamUp - 팀 프로젝트 매칭 플랫폼

## 🚀 프로젝트 개요

TeamUp은 개발자들이 팀 프로젝트를 찾고 매칭할 수 있는 플랫폼입니다. 이메일 인증을 통한 안전한 회원가입, 다단계 프로필 설정, 그리고 포트폴리오 관리 기능을 제공합니다.

## ✨ 주요 기능

### 🔐 인증 시스템
- **이메일 인증 회원가입**: Gmail SMTP를 통한 안전한 인증
- **JWT 토큰 기반 로그인**: 보안성 높은 인증 시스템
- **비밀번호 해싱**: bcrypt를 통한 안전한 비밀번호 저장

### 👤 사용자 관리
- **다단계 회원가입**: 기본정보 → 스킬/역할 → 경험 → 성향테스트(선택)
- **마이페이지**: 이름, 비밀번호 수정
- **프로필 관리**: 스킬, 역할, 공모전 수상 경험 관리

### 🎯 프로필 시스템
- **스킬 관리**: 기존 스킬 선택 또는 사용자 정의 스킬 추가
- **역할 관리**: 기존 역할 선택 또는 사용자 정의 역할 추가
- **경험 관리**: 공모전 수상 경험 포트폴리오

## 🏗️ 프로젝트 구조

```
TeamUp/
├── main.py                 # FastAPI 앱 메인 파일
├── config.py               # 설정 파일
├── database.py             # 데이터베이스 연결
├── requirements.txt        # 의존성 패키지
├── routers/                # API 라우터들
│   ├── users.py           # 사용자 관리 + 마이페이지
│   ├── profile.py         # 프로필 상세 기능
│   └── registration.py    # 회원가입 관련
├── models/                 # 데이터베이스 모델들
│   ├── user.py            # 사용자 모델
│   ├── skill.py           # 스킬 모델
│   ├── role.py            # 역할 모델
│   ├── experience.py      # 경험 모델
│   └── ...                # 기타 모델들
├── schemas/                # Pydantic 스키마들
│   ├── user.py            # 사용자 스키마
│   └── registration.py    # 회원가입 스키마
└── utils/                  # 유틸리티 함수들
    ├── auth.py            # 인증 유틸리티
    └── email_auth.py      # 이메일 인증
```

## 🚀 빠른 시작

### 1. Conda 환경 설정 (권장)
```bash
# Python 3.12.6으로 teamup 환경 생성
conda create -n teamup python=3.12.6

# 환경 활성화
conda activate teamup

# 의존성 설치
pip install -r requirements.txt
```

> **💡 참고**: conda는 자체적으로 가상환경을 관리하므로 별도의 venv 폴더가 필요하지 않습니다.

### 2. 환경 변수 설정
`.env` 파일 생성 (conda 환경 사용 시 프로젝트 루트에 생성):
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

# Email Verification
VERIFICATION_CODE_EXPIRE_MINUTES=10
```

### 3. Gmail SMTP 설정
자세한 설정은 `SETUP_EMAIL.md` 파일을 참조하세요.

### 4. 서버 실행
```bash
uvicorn main:app --reload
```

## 📱 API 엔드포인트

### 🔐 인증 관련 (`/api/v1/users`)
```bash
POST /users/login              # 로그인
GET  /users/me                 # 현재 사용자 정보 조회
PUT  /users/mypage             # 회원정보 수정 (이름, 비밀번호)
```

### 📝 회원가입 관련 (`/api/v1/registration`)
```bash
POST /registration/send-verification    # 이메일 인증번호 발송
POST /registration/verify-email         # 이메일 인증번호 검증
POST /registration/check-userid         # 사용자 ID 중복 검사
POST /registration/register             # 회원가입
POST /registration/step1                # 1단계: 기본정보 + 이메일인증
POST /registration/step2                # 2단계: 스킬 + 역할 선택
POST /registration/step3                # 3단계: 공모전 수상 경험
POST /registration/step4                # 4단계: 성향테스트 (선택사항)
POST /registration/complete             # 전체 회원가입 완료
GET  /registration/status/{user_id}     # 회원가입 진행 상태
```

### 👤 프로필 관리 (`/api/v1/profile`)
```bash
# 스킬 관리
PUT  /profile/skills          # 스킬 수정
GET  /profile/skills          # 현재 스킬 조회

# 역할 관리
PUT  /profile/roles           # 역할 수정
GET  /profile/roles           # 현재 역할 조회

# 경험 관리
PUT  /profile/experiences     # 공모전 경험 수정
GET  /profile/experiences     # 현재 경험 조회
```

## 💡 사용 예시

### 1. 회원가입 과정
```bash
# 1단계: 이메일 인증번호 발송
curl -X POST "http://localhost:8000/api/v1/registration/send-verification" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'

# 2단계: 이메일 인증번호 검증
curl -X POST "http://localhost:8000/api/v1/registration/verify-email" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "verification_code": "123456"}'

# 3단계: 회원가입
curl -X POST "http://localhost:8000/api/v1/registration/register" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "testuser",
       "name": "Test User",
       "email": "user@example.com",
       "password": "password123",
       "verification_code": "123456"
     }'
```

### 2. 로그인
```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "testuser",
       "password": "password123"
     }'
```

### 3. 프로필 수정
```bash
# 스킬 수정
curl -X PUT "http://localhost:8000/api/v1/profile/skills" \
     -H "Authorization: Bearer {access_token}" \
     -H "Content-Type: application/json" \
     -d '{
       "skill_ids": [1, 2, 3],
       "custom_skills": ["Flutter", "Dart"]
     }'

# 경험 수정
curl -X PUT "http://localhost:8000/api/v1/profile/experiences" \
     -H "Authorization: Bearer {access_token}" \
     -H "Content-Type: application/json" \
     -d '{
       "experiences": [
         {
           "contest_name": "2024 대학생 소프트웨어 경진대회",
           "award_date": "2024-12-01",
           "host_organization": "한국정보산업연합회",
           "award_name": "대상",
           "description": "팀 프로젝트 매칭 플랫폼으로 수상"
         }
       ]
     }'
```

## 🔒 보안 특징

- **이메일 인증**: 6자리 랜덤 인증번호, 10분 만료
- **비밀번호 보안**: bcrypt 해싱, 최소 6자 이상
- **JWT 토큰**: 안전한 인증 및 권한 관리
- **데이터 검증**: Pydantic을 통한 엄격한 데이터 검증
- **SQL 인젝션 방지**: SQLAlchemy ORM 사용

## 🛠️ 기술 스택

- **Backend**: FastAPI (Python 3.12.6 권장)
- **Database**: MySQL + SQLAlchemy ORM
- **Authentication**: JWT + bcrypt
- **Email**: Gmail SMTP
- **Validation**: Pydantic
- **Documentation**: Swagger UI (자동 생성)

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

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.

---

**TeamUp** - 함께 성장하는 개발자 커뮤니티 🚀 
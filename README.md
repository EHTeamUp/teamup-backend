# TeamUp - 팀 프로젝트 매칭 플랫폼

## 이메일 인증 기능이 포함된 회원가입 시스템

### 새로운 회원가입 흐름

1. **이메일 인증번호 요청**: `POST /users/send-verification`
2. **이메일 인증번호 검증**: `POST /users/verify-email`
3. **회원가입 완료**: `POST /users/register`

### 간단한 설정 (Redis 없음)

이메일 인증을 위해 **Gmail SMTP 설정**만 필요합니다.

#### 1. Gmail 설정
- Google 계정에서 **2단계 인증** 활성화
- **앱 비밀번호** 생성 (16자리)
- 자세한 설정은 `SETUP_EMAIL.md` 참조

#### 2. 환경 변수 설정
`.env` 파일에 다음 설정 추가:

```env
# Email Configuration (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Email Verification
VERIFICATION_CODE_EXPIRE_MINUTES=10
```

### API 사용 예시

#### 1. 이메일 인증번호 전송
```bash
curl -X POST "http://localhost:8000/users/send-verification" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
```

#### 2. 이메일 인증번호 검증
```bash
curl -X POST "http://localhost:8000/users/verify-email" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "verification_code": "123456"}'
```

#### 3. 회원가입 (인증번호 포함)
```bash
curl -X POST "http://localhost:8000/users/register" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "testuser",
       "name": "Test User",
       "email": "user@example.com",
       "password": "password123",
       "verification_code": "123456"
     }'
```

### 보안 특징

- **6자리 숫자 인증번호**: 랜덤 생성
- **10분 만료**: 인증번호 자동 만료
- **메모리 기반**: 빠른 검증 (서버 재시작 시 데이터 손실)
- **bcrypt 해싱**: 안전한 비밀번호 저장
- **JWT 토큰**: 로그인 후 인증

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 서버 실행

```bash
uvicorn main:app --reload
```

### 상세 설정 가이드

자세한 설정 방법은 `SETUP_EMAIL.md` 파일을 참조하세요. 
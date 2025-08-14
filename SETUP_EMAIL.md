# TeamUp 이메일 인증 설정 가이드

## 🚀 간단한 설정

Gmail SMTP를 사용하여 이메일 인증을 설정하는 방법입니다.

## 📧 Gmail 설정

### 1. Google 계정 보안 설정
1. [Google 계정 설정](https://myaccount.google.com/) 접속
2. **보안** 탭 클릭
3. **2단계 인증** 활성화

### 2. 앱 비밀번호 생성
1. **보안** → **2단계 인증** → **앱 비밀번호**
2. **앱 선택**: "메일"
3. **기기 선택**: "Windows 컴퓨터" 또는 "기타"
4. **생성** 클릭
5. **16자리 비밀번호** 복사 

## ⚙️ 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용 추가:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/teamup_db

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

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## 🔑 SECRET_KEY 생성

강력한 비밀키 생성:
```bash
# Windows PowerShell
openssl rand -hex 32

# 또는 Python에서
python -c "import secrets; print(secrets.token_hex(32))"
```

## 📱 API 사용법

### 1. 이메일 인증번호 전송
```bash
curl -X POST "http://localhost:8000/users/send-verification" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
```

### 2. 이메일 인증번호 검증
```bash
curl -X POST "http://localhost:8000/users/verify-email" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "verification_code": "123456"}'
```

### 3. 회원가입 (인증번호 포함)
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

## ⚠️ 주의사항

- **앱 비밀번호**: 일반 Gmail 비밀번호가 아닌 **앱 비밀번호** 사용
- **2단계 인증**: 반드시 활성화 필요
- **메모리 기반**: 서버 재시작 시 인증 데이터 손실
- **개발용**: 프로덕션 환경에서는 Redis 사용 권장

## 🧪 테스트

1. **서버 실행**:
   ```bash
   uvicorn main:app --reload
   ```

2. **API 문서 확인**: http://localhost:8000/docs

3. **이메일 전송 테스트**: 위의 curl 명령어로 테스트

## 🆘 문제 해결

### 이메일 전송 실패
- Gmail 앱 비밀번호 확인
- 2단계 인증 활성화 확인
- SMTP 설정 확인

### 인증번호 만료
- 기본 10분 만료
- `VERIFICATION_CODE_EXPIRE_MINUTES` 값 조정 가능

### 서버 재시작 시 데이터 손실
- 메모리 기반이므로 정상 동작
- 프로덕션에서는 Redis 사용 권장 
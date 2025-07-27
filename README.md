# TeamUp API

FastAPI와 MySQL을 사용한 팀 협업 플랫폼 백엔드 API

## 🚀 기술 스택

- **Backend**: FastAPI
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt
- **Validation**: Pydantic

## 📋 필수 요구사항

- Python 3.8+
- MySQL 8.0+
- pip

## 🛠️ 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd TeamUp
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. MySQL 데이터베이스 설정

1. MySQL 서버가 실행 중인지 확인
2. 데이터베이스 생성:
```sql
CREATE DATABASE teamup_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/teamup_db

# Security
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

⚠️ **중요**: 
- `username`, `password`를 실제 MySQL 계정 정보로 변경하세요
- `SECRET_KEY`는 강력한 비밀키로 변경하세요 (최소 32자 이상 권장)
- 강력한 비밀키 생성 방법: `openssl rand -hex 32` 명령어 사용
- `.env` 파일은 Git에 올라가지 않도록 `.gitignore`에 포함되어 있습니다

### 6. 서버 실행
```bash
python main.py
```

또는

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 인증

API는 JWT 토큰 기반 인증을 사용합니다.

### 사용자 등록
```bash
POST /api/v1/users/register
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
}
```

### 로그인
```bash
POST /api/v1/users/login
{
    "username": "testuser",
    "password": "password123"
}
```

응답으로 받은 `access_token`을 이후 요청의 Authorization 헤더에 포함:
```
Authorization: Bearer <access_token>
```

## 📱 Android Studio 연동

### CORS 설정
API는 Android 에뮬레이터와의 통신을 위해 CORS가 설정되어 있습니다:
- `http://10.0.2.2:8000` (Android 에뮬레이터용)
- `http://localhost:8000`
- `http://127.0.0.1:8000`

### Android에서 API 호출 예시 (Java)

#### build.gradle (app 레벨)
```gradle
dependencies {
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.9.0'
}
```

#### API 서비스 인터페이스
```java
public interface ApiService {
    @POST("api/v1/users/login")
    Call<LoginResponse> login(@Body LoginRequest loginRequest);
    
    @POST("api/v1/users/register")
    Call<UserResponse> register(@Body RegisterRequest registerRequest);
    
    @GET("api/v1/users/me")
    Call<UserResponse> getCurrentUser(@Header("Authorization") String token);
}
```

#### 데이터 모델 클래스
```java
public class LoginRequest {
    private String username;
    private String password;
    
    public LoginRequest(String username, String password) {
        this.username = username;
        this.password = password;
    }
    
    // Getters and Setters
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
}

public class LoginResponse {
    private String access_token;
    private String token_type;
    
    // Getters and Setters
    public String getAccessToken() { return access_token; }
    public void setAccessToken(String accessToken) { this.access_token = accessToken; }
    public String getTokenType() { return token_type; }
    public void setTokenType(String tokenType) { this.token_type = tokenType; }
}
```

#### Retrofit 설정 및 사용 예시
```java
public class ApiClient {
    private static final String BASE_URL = "http://10.0.2.2:8000/";
    private static Retrofit retrofit = null;
    
    public static Retrofit getClient() {
        if (retrofit == null) {
            // 로깅 인터셉터 추가
            HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
            logging.setLevel(HttpLoggingInterceptor.Level.BODY);
            
            OkHttpClient.Builder httpClient = new OkHttpClient.Builder();
            httpClient.addInterceptor(logging);
            
            retrofit = new Retrofit.Builder()
                .baseUrl(BASE_URL)
                .addConverterFactory(GsonConverterFactory.create())
                .client(httpClient.build())
                .build();
        }
        return retrofit;
    }
}

// 사용 예시
public class MainActivity extends AppCompatActivity {
    private ApiService apiService;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        apiService = ApiClient.getClient().create(ApiService.class);
        
        // 로그인 예시
        loginUser("testuser", "password123");
    }
    
    private void loginUser(String username, String password) {
        LoginRequest loginRequest = new LoginRequest(username, password);
        
        Call<LoginResponse> call = apiService.login(loginRequest);
        call.enqueue(new Callback<LoginResponse>() {
            @Override
            public void onResponse(Call<LoginResponse> call, Response<LoginResponse> response) {
                if (response.isSuccessful()) {
                    LoginResponse loginResponse = response.body();
                    String token = loginResponse.getAccessToken();
                    // 토큰을 SharedPreferences에 저장
                    saveToken(token);
                    Toast.makeText(MainActivity.this, "로그인 성공!", Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(MainActivity.this, "로그인 실패", Toast.LENGTH_SHORT).show();
                }
            }
            
            @Override
            public void onFailure(Call<LoginResponse> call, Throwable t) {
                Toast.makeText(MainActivity.this, "네트워크 오류: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void saveToken(String token) {
        SharedPreferences prefs = getSharedPreferences("TeamUpPrefs", MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        editor.putString("access_token", token);
        editor.apply();
    }
}
```

#### 권한 설정 (AndroidManifest.xml)
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

## 🗂️ 프로젝트 구조

```
TeamUp/
├── main.py              # FastAPI 앱 진입점
├── config.py            # 설정 관리
├── database.py          # 데이터베이스 연결
├── requirements.txt     # Python 의존성
├── models/              # SQLAlchemy 모델
│   └── user.py
├── schemas/             # Pydantic 스키마
│   └── user.py
├── routers/             # API 라우터
│   └── users.py
└── utils/               # 유틸리티 함수
    └── auth.py
```

## 🔧 개발 환경 설정

### 디버그 모드
개발 중에는 `DEBUG=True`로 설정하여 자동 리로드와 상세한 에러 메시지를 활성화할 수 있습니다.

### 로깅
SQL 쿼리 로깅이 활성화되어 있어 데이터베이스 쿼리를 확인할 수 있습니다.

## 🚀 배포

프로덕션 환경에서는 다음 사항을 고려하세요:

1. `DEBUG=False`로 설정
2. 강력한 `SECRET_KEY` 사용
3. 데이터베이스 연결 보안 강화
4. HTTPS 사용
5. 적절한 로깅 설정

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 
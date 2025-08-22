import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
from datetime import datetime, timedelta
import threading
import time

# 메모리 기반 저장소 (Redis 대체)
verification_codes = {}  # {email: {"code": "123456", "expires_at": datetime}}
verified_emails = {}      # {email: {"verified_at": datetime, "expires_at": datetime}}

# 스레드 안전을 위한 락
storage_lock = threading.Lock()

def cleanup_expired_data():
    """만료된 데이터 정리"""
    current_time = datetime.now()
    
    with storage_lock:
        # 만료된 인증번호 삭제
        expired_verifications = [
            email for email, data in verification_codes.items()
            if data["expires_at"] < current_time
        ]
        for email in expired_verifications:
            del verification_codes[email]
        
        # 만료된 인증 완료 상태 삭제
        expired_verified = [
            email for email, data in verified_emails.items()
            if data["expires_at"] < current_time
        ]
        for email in expired_verified:
            del verified_emails[email]

def generate_verification_code(length: int = 6) -> str:
    """인증번호 생성 (숫자만)"""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(email: str, verification_code: str) -> bool:
    """인증번호를 이메일로 전송"""
    try:
        print(f"📧 이메일 전송 시작: {email}")
        print(f"   SMTP 서버: {settings.SMTP_SERVER}:{settings.SMTP_PORT}")
        print(f"   사용자: {settings.SMTP_USERNAME}")
        
        # 이메일 메시지 생성
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "TeamUp 회원가입 이메일 인증"
        
        # 이메일 본문
        body = f"""
        안녕하세요! TeamUp 회원가입을 위한 이메일 인증번호입니다.
        
        인증번호: {verification_code}
        
        이 인증번호는 {settings.VERIFICATION_CODE_EXPIRE_MINUTES}분 후에 만료됩니다.
        인증번호를 입력하여 회원가입을 완료해주세요.
        
        감사합니다.
        TeamUp 팀
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # SMTP 서버 연결 및 이메일 전송 (타임아웃 설정 추가)
        print("   🔌 SMTP 서버 연결 중...")
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT, timeout=60)
        print("   🔒 TLS 시작...")
        server.starttls()
        print("   🔑 로그인 중...")
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        print("   📤 이메일 전송 중...")
        text = msg.as_string()
        server.sendmail(settings.SMTP_USERNAME, email, text)
        server.quit()
        print(f"✅ 이메일 전송 성공: {email}")
        
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP 인증 실패: {e}")
        print("   💡 Gmail 앱 비밀번호를 확인하고 2단계 인증이 활성화되어 있는지 확인하세요.")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}")
        return False

def store_verification_code(email: str, verification_code: str) -> bool:
    """인증번호를 메모리에 저장 (만료 시간 설정)"""
    try:
        with storage_lock:
            expires_at = datetime.now() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
            verification_codes[email] = {
                "code": verification_code,
                "expires_at": expires_at
            }
        return True
    except Exception as e:
        print(f"인증번호 저장 실패: {e}")
        return False

def verify_email_code(email: str, verification_code: str) -> bool:
    """이메일 인증번호 검증"""
    try:
        with storage_lock:
            if email not in verification_codes:
                print(f"❌ 인증번호를 찾을 수 없음: {email}")
                return False
            
            stored_data = verification_codes[email]
            stored_code = stored_data["code"]
            expires_at = stored_data["expires_at"]
            
            # 만료 시간 확인
            if datetime.now() > expires_at:
                print(f"❌ 인증번호 만료: {email}")
                del verification_codes[email]
                return False
            
            if stored_code == verification_code:
                # 인증 성공 시 저장소에서 삭제
                del verification_codes[email]
                print(f"✅ 인증번호 일치, 저장소에서 삭제: {email}")
                
                # 락을 유지한 상태에서 인증 완료 상태 저장
                expires_at_verified = datetime.now() + timedelta(days=7)
                verified_emails[email] = {
                    "verified_at": datetime.now(),
                    "expires_at": expires_at_verified
                }
                print(f"✅ 이메일 인증 완료 상태 저장: {email}")
                print(f"   저장된 데이터: {verified_emails[email]}")
                print(f"   현재 verified_emails 키: {list(verified_emails.keys())}")
                
                return True
            else:
                print(f"❌ 인증번호 불일치: {email}")
                return False
        
        return False
    except Exception as e:
        print(f"❌ 인증번호 검증 실패: {e}")
        return False

def is_email_verified(email: str) -> bool:
    """이메일이 이미 인증되었는지 확인"""
    try:
        print(f"🔍 이메일 인증 상태 확인 시작: {email}")
        print(f"   현재 verified_emails 키: {list(verified_emails.keys())}")
        
        with storage_lock:
            if email in verified_emails:
                verified_data = verified_emails[email]
                expires_at = verified_data["expires_at"]
                current_time = datetime.now()
                
                print(f"   인증 데이터: {verified_data}")
                print(f"   현재 시간: {current_time}")
                print(f"   만료 시간: {expires_at}")
                
                # 만료 시간 확인
                if current_time > expires_at:
                    del verified_emails[email]
                    print(f"❌ 이메일 인증 상태 만료: {email}")
                    return False
                
                print(f"✅ 이메일 인증 상태 확인: {email}")
                return True
            else:
                print(f"❌ 이메일 인증 상태 없음: {email}")
                return False
    except Exception as e:
        print(f"❌ 이메일 인증 상태 확인 실패: {e}")
        return False

# mark_email_as_verified 함수는 더 이상 사용되지 않음
# verify_email_code 내부에서 직접 처리하도록 변경됨
def mark_email_as_verified(email: str) -> bool:
    """이메일을 인증 완료 상태로 표시 (더 이상 사용되지 않음)"""
    print(f"⚠️ mark_email_as_verified는 더 이상 사용되지 않습니다: {email}")
    return False

# 백그라운드에서 주기적으로 만료된 데이터 정리
def start_cleanup_thread():
    """백그라운드 정리 스레드 시작"""
    def cleanup_loop():
        while True:
            time.sleep(60)  # 1분마다 실행
            cleanup_expired_data()
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()

# 서버 시작 시 정리 스레드 시작 (무한루프 방지를 위해 임시 비활성화)
# start_cleanup_thread() 
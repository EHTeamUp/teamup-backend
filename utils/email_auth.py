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
        
        # SMTP 서버 연결 및 이메일 전송
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.SMTP_USERNAME, email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"이메일 전송 실패: {e}")
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
        cleanup_expired_data()  # 만료된 데이터 정리
        
        with storage_lock:
            if email not in verification_codes:
                return False
            
            stored_data = verification_codes[email]
            stored_code = stored_data["code"]
            
            if stored_code == verification_code:
                # 인증 성공 시 저장소에서 삭제
                del verification_codes[email]
                return True
            
            return False
    except Exception as e:
        print(f"인증번호 검증 실패: {e}")
        return False

def is_email_verified(email: str) -> bool:
    """이메일이 이미 인증되었는지 확인"""
    try:
        cleanup_expired_data()  # 만료된 데이터 정리
        
        with storage_lock:
            return email in verified_emails
    except Exception as e:
        print(f"이메일 인증 상태 확인 실패: {e}")
        return False

def mark_email_as_verified(email: str) -> bool:
    """이메일을 인증 완료 상태로 표시"""
    try:
        with storage_lock:
            expires_at = datetime.now() + timedelta(hours=24)
            verified_emails[email] = {
                "verified_at": datetime.now(),
                "expires_at": expires_at
            }
        return True
    except Exception as e:
        print(f"이메일 인증 완료 표시 실패: {e}")
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

# 서버 시작 시 정리 스레드 시작
start_cleanup_thread() 
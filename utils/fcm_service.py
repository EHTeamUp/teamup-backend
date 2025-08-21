import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Dict, Any
import json
from config import settings

# Firebase 초기화 (한 번만 실행)
try:
    firebase_admin.get_app()
except ValueError:
    # Firebase 서비스 계정 키 파일이 있는 경우
    if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and settings.FIREBASE_CREDENTIALS_PATH:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    else:
        # 기본 앱으로 초기화 (환경 변수 사용)
        firebase_admin.initialize_app()

class FCMService:
    """Firebase Cloud Messaging 서비스"""
    
    @staticmethod
    def send_single_notification(
        token: str, 
        title: str, 
        body: str, 
        data: Dict[str, str] = None
    ) -> bool:
        """단일 디바이스에 알림 전송"""
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token
            )
            
            response = messaging.send(message)
            print(f"Successfully sent message: {response}")
            return True
            
        except Exception as e:
            print(f"Error sending FCM notification: {e}")
            return False
    
    @staticmethod
    def send_multicast_notification(
        tokens: List[str], 
        title: str, 
        body: str, 
        data: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """여러 디바이스에 알림 전송"""
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            
            result = {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": response.responses
            }
            
            print(f"Successfully sent {response.success_count} messages")
            if response.failure_count > 0:
                print(f"Failed to send {response.failure_count} messages")
                
            return result
            
        except Exception as e:
            print(f"Error sending multicast FCM notification: {e}")
            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "responses": []
            }
    
    @staticmethod
    def send_topic_notification(
        topic: str, 
        title: str, 
        body: str, 
        data: Dict[str, str] = None
    ) -> bool:
        """토픽 구독자들에게 알림 전송"""
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                topic=topic
            )
            
            response = messaging.send(message)
            print(f"Successfully sent topic message: {response}")
            return True
            
        except Exception as e:
            print(f"Error sending topic FCM notification: {e}")
            return False
    
    @staticmethod
    def subscribe_to_topic(tokens: List[str], topic: str) -> Dict[str, Any]:
        """토큰들을 토픽에 구독"""
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            
            result = {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "errors": response.errors
            }
            
            print(f"Successfully subscribed {response.success_count} tokens to topic: {topic}")
            if response.failure_count > 0:
                print(f"Failed to subscribe {response.failure_count} tokens")
                
            return result
            
        except Exception as e:
            print(f"Error subscribing to topic: {e}")
            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "errors": []
            }
    
    @staticmethod
    def unsubscribe_from_topic(tokens: List[str], topic: str) -> Dict[str, Any]:
        """토큰들을 토픽에서 구독 해제"""
        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            
            result = {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "errors": response.errors
            }
            
            print(f"Successfully unsubscribed {response.success_count} tokens from topic: {topic}")
            if response.failure_count > 0:
                print(f"Failed to unsubscribe {response.failure_count} tokens")
                
            return result
            
        except Exception as e:
            print(f"Error unsubscribing from topic: {e}")
            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "errors": []
            }


import requests
import json
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SlackNotifier:
    """Slack 알림 클래스"""
    
    def __init__(self, webhook_url: Optional[str] = None, channel: Optional[str] = None):
        self.webhook_url = webhook_url
        self.channel = channel
        
    def send_login_notification(self, username: str, organization: str, pc_id: str) -> bool:
        """
        로그인 알림 메시지를 Slack으로 전송
        
        Args:
            username: 사용자명
            organization: 소속
            pc_id: PC ID
            
        Returns:
            bool: 전송 성공 여부
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL이 설정되지 않았습니다.")
            return False
            
        message = f"🔑 *로그인 알림*\n"
        message += f"• 사용자: {username}\n"
        message += f"• 소속: {organization}\n"
        message += f"• PC: {pc_id}\n"
        message += f"• 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self._send_message(message)
    
    def send_logout_notification(self, username: str, organization: str, pc_id: str) -> bool:
        """
        로그아웃 알림 메시지를 Slack으로 전송
        
        Args:
            username: 사용자명
            organization: 소속
            pc_id: PC ID
            
        Returns:
            bool: 전송 성공 여부
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL이 설정되지 않았습니다.")
            return False
            
        message = f"🔓 *로그아웃 알림*\n"
        message += f"• 사용자: {username}\n"
        message += f"• 소속: {organization}\n"
        message += f"• PC: {pc_id}\n"
        message += f"• 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self._send_message(message)
    
    def send_system_notification(self, message: str) -> bool:
        """
        시스템 알림 메시지를 Slack으로 전송
        
        Args:
            message: 전송할 메시지
            
        Returns:
            bool: 전송 성공 여부
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL이 설정되지 않았습니다.")
            return False
            
        formatted_message = f"⚡ *시스템 알림*\n{message}"
        return self._send_message(formatted_message)
    
    def _send_message(self, message: str) -> bool:
        """
        실제 메시지 전송 처리
        
        Args:
            message: 전송할 메시지
            
        Returns:
            bool: 전송 성공 여부
        """
        try:
            payload = {
                "text": message,
                "username": "PC Control System",
                "icon_emoji": ":computer:"
            }
            
            if self.channel:
                payload["channel"] = self.channel
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack 메시지 전송 성공")
                return True
            else:
                logger.error(f"Slack 메시지 전송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Slack 메시지 전송 중 오류 발생: {str(e)}")
            return False
    
    def update_config(self, webhook_url: str, channel: Optional[str] = None):
        """
        Slack 설정 업데이트
        
        Args:
            webhook_url: 웹훅 URL
            channel: 채널명 (선택사항)
        """
        self.webhook_url = webhook_url
        self.channel = channel
        logger.info("Slack 설정이 업데이트되었습니다.")

# 전역 슬랙 알림 인스턴스
slack_notifier = SlackNotifier() 
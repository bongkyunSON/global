from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PCStatus(str, Enum):
    """PC 상태 열거형"""
    LOCKED = "locked"           # 잠금됨 (로그인 필요)
    LOGGED_IN = "logged_in"     # 로그인됨
    OFFLINE = "offline"         # 오프라인

class LoginRequest(BaseModel):
    """로그인 요청 모델"""
    pc_id: str
    username: str
    organization: str

class LoginResponse(BaseModel):
    """로그인 응답 모델"""
    success: bool
    message: str
    pc_id: str
    username: Optional[str] = None
    organization: Optional[str] = None

class PCInfo(BaseModel):
    """PC 정보 모델"""
    pc_id: str
    status: PCStatus
    username: Optional[str] = None
    organization: Optional[str] = None
    login_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    ip_address: Optional[str] = None

class LogoutRequest(BaseModel):
    """로그아웃 요청 모델"""
    pc_id: str

class HeartbeatRequest(BaseModel):
    """하트비트 요청 모델"""
    pc_id: str
    ip_address: str

class SlackConfig(BaseModel):
    """Slack 설정 모델"""
    webhook_url: str
    channel: str

class WSMessage(BaseModel):
    """WebSocket 메시지 모델"""
    type: str  # 'login', 'logout', 'heartbeat', 'pc_status_update'
    data: dict

class DashboardStats(BaseModel):
    """대시보드 통계 모델"""
    total_pcs: int
    online_pcs: int
    logged_in_pcs: int
    locked_pcs: int
    offline_pcs: int 
import asyncio
import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
from .models import WSMessage, PCInfo, PCStatus

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 연결들 (PC_ID -> WebSocket)
        self.active_connections: Dict[str, WebSocket] = {}
        # 관리자 대시보드 연결들
        self.admin_connections: Set[WebSocket] = set()
        # PC 정보 저장
        self.pc_info: Dict[str, PCInfo] = {}
        
    async def connect_pc(self, websocket: WebSocket, pc_id: str):
        """PC 클라이언트 연결"""
        await websocket.accept()
        self.active_connections[pc_id] = websocket
        
        # PC 정보 초기화
        self.pc_info[pc_id] = PCInfo(
            pc_id=pc_id,
            status=PCStatus.LOCKED,
            last_heartbeat=datetime.now()
        )
        
        logger.info(f"PC {pc_id} 연결됨")
        
        # 관리자들에게 PC 상태 업데이트 알림
        await self.broadcast_to_admins({
            "type": "pc_connected",
            "data": self.pc_info[pc_id].dict()
        })
        
    async def connect_admin(self, websocket: WebSocket):
        """관리자 대시보드 연결"""
        await websocket.accept()
        self.admin_connections.add(websocket)
        
        # 현재 PC 상태 정보 전송
        await self.send_to_admin(websocket, {
            "type": "initial_pc_status",
            "data": [pc.dict() for pc in self.pc_info.values()]
        })
        
        logger.info("관리자 대시보드 연결됨")
        
    def disconnect_pc(self, pc_id: str):
        """PC 클라이언트 연결 해제"""
        if pc_id in self.active_connections:
            del self.active_connections[pc_id]
            
        if pc_id in self.pc_info:
            self.pc_info[pc_id].status = PCStatus.OFFLINE
            
        logger.info(f"PC {pc_id} 연결 해제됨")
        
    def disconnect_admin(self, websocket: WebSocket):
        """관리자 대시보드 연결 해제"""
        self.admin_connections.discard(websocket)
        logger.info("관리자 대시보드 연결 해제됨")
        
    async def send_to_pc(self, pc_id: str, message: dict):
        """특정 PC에 메시지 전송"""
        if pc_id in self.active_connections:
            try:
                await self.active_connections[pc_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"PC {pc_id}로 메시지 전송 실패: {str(e)}")
                return False
        return False
        
    async def send_to_admin(self, websocket: WebSocket, message: dict):
        """특정 관리자에게 메시지 전송"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"관리자로 메시지 전송 실패: {str(e)}")
            
    async def broadcast_to_admins(self, message: dict):
        """모든 관리자에게 메시지 브로드캐스트"""
        if not self.admin_connections:
            return
            
        message_str = json.dumps(message)
        disconnected_admins = []
        
        for admin_ws in self.admin_connections:
            try:
                await admin_ws.send_text(message_str)
            except Exception as e:
                logger.error(f"관리자 브로드캐스트 실패: {str(e)}")
                disconnected_admins.append(admin_ws)
                
        # 연결이 끊어진 관리자들 제거
        for admin_ws in disconnected_admins:
            self.admin_connections.discard(admin_ws)
            
    async def broadcast_to_all_pcs(self, message: dict):
        """모든 PC에 메시지 브로드캐스트"""
        if not self.active_connections:
            return
            
        message_str = json.dumps(message)
        disconnected_pcs = []
        
        for pc_id, pc_ws in self.active_connections.items():
            try:
                await pc_ws.send_text(message_str)
            except Exception as e:
                logger.error(f"PC {pc_id} 브로드캐스트 실패: {str(e)}")
                disconnected_pcs.append(pc_id)
                
        # 연결이 끊어진 PC들 제거
        for pc_id in disconnected_pcs:
            self.disconnect_pc(pc_id)
            
    def update_pc_info(self, pc_id: str, **kwargs):
        """PC 정보 업데이트"""
        if pc_id in self.pc_info:
            for key, value in kwargs.items():
                if hasattr(self.pc_info[pc_id], key):
                    setattr(self.pc_info[pc_id], key, value)
        else:
            # 새로운 PC 정보 생성
            self.pc_info[pc_id] = PCInfo(pc_id=pc_id, status=PCStatus.LOCKED, **kwargs)
            
    def get_pc_info(self, pc_id: str) -> Optional[PCInfo]:
        """PC 정보 조회"""
        return self.pc_info.get(pc_id)
        
    def get_all_pc_info(self) -> Dict[str, PCInfo]:
        """모든 PC 정보 조회"""
        return self.pc_info.copy()
        
    def is_user_logged_in(self, username: str) -> Optional[str]:
        """사용자가 다른 PC에 로그인되어 있는지 확인"""
        for pc_id, pc_info in self.pc_info.items():
            if pc_info.status == PCStatus.LOGGED_IN and pc_info.username == username:
                return pc_id
        return None
        
    def get_dashboard_stats(self) -> dict:
        """대시보드 통계 정보 반환"""
        total_pcs = len(self.pc_info)
        online_pcs = len([pc for pc in self.pc_info.values() if pc.status != PCStatus.OFFLINE])
        logged_in_pcs = len([pc for pc in self.pc_info.values() if pc.status == PCStatus.LOGGED_IN])
        locked_pcs = len([pc for pc in self.pc_info.values() if pc.status == PCStatus.LOCKED])
        offline_pcs = len([pc for pc in self.pc_info.values() if pc.status == PCStatus.OFFLINE])
        
        return {
            "total_pcs": total_pcs,
            "online_pcs": online_pcs,
            "logged_in_pcs": logged_in_pcs,
            "locked_pcs": locked_pcs,
            "offline_pcs": offline_pcs
        }

# 전역 연결 관리자 인스턴스
connection_manager = ConnectionManager() 
import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from datetime import datetime
import uvicorn

from .models import (
    LoginRequest, LoginResponse, LogoutRequest, HeartbeatRequest,
    PCInfo, PCStatus, SlackConfig, DashboardStats
)
from .websocket_manager import connection_manager
from .slack_integration import slack_notifier

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="PC Control System",
    description="PC방용 로그인 제어 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "PC Control System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now()}

# === PC 관리 API ===

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """PC 로그인 처리"""
    try:
        # 중복 로그인 체크
        existing_pc = connection_manager.is_user_logged_in(request.username)
        if existing_pc:
            return LoginResponse(
                success=False,
                message=f"사용자 '{request.username}'이(가) 이미 PC-{existing_pc}에 로그인되어 있습니다.",
                pc_id=request.pc_id
            )
        
        # PC 정보 업데이트
        connection_manager.update_pc_info(
            request.pc_id,
            status=PCStatus.LOGGED_IN,
            username=request.username,
            organization=request.organization,
            login_time=datetime.now(),
            last_heartbeat=datetime.now()
        )
        
        # 로그인 성공 메시지를 해당 PC에 전송
        await connection_manager.send_to_pc(request.pc_id, {
            "type": "login_success",
            "data": {
                "username": request.username,
                "organization": request.organization
            }
        })
        
        # 관리자들에게 상태 업데이트 알림
        pc_info = connection_manager.get_pc_info(request.pc_id)
        if pc_info:
            await connection_manager.broadcast_to_admins({
                "type": "pc_status_update",
                "data": pc_info.dict()
            })
        
        # Slack 알림 전송
        slack_notifier.send_login_notification(
            request.username,
            request.organization,
            request.pc_id
        )
        
        logger.info(f"로그인 성공: {request.username} ({request.organization}) - PC: {request.pc_id}")
        
        return LoginResponse(
            success=True,
            message="로그인 성공",
            pc_id=request.pc_id,
            username=request.username,
            organization=request.organization
        )
        
    except Exception as e:
        logger.error(f"로그인 처리 중 오류: {str(e)}")
        return LoginResponse(
            success=False,
            message=f"로그인 처리 중 오류가 발생했습니다: {str(e)}",
            pc_id=request.pc_id
        )

@app.post("/api/logout", response_model=dict)
async def logout(request: LogoutRequest):
    """PC 로그아웃 처리"""
    try:
        pc_info = connection_manager.get_pc_info(request.pc_id)
        if not pc_info:
            return {"success": False, "message": "PC 정보를 찾을 수 없습니다."}
        
        # 로그아웃 처리 전에 사용자 정보 백업
        username = pc_info.username
        organization = pc_info.organization
        
        # PC 정보 업데이트
        connection_manager.update_pc_info(
            request.pc_id,
            status=PCStatus.LOCKED,
            username=None,
            organization=None,
            login_time=None,
            last_heartbeat=datetime.now()
        )
        
        # 로그아웃 메시지를 해당 PC에 전송
        await connection_manager.send_to_pc(request.pc_id, {
            "type": "logout",
            "data": {}
        })
        
        # 관리자들에게 상태 업데이트 알림
        updated_pc_info = connection_manager.get_pc_info(request.pc_id)
        if updated_pc_info:
            await connection_manager.broadcast_to_admins({
                "type": "pc_status_update",
                "data": updated_pc_info.dict()
            })
        
        # Slack 알림 전송
        if username and organization:
            slack_notifier.send_logout_notification(
                username,
                organization,
                request.pc_id
            )
        
        logger.info(f"로그아웃 성공: {username} - PC: {request.pc_id}")
        
        return {"success": True, "message": "로그아웃 성공"}
        
    except Exception as e:
        logger.error(f"로그아웃 처리 중 오류: {str(e)}")
        return {"success": False, "message": f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}"}

@app.post("/api/heartbeat")
async def heartbeat(request: HeartbeatRequest):
    """PC 하트비트 처리"""
    try:
        connection_manager.update_pc_info(
            request.pc_id,
            last_heartbeat=datetime.now(),
            ip_address=request.ip_address
        )
        
        return {"success": True, "message": "하트비트 처리 완료"}
        
    except Exception as e:
        logger.error(f"하트비트 처리 중 오류: {str(e)}")
        return {"success": False, "message": f"하트비트 처리 중 오류가 발생했습니다: {str(e)}"}

@app.get("/api/pcs", response_model=List[PCInfo])
async def get_all_pcs():
    """모든 PC 정보 조회"""
    try:
        pc_info_dict = connection_manager.get_all_pc_info()
        return list(pc_info_dict.values())
    except Exception as e:
        logger.error(f"PC 정보 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="PC 정보 조회 중 오류가 발생했습니다.")

@app.get("/api/pcs/{pc_id}", response_model=PCInfo)
async def get_pc_info(pc_id: str):
    """특정 PC 정보 조회"""
    try:
        pc_info = connection_manager.get_pc_info(pc_id)
        if not pc_info:
            raise HTTPException(status_code=404, detail="PC 정보를 찾을 수 없습니다.")
        return pc_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PC 정보 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="PC 정보 조회 중 오류가 발생했습니다.")

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """대시보드 통계 정보 조회"""
    try:
        stats = connection_manager.get_dashboard_stats()
        return DashboardStats(**stats)
    except Exception as e:
        logger.error(f"대시보드 통계 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="대시보드 통계 조회 중 오류가 발생했습니다.")

# === Slack 설정 API ===

@app.post("/api/slack/config")
async def update_slack_config(config: SlackConfig):
    """Slack 설정 업데이트"""
    try:
        slack_notifier.update_config(config.webhook_url, config.channel)
        
        # 설정 테스트 메시지 전송
        test_success = slack_notifier.send_system_notification(
            "Slack 설정이 성공적으로 업데이트되었습니다!"
        )
        
        if test_success:
            return {"success": True, "message": "Slack 설정이 업데이트되었습니다."}
        else:
            return {"success": False, "message": "Slack 설정은 저장되었지만 테스트 메시지 전송에 실패했습니다."}
            
    except Exception as e:
        logger.error(f"Slack 설정 업데이트 중 오류: {str(e)}")
        return {"success": False, "message": f"Slack 설정 업데이트 중 오류가 발생했습니다: {str(e)}"}

# === WebSocket 연결 ===

@app.websocket("/ws/pc/{pc_id}")
async def websocket_pc_endpoint(websocket: WebSocket, pc_id: str):
    """PC 클라이언트 WebSocket 연결"""
    await connection_manager.connect_pc(websocket, pc_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # 메시지 타입에 따른 처리
                if message.get("type") == "heartbeat":
                    connection_manager.update_pc_info(
                        pc_id,
                        last_heartbeat=datetime.now(),
                        ip_address=message.get("data", {}).get("ip_address")
                    )
                
                elif message.get("type") == "status_update":
                    # PC 상태 업데이트
                    status_data = message.get("data", {})
                    connection_manager.update_pc_info(pc_id, **status_data)
                    
                    # 관리자들에게 상태 업데이트 알림
                    pc_info = connection_manager.get_pc_info(pc_id)
                    if pc_info:
                        await connection_manager.broadcast_to_admins({
                            "type": "pc_status_update",
                            "data": pc_info.dict()
                        })
                
            except json.JSONDecodeError:
                logger.warning(f"PC {pc_id}에서 잘못된 JSON 메시지 수신")
                
    except WebSocketDisconnect:
        connection_manager.disconnect_pc(pc_id)
        
        # 관리자들에게 PC 연결 해제 알림
        await connection_manager.broadcast_to_admins({
            "type": "pc_disconnected",
            "data": {"pc_id": pc_id}
        })

@app.websocket("/ws/admin")
async def websocket_admin_endpoint(websocket: WebSocket):
    """관리자 대시보드 WebSocket 연결"""
    await connection_manager.connect_admin(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # 관리자 명령 처리
                if message.get("type") == "force_logout":
                    pc_id = message.get("data", {}).get("pc_id")
                    if pc_id:
                        # 강제 로그아웃 명령을 해당 PC에 전송
                        await connection_manager.send_to_pc(pc_id, {
                            "type": "force_logout",
                            "data": {}
                        })
                        
                        # PC 정보 업데이트
                        connection_manager.update_pc_info(
                            pc_id,
                            status=PCStatus.LOCKED,
                            username=None,
                            organization=None,
                            login_time=None
                        )
                        
                        # 모든 관리자에게 상태 업데이트 알림
                        pc_info = connection_manager.get_pc_info(pc_id)
                        if pc_info:
                            await connection_manager.broadcast_to_admins({
                                "type": "pc_status_update",
                                "data": pc_info.dict()
                            })
                
            except json.JSONDecodeError:
                logger.warning("관리자에서 잘못된 JSON 메시지 수신")
                
    except WebSocketDisconnect:
        connection_manager.disconnect_admin(websocket)

# === 애플리케이션 시작 ===

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
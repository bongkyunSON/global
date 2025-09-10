from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import asyncio
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from dotenv import load_dotenv
import uvicorn
from datetime import datetime, timedelta
import pytz
import json
from pathlib import Path
from collections import defaultdict, Counter
from urllib.parse import quote
import unicodedata

# 환경변수 로드
load_dotenv()

app = FastAPI(title="PC방 제어시스템")

# WebSocket 연결 관리자
class ConnectionManager:
    def __init__(self):
        # pc_number를 키로 사용하는 딕셔너리
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, pc_number: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[pc_number] = websocket
        print(f"🖥️ PC #{pc_number} connected.")

    def disconnect(self, pc_number: int):
        if pc_number in self.active_connections:
            del self.active_connections[pc_number]
            print(f"🖥️ PC #{pc_number} disconnected.")

    async def send_personal_message(self, message: str, pc_number: int):
        if pc_number in self.active_connections:
            websocket = self.active_connections[pc_number]
            await websocket.send_text(message)
            print(f"📤 Sent '{message}' to PC #{pc_number}")

manager = ConnectionManager()

@app.websocket("/ws/{pc_number}")
async def websocket_endpoint(websocket: WebSocket, pc_number: int):
    """클라이언트 PC와 웹소켓 연결을 설정하는 엔드포인트"""
    await manager.connect(pc_number, websocket)
    try:
        while True:
            # 클라이언트로부터 메시지를 기다리며 연결을 유지합니다.
            # 실제로는 클라이언트가 메시지를 보내지 않으므로, 연결 상태 확인용입니다.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(pc_number)


# 로그인 요청 모델
class LoginRequest(BaseModel):
    name: str
    affiliation: str
    contact: Optional[str] = ""  # 선택적 필드, 기본값은 빈 문자열
    email: Optional[str] = ""  # 선택적 필드, 기본값은 빈 문자열
    pc_number: int

# 호출 요청 모델
class CallRequest(BaseModel):
    name: str
    affiliation: str
    contact: Optional[str] = ""  # 선택적 필드, 기본값은 빈 문자열
    email: Optional[str] = ""  # 선택적 필드, 기본값은 빈 문자열
    pc_number: int
    message: str = "호출요청"

# 비회원 호출 요청 모델
class GuestCallRequest(BaseModel):
    pc_number: int
    message: str = "비회원 호출"

# 슬랙 설정
bot_token = os.getenv('SLACK_BOT_TOKEN')
app_token = os.getenv('SLACK_APP_TOKEN')

# slack_channel = os.getenv('SLACK_CHANNEL', 'test')
# call_channel = os.getenv('CALL_CHANNEL', '호출')
# feedback_channel = os.getenv('FEEDBACK_CHANNEL', '피드백')

slack_channel = os.getenv('SLACK_CHANNEL', '5-온콘-로그인')  # 기본값: test
call_channel = os.getenv('CALL_CHANNEL', '6-온콘-호출')  # 기본값: 호출
feedback_channel = os.getenv('FEEDBACK_CHANNEL', '7-온콘-피드백')


if not bot_token or not app_token:
    print("⚠️ 슬랙 토큰이 설정되지 않았습니다. .env 파일을 확인해주세요.")

slack_app = AsyncApp(token=bot_token)

def load_config():
    """설정 파일 로드"""
    # Docker 환경과 로컬 환경 모두 지원
    config_file = Path("config.json") if Path("config.json").exists() else Path("../config.json")
    default_config = {
        "pc_number": 1,
        "server_port": 8000,
        "auto_start": True,
        "fullscreen": True
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        except:
            pass
            
    return default_config

@app.get("/api/config")
async def get_config():
    """설정 정보 반환"""
    config = load_config()
    return {"pc_number": config["pc_number"]}

async def send_slack_notification(message_or_name, affiliation=None, contact=None, email=None, pc_number=None, action="로그인", is_feedback=False):
    """슬랙으로 알림 전송 (로그인/로그아웃 및 피드백)"""
    try:
        if is_feedback:
            # 피드백 메시지인 경우 - message_or_name이 완성된 메시지
            message = message_or_name
            # 환경변수로 설정된 피드백 채널 사용
            target_channel = feedback_channel
        else:
            # 로그인/로그아웃 알림인 경우
            name = message_or_name
            # 한국 시간대 설정
            korea_tz = pytz.timezone('Asia/Seoul')
            current_time = datetime.now(korea_tz).strftime("%Y-%m-%d %H:%M:%S")
            
            # 연락처와 이메일이 없거나 빈 문자열인 경우 처리
            contact_text = f"\n연락처: {contact}" if contact and contact.strip() else ""
            email_text = f"\n이메일: {email}" if email and email.strip() else ""
            
            if action == "로그인":
                message = f"🟢 *PC방 로그인 알림*\n이름: {name}\n소속: {affiliation}{contact_text}{email_text}\n{pc_number}번 PC에서 로그인하였습니다.\n시간: {current_time}"
            else:
                message = f"🔴 *PC방 로그아웃 알림*\n이름: {name}\n소속: {affiliation}{contact_text}{email_text}\n{pc_number}번 PC에서 로그아웃하였습니다.\n시간: {current_time}"
            
            target_channel = slack_channel
        
        await slack_app.client.chat_postMessage(
            channel=target_channel,
            text=message
        )
        return True
    except Exception as e:
        print(f"슬랙 알림 전송 실패: {e}")
        return False

async def send_call_notification(name: str, affiliation: str, contact: Optional[str], email: Optional[str], pc_number: int, message: str = "호출요청"):
    """호출 채널로 알림 전송"""
    try:
        print(f"📤 슬랙 호출 메시지 전송 시작...")
        print(f"채널: {call_channel}")
        
        # 한국 시간대 설정
        korea_tz = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(korea_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        # 연락처와 이메일이 없거나 빈 문자열인 경우 처리
        contact_text = f"\n연락처: {contact}" if contact and contact.strip() else ""
        email_text = f"\n이메일: {email}" if email and email.strip() else ""
        
        call_message = f"📢 *호출 요청*\n이름: {name}\n소속: {affiliation}{contact_text}{email_text}\n{pc_number}번 PC에서 호출하였습니다.\n메시지: {message}\n시간: {current_time}"
        
        print(f"전송할 메시지: {call_message}")
        
        # 슬랙 봇 토큰 확인
        if not bot_token:
            print("❌ 슬랙 봇 토큰이 설정되지 않았습니다!")
            return False
        
        result = await slack_app.client.chat_postMessage(
            channel=call_channel,  # 호출 전용 채널 (환경변수)
            text=call_message
        )
        
        print(f"✅ 슬랙 메시지 전송 성공: {result}")
        return True
        
    except Exception as e:
        print(f"❌ 호출 알림 전송 실패: {e}")
        print(f"에러 타입: {type(e)}")
        print(f"슬랙 봇 토큰 존재 여부: {bool(bot_token)}")
        print(f"호출 채널: {call_channel}")
        return False

async def send_guest_call_notification(pc_number: int, message: str = "비회원 호출"):
    """비회원 호출 채널로 알림 전송"""
    try:
        print(f"📤 비회원 슬랙 호출 메시지 전송 시작...")
        print(f"채널: {call_channel}")
        
        # 한국 시간대 설정
        korea_tz = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(korea_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        call_message = f"📢 *비회원 호출 요청*\n{pc_number}번 PC에서 비회원이 호출하였습니다.\n메시지: {message}\n시간: {current_time}"
        
        print(f"전송할 메시지: {call_message}")
        
        # 슬랙 봇 토큰 확인
        if not bot_token:
            print("❌ 슬랙 봇 토큰이 설정되지 않았습니다!")
            return False
        
        result = await slack_app.client.chat_postMessage(
            channel=call_channel,  # 호출 전용 채널 (환경변수)
            text=call_message
        )
        
        print(f"✅ 비회원 슬랙 메시지 전송 성공: {result}")
        return True
        
    except Exception as e:
        print(f"❌ 비회원 호출 알림 전송 실패: {e}")
        print(f"에러 타입: {type(e)}")
        print(f"슬랙 봇 토큰 존재 여부: {bool(bot_token)}")
        print(f"호출 채널: {call_channel}")
        return False

@app.post("/api/login")
async def login(request: LoginRequest):
    """로그인 API"""
    try:
        # 로그인 기록 저장
        login_record = {
            "timestamp": datetime.now(pytz.timezone('Asia/Seoul')).isoformat(),
            "name": request.name,
            "affiliation": request.affiliation,
            "contact": request.contact,
            "email": request.email,
            "pc_number": request.pc_number
        }
        login_history.append(login_record)
        
        # 로그인 기록을 파일에 저장
        save_login_history()
        
        # 슬랙 알림 전송
        success = await send_slack_notification(
            request.name, 
            request.affiliation, 
            request.contact,
            request.email,
            request.pc_number, 
            "로그인"
        )
        
        if success:
            return {"status": "success", "message": "로그인이 완료되었습니다."}
        else:
            return {"status": "warning", "message": "로그인은 되었지만 슬랙 알림 전송에 실패했습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그인 처리 중 오류가 발생했습니다: {str(e)}")

@app.post("/api/logout")
async def logout(request: LoginRequest):
    """로그아웃 API"""
    try:
        # WebSocket을 통해 해당 PC 클라이언트에 재부팅 명령 전송
        await manager.send_personal_message("reboot", request.pc_number)
        
        # 슬랙 알림 전송
        success = await send_slack_notification(
            request.name, 
            request.affiliation, 
            request.contact,
            request.email,
            request.pc_number, 
            "로그아웃"
        )
        
        if success:
            return {"status": "success", "message": "로그아웃이 완료되었습니다."}
        else:
            return {"status": "warning", "message": "로그아웃은 되었지만 슬랙 알림 전송에 실패했습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}")

@app.post("/api/call")
async def call_staff(request: CallRequest):
    """호출 API"""
    try:
        print(f"🔔 호출 요청 받음: {request.name} ({request.affiliation}) - {request.message}")
        
        # 호출 기록 저장
        korea_tz = pytz.timezone('Asia/Seoul')
        call_record = {
            "timestamp": datetime.now(korea_tz).isoformat(),
            "name": request.name,
            "affiliation": request.affiliation,
            "contact": request.contact or "",
            "email": request.email or "",
            "pc_number": request.pc_number,
            "message": request.message,
            "type": "member"
        }
        
        call_history.append(call_record)
        save_call_history()
        
        # 호출 알림 전송
        success = await send_call_notification(
            request.name,
            request.affiliation,
            request.contact,
            request.email,
            request.pc_number,
            request.message
        )
        
        if success:
            print(f"✅ 호출 전송 성공: {request.name}")
            return {"status": "success", "message": "호출이 전송되었습니다."}
        else:
            print(f"❌ 호출 전송 실패: {request.name}")
            return {"status": "error", "message": "호출 전송에 실패했습니다."}
    except Exception as e:
        print(f"❌ 호출 API 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"호출 처리 중 오류가 발생했습니다: {str(e)}")

@app.post("/api/guest-call")
async def guest_call_staff(request: GuestCallRequest):
    """비회원 호출 API"""
    try:
        print(f"🔔 비회원 호출 요청 받음: {request.pc_number}번 PC - {request.message}")
        
        # 비회원 호출 기록 저장
        korea_tz = pytz.timezone('Asia/Seoul')
        call_record = {
            "timestamp": datetime.now(korea_tz).isoformat(),
            "name": "비회원",
            "affiliation": "비회원",
            "contact": "",
            "email": "",
            "pc_number": request.pc_number,
            "message": request.message,
            "type": "guest"
        }
        
        call_history.append(call_record)
        save_call_history()
        
        # 비회원 호출 알림 전송
        success = await send_guest_call_notification(
            request.pc_number,
            request.message
        )
        
        if success:
            print(f"✅ 비회원 호출 전송 성공: {request.pc_number}번 PC")
            return {"status": "success", "message": "호출이 전송되었습니다."}
        else:
            print(f"❌ 비회원 호출 전송 실패: {request.pc_number}번 PC")
            return {"status": "error", "message": "호출 전송에 실패했습니다."}
    except Exception as e:
        print(f"❌ 비회원 호출 API 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"호출 처리 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/shorts-images")
async def get_shorts_images():
    """숏츠 이미지 갤러리 데이터 API"""
    try:
        # Docker 환경과 로컬 환경 모두 지원
        shorts_dir = "image/shorts" if os.path.exists("image/shorts") else "../image/shorts"
        
        if not os.path.exists(shorts_dir):
            raise HTTPException(status_code=404, detail="shorts 디렉토리를 찾을 수 없습니다.")
        
        galleries = []
        
        # 디렉토리 목록을 가져와서 정렬 (01_, 02_, ... 10_ 순서)
        folders = [f for f in os.listdir(shorts_dir) if os.path.isdir(os.path.join(shorts_dir, f)) and f.startswith(('01_', '02_', '03_', '04_', '05_', '06_', '07_', '08_', '09_', '10_'))]
        folders.sort(key=lambda x: int(x.split('_')[0]))
        
        for folder in folders:
            # 유니코드 정규화 (NFC)
            norm_folder = unicodedata.normalize('NFC', folder)
            folder_path = os.path.join(shorts_dir, norm_folder)
            images = []
            
            # 각 폴더 내의 이미지 파일들을 찾음
            for file in os.listdir(folder_path):
                # macOS 숨겨진 파일 (._ 접두사) 및 시스템 파일 제외
                if file.startswith(('.', '_.')):
                    continue
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    # 유니코드 정규화 (NFC) 및 URL 인코딩
                    norm_file = unicodedata.normalize('NFC', file)
                    
                    # 웹에서 접근 가능한 경로로 변환 (URL 인코딩 포함)
                    image_url = f"/assets/shorts/{quote(norm_folder)}/{quote(norm_file)}"
                    images.append({
                        "filename": norm_file,
                        "url": image_url
                    })
            
            # 이미지 순서 정렬 (_main, _top, _bottom 순서)
            images.sort(key=lambda x: ('_main' in x['filename'], '_top' in x['filename'], '_bottom' in x['filename']))
            
            galleries.append({
                "id": len(galleries) + 1,
                "title": folder,
                "folder": folder,
                "images": images
            })
        
        return {"galleries": galleries}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 데이터 로드 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/download-template/{template_number}")
async def download_template(template_number: int):
    """숏츠 템플릿 zip 파일 다운로드 API"""
    try:
        # 템플릿 번호 검증 (1-10)
        if template_number < 1 or template_number > 10:
            raise HTTPException(status_code=400, detail="템플릿 번호는 1부터 10까지만 가능합니다.")
        
        # Docker 환경과 로컬 환경 모두 지원
        base_dir = "image/shorts/다운로드/최종_온콘 숏츠 템플릿 최적화" if os.path.exists("image/shorts/다운로드/최종_온콘 숏츠 템플릿 최적화") else "../image/shorts/다운로드/최종_온콘 숏츠 템플릿 최적화"
        
        # 템플릿 번호에 따른 파일명 매핑
        template_files = {
            1: "1_기본프리셋.zip",
            2: "2_정책 인사이트.zip", 
            3: "3_세미나 포럼.zip",
            4: "4_이슈 브리핑.zip",
            5: "5_문화 홍보.zip",
            6: "6_팩트체크.zip",
            7: "7_이슈 고발.zip",
            8: "8_산업 리포트.zip",
            9: "9_현장 스토리.zip",
            10: "10_디지털 세션.zip"
        }
        
        zip_filename = template_files.get(template_number)
        if not zip_filename:
            raise HTTPException(status_code=404, detail="해당 템플릿을 찾을 수 없습니다.")
        
        zip_file_path = os.path.join(base_dir, zip_filename)
        
        # 파일 존재 확인
        if not os.path.exists(zip_file_path):
            raise HTTPException(status_code=404, detail=f"템플릿 파일을 찾을 수 없습니다: {zip_filename}")
        
        # 한글 파일명을 위한 URL 인코딩 처리
        encoded_filename = quote(zip_filename.encode('utf-8'))
        
        # 다운로드 기록 저장
        try:
            korea_tz = pytz.timezone('Asia/Seoul')
            template_titles = {
                1: "1번 기본 프리셋",
                2: "2번 정책 인사이트",
                3: "3번 세미나 포럼",
                4: "4번 이슈 브리핑",
                5: "5번 문화 홍보",
                6: "6번 펙트체크",
                7: "7번 이슈 고발",
                8: "8번 산업 리포트",
                9: "9번 현장 스토리",
                10: "10번 디지털 세션",
            }
            download_record = {
                "timestamp": datetime.now(korea_tz).isoformat(),
                "template_number": template_number,
                "template_title": template_titles.get(template_number, str(template_number)),
                "filename": zip_filename,
            }
            download_history.append(download_record)
            save_download_history()
        except Exception as log_err:
            print(f"⚠️ 다운로드 기록 저장 실패: {log_err}")

        # 파일 다운로드 응답
        return FileResponse(
            path=zip_file_path,
            filename=zip_filename,
            media_type='application/zip',
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"템플릿 다운로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"템플릿 다운로드 중 오류가 발생했습니다: {str(e)}")

@app.get("/graph/download", response_class=HTMLResponse)
async def download_graph_page():
    """다운로드 통계 페이지 반환"""
    try:
        with open(f"{frontend_dir}/download.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="다운로드 통계 페이지를 찾을 수 없습니다.")

@app.get("/download", response_class=HTMLResponse)
async def download_page():
    """다운로드 통계 페이지 반환 (단축 경로)"""
    try:
        with open(f"{frontend_dir}/download.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="다운로드 통계 페이지를 찾을 수 없습니다.")

@app.get("/api/download-statistics")
async def get_download_statistics(period: str = "week"):
    """다운로드 통계 데이터 API (일/주/월/템플릿별)"""
    try:
        # 현재 시간 (한국 시간)
        now = datetime.now(pytz.timezone('Asia/Seoul'))
        today = now.date()

        # 기간 설정
        if period == "month":
            days_back = 30
            period_name = "최근 30일"
        elif period == "year":
            days_back = 365
            period_name = "최근 12개월"
        else:  # week
            days_back = 7
            period_name = "최근 7일"

        period_ago = today - timedelta(days=days_back)

        # 총 다운로드 수
        total_downloads = len(download_history)

        # 기간별 다운로드 수 및 일별 데이터
        daily_counts = defaultdict(int)
        template_counts = defaultdict(int)

        for record in download_history:
            record_date = datetime.fromisoformat(record["timestamp"]).date()
            if period == "year":
                # 연간 통계를 위해 template_counts는 전체 누적, daily_counts는 해당 연도 기간만
                template_counts[record.get("template_title") or str(record.get("template_number"))] += 1
                if record_date.year == today.year:
                    year_month = record_date.strftime("%Y-%m")
            if period != "year":
                if record_date >= period_ago:
                    daily_counts[record_date.isoformat()] += 1
                    template_counts[record.get("template_title") or str(record.get("template_number"))] += 1

        # 일별 데이터
        daily_data = []
        if period != "year":
            for i in range(days_back):
                date = (today - timedelta(days=days_back-1-i)).isoformat()
                daily_data.append({
                    "date": date,
                    "count": daily_counts[date]
                })

        # 월별 데이터 (년도 탭용)
        monthly_data = []
        if period == "year":
            current_year = today.year
            monthly_counts = defaultdict(int)
            for record in download_history:
                record_date = datetime.fromisoformat(record["timestamp"]).date()
                if record_date.year == current_year:
                    year_month = record_date.strftime("%Y-%m")
                    monthly_counts[year_month] += 1
            for month in range(1, 12+1):
                year_month = f"{current_year}-{month:02d}"
                monthly_data.append({
                    "month": year_month,
                    "count": monthly_counts[year_month]
                })

        # 기간 합계
        if period == "year":
            period_downloads = sum(item["count"] for item in monthly_data)
        else:
            period_downloads = sum(item["count"] for item in daily_data)

        return {
            "totalDownloads": total_downloads,
            "periodDownloads": period_downloads,
            "dailyData": daily_data,
            "monthlyData": monthly_data,
            "templateData": dict(template_counts),
            "period": period,
            "periodName": period_name
        }
    except Exception as e:
        print(f"다운로드 통계 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="다운로드 통계를 생성하는 중 오류가 발생했습니다.")

@app.get("/api/downloads")
async def get_downloads():
    """다운로드 상세 목록 API (최신순)"""
    try:
        # 최신순으로 정렬
        sorted_downloads = sorted(
            download_history,
            key=lambda x: x["timestamp"],
            reverse=True
        )
        return {"downloads": sorted_downloads}
    except Exception as e:
        print(f"다운로드 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="다운로드 목록을 조회하는 중 오류가 발생했습니다.")

@app.get("/api/health")
async def health_check():
    """헬스체크 API"""
    return {"status": "healthy", "message": "PC방 제어시스템이 정상 작동중입니다."}

# 정적 파일 서빙 (프론트엔드 / 이미지)
# Docker 환경과 로컬 환경 모두 지원
frontend_dir = "frontend" if os.path.exists("frontend") else "../frontend"
frontend_shorts_dir = "frontend_shorts" if os.path.exists("frontend_shorts") else "../frontend_shorts"

app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# 숏츠 갤러리 정적 파일 서빙
if os.path.exists(frontend_shorts_dir):
    app.mount("/shorts-static", StaticFiles(directory=frontend_shorts_dir), name="shorts-static")

# 이미지(에셋) 서빙
image_dir = "image" if os.path.exists("image") else "../image"
if os.path.exists(image_dir):
    app.mount("/assets", StaticFiles(directory=image_dir), name="assets")

# 사용자 로그인 기록 저장
login_history = []
LOGIN_DATA_FILE = "login_history.json"

# 피드백 기록 저장
feedback_history = []
FEEDBACK_DATA_FILE = "feedback_history.json"

# 호출 기록 저장
call_history = []
CALL_DATA_FILE = "call_history.json"

# 다운로드 기록 저장
download_history = []
DOWNLOAD_DATA_FILE = "download_history.json"

# 베이스 로그인 데이터 로드
def load_base_login_history():
    """베이스 로그인 기록을 파일에서 로드"""
    try:
        if os.path.exists("base_login_history.json"):
            with open("base_login_history.json", 'r', encoding='utf-8') as f:
                base_data = json.load(f)
                print(f"📊 베이스 로그인 기록 {len(base_data)}개를 로드했습니다.")
                return base_data
        else:
            print("⚠️ 베이스 로그인 기록 파일이 없습니다.")
            return []
    except Exception as e:
        print(f"❌ 베이스 로그인 기록 로드 실패: {e}")
        return []

# 로그인 데이터 파일에서 로드
def load_login_history():
    """기존 로그인 기록을 파일에서 로드"""
    global login_history
    try:
        if os.path.exists(LOGIN_DATA_FILE):
            with open(LOGIN_DATA_FILE, 'r', encoding='utf-8') as f:
                login_history = json.load(f)
                print(f"📊 기존 로그인 기록 {len(login_history)}개를 로드했습니다.")
        else:
            print("📊 새로운 로그인 기록 파일을 생성합니다.")
            login_history = []
    except Exception as e:
        print(f"❌ 로그인 기록 로드 실패: {e}")
        login_history = []

# 로그인 데이터 파일에 저장
def save_login_history():
    """로그인 기록을 파일에 저장"""
    try:
        with open(LOGIN_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(login_history, f, ensure_ascii=False, indent=2)
        print(f"💾 로그인 기록 {len(login_history)}개를 저장했습니다.")
    except Exception as e:
        print(f"❌ 로그인 기록 저장 실패: {e}")

def load_feedback_history():
    """기존 피드백 기록을 파일에서 로드"""
    global feedback_history
    try:
        if os.path.exists(FEEDBACK_DATA_FILE):
            with open(FEEDBACK_DATA_FILE, 'r', encoding='utf-8') as f:
                feedback_history = json.load(f)
                print(f"📝 기존 피드백 기록 {len(feedback_history)}개를 로드했습니다.")
        else:
            print("📝 새로운 피드백 기록 파일을 생성합니다.")
            feedback_history = []
    except Exception as e:
        print(f"❌ 피드백 기록 로드 실패: {e}")
        feedback_history = []

def save_feedback_history():
    """피드백 기록을 파일에 저장"""
    try:
        with open(FEEDBACK_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(feedback_history, f, ensure_ascii=False, indent=2)
        print(f"💾 피드백 기록 {len(feedback_history)}개를 저장했습니다.")
    except Exception as e:
        print(f"❌ 피드백 기록 저장 실패: {e}")

def load_call_history():
    """기존 호출 기록을 파일에서 로드"""
    global call_history
    try:
        if os.path.exists(CALL_DATA_FILE):
            with open(CALL_DATA_FILE, 'r', encoding='utf-8') as f:
                call_history = json.load(f)
                print(f"📞 기존 호출 기록 {len(call_history)}개를 로드했습니다.")
        else:
            print("📞 새로운 호출 기록 파일을 생성합니다.")
            call_history = []
    except Exception as e:
        print(f"❌ 호출 기록 로드 실패: {e}")
        call_history = []

def save_call_history():
    """호출 기록을 파일에 저장"""
    try:
        with open(CALL_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(call_history, f, ensure_ascii=False, indent=2)
        print(f"💾 호출 기록 {len(call_history)}개를 저장했습니다.")
    except Exception as e:
        print(f"❌ 호출 기록 저장 실패: {e}")

def load_download_history():
    """기존 다운로드 기록을 파일에서 로드"""
    global download_history
    try:
        if os.path.exists(DOWNLOAD_DATA_FILE):
            with open(DOWNLOAD_DATA_FILE, 'r', encoding='utf-8') as f:
                download_history = json.load(f)
                print(f"⬇️ 기존 다운로드 기록 {len(download_history)}개를 로드했습니다.")
        else:
            print("⬇️ 새로운 다운로드 기록 파일을 생성합니다.")
            download_history = []
    except Exception as e:
        print(f"❌ 다운로드 기록 로드 실패: {e}")
        download_history = []

def save_download_history():
    """다운로드 기록을 파일에 저장"""
    try:
        with open(DOWNLOAD_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(download_history, f, ensure_ascii=False, indent=2)
        print(f"💾 다운로드 기록 {len(download_history)}개를 저장했습니다.")
    except Exception as e:
        print(f"❌ 다운로드 기록 저장 실패: {e}")

# 서버 시작 시 기존 데이터 로드
load_login_history()
load_feedback_history()
load_call_history()
load_download_history()

# 데이터 백업 함수 (선택적)
def backup_login_history():
    """로그인 기록 백업 생성"""
    try:
        backup_filename = f"login_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(login_history, f, ensure_ascii=False, indent=2)
        print(f"📦 백업 파일 생성: {backup_filename}")
        return backup_filename
    except Exception as e:
        print(f"❌ 백업 생성 실패: {e}")
        return None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """루트 페이지 - 로그인 폼 반환"""
    try:
        html_path = f"{frontend_dir}/index.html"
        with open(html_path, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>프론트엔드 파일을 찾을 수 없습니다.</h1>", status_code=404)

@app.get("/shorts", response_class=HTMLResponse)
async def read_shorts():
    """숏츠 갤러리 페이지"""
    try:
        html_path = f"{frontend_shorts_dir}/index.html"
        with open(html_path, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>숏츠 갤러리 페이지를 찾을 수 없습니다.</h1>", status_code=404)

@app.get("/theme", response_class=HTMLResponse)
async def theme_page():
    """테마 선택 페이지"""
    try:
        html_path = f"{frontend_dir}/theme.html"
        with open(html_path, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>테마 선택 페이지를 찾을 수 없습니다.</h1>", status_code=404)

@app.get("/favicon.ico")
async def get_favicon():
    """favicon.ico 404 에러 방지"""
    return HTMLResponse("", status_code=204)

@app.post("/api/feedback")
async def send_feedback(request: Request):
    """피드백을 슬랙으로 전송"""
    try:
        data = await request.json()
        feedback_text = data.get('feedback', '')
        feedback_type = data.get('type', 'other')
        user_info = data.get('user', {})
        timestamp = data.get('timestamp', '')
        
        if not feedback_text.strip():
            raise HTTPException(status_code=400, detail="피드백 내용이 필요합니다.")
        
        # 카테고리 이모지 매핑
        type_emojis = {
            'suggestion': '💡',
            'bug': '🐛', 
            'improvement': '⚡',
            'other': '💬'
        }
        
        type_names = {
            'suggestion': '제안사항',
            'bug': '버그 신고',
            'improvement': '개선사항', 
            'other': '기타'
        }
        
        emoji = type_emojis.get(feedback_type, '💬')
        type_name = type_names.get(feedback_type, '기타')
        
        # 슬랙 메시지 구성
        message = f"""
🗨️ **새로운 피드백이 도착했습니다!**

{emoji} **카테고리**: {type_name}

📝 **내용**:
{feedback_text}

👤 **사용자 정보**:
• 이름: {user_info.get('name', 'N/A')}
• 소속: {user_info.get('affiliation', 'N/A')}
• 연락처: {user_info.get('contact', 'N/A')}
• 이메일: {user_info.get('email', 'N/A')}

🕒 **전송 시간**: {timestamp}
        """.strip()
        
        # 피드백 기록 저장
        korea_tz = pytz.timezone('Asia/Seoul')
        feedback_record = {
            "timestamp": datetime.now(korea_tz).isoformat(),
            "feedback": feedback_text,
            "type": feedback_type,
            "type_name": type_name,
            "user": {
                "name": user_info.get('name', 'N/A'),
                "affiliation": user_info.get('affiliation', 'N/A'),
                "contact": user_info.get('contact', 'N/A'),
                "email": user_info.get('email', 'N/A')
            }
        }
        
        feedback_history.append(feedback_record)
        save_feedback_history()
        
        # 슬랙으로 피드백 전송 (피드백 채널 사용)
        await send_slack_notification(message, is_feedback=True)
        
        return {"status": "success", "message": "피드백이 성공적으로 전송되었습니다."}
        
    except Exception as e:
        print(f"피드백 전송 오류: {e}")
        raise HTTPException(status_code=500, detail="피드백 전송 중 오류가 발생했습니다.")

@app.get("/graph", response_class=HTMLResponse)
async def graph_page():
    """통계 페이지 반환"""
    try:
        with open(f"{frontend_dir}/graph.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="통계 페이지를 찾을 수 없습니다.")

@app.get("/graph/feedback", response_class=HTMLResponse)
async def feedback_page():
    """피드백 전용 페이지 반환"""
    try:
        with open(f"{frontend_dir}/feedback.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="피드백 페이지를 찾을 수 없습니다.")

@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page_short():
    """피드백 페이지 반환 (단축 경로)"""
    try:
        with open(f"{frontend_dir}/feedback.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="피드백 페이지를 찾을 수 없습니다.")

@app.get("/api/statistics")
async def get_statistics(period: str = "week"):
    """사용자 통계 데이터 API"""
    try:
        # 베이스 데이터와 실제 데이터 합치기
        base_data = load_base_login_history()
        combined_login_history = base_data + login_history
        
        if not combined_login_history:
            # 데모 데이터 반환
            return {
                "totalUsers": 0,
                "todayUsers": 0,
                "thisWeekUsers": 0,
                "avgDailyUsers": 0,
                "totalFeedbacks": 0,
                "dailyData": [],
                "monthlyData": [],
                "affiliationData": {}
            }
        
        # 현재 시간 (한국 시간)
        now = datetime.now(pytz.timezone('Asia/Seoul'))
        today = now.date()
        
        # 기간 설정
        if period == "month":
            days_back = 30
            period_name = "최근 30일"
        elif period == "year":
            days_back = 365
            period_name = "최근 12개월"
        else:  # week
            days_back = 7
            period_name = "최근 7일"
            
        period_ago = today - timedelta(days=days_back)
            # 베이스데이터가 아닌 실제 로그인 기록만 필터링
        real_login_history = [
            record for record in combined_login_history 
            if record["name"] != "베이스데이터" and record["affiliation"] != "베이스데이터"
        ]
        
        # 기간별 로그인 기록 필터링
        period_login_history = [
            record for record in real_login_history
            if datetime.fromisoformat(record["timestamp"]).date() >= period_ago
        ]
        
        # 총 사용자 수 (기간별 고유 사용자)
        if period == "year":
            # 연간: 해당 연도의 고유 사용자
            year_login_history = [
                record for record in real_login_history
                if datetime.fromisoformat(record["timestamp"]).date().year == today.year
            ]
            unique_users = len(set((record["name"], record["affiliation"]) for record in year_login_history))
        else:
            # 주간/월간: 해당 기간의 고유 사용자
            unique_users = len(set((record["name"], record["affiliation"]) for record in period_login_history))
        
        # 총 로그인 수 (베이스데이터 포함)
        total_logins = len(login_history)
        
        # 오늘 로그인 수
        today_users = len([
            record for record in login_history
            if datetime.fromisoformat(record["timestamp"]).date() == today
        ])
        
        # 기간별 로그인 수
        if period == "year":
            # 연간: 해당 연도의 로그인 수 (베이스데이터 포함)
            period_users = len([
                record for record in combined_login_history
                if datetime.fromisoformat(record["timestamp"]).date().year == today.year
            ])
        else:
            # 주간/월간: 해당 기간의 로그인 수 (베이스데이터 포함)
            period_users = len([
                record for record in combined_login_history
                if datetime.fromisoformat(record["timestamp"]).date() >= period_ago
            ])
        
        # 일평균 사용자 수 (기간별)
        if period_users > 0 and days_back > 0:
            # 실제 데이터가 있는 날짜 수 계산
            actual_days = len(set([
                datetime.fromisoformat(record["timestamp"]).date()
                for record in login_history
                if datetime.fromisoformat(record["timestamp"]).date() >= period_ago
            ]))
            if actual_days > 0:
                avg_daily_users = round(period_users / actual_days)
            else:
                avg_daily_users = 0
        else:
            avg_daily_users = 0
        
        # 일별 데이터 (기간별)
        daily_counts = defaultdict(int)
        for record in login_history:
            record_date = datetime.fromisoformat(record["timestamp"]).date()
            if record_date >= period_ago:
                daily_counts[record_date.isoformat()] += 1
        
        daily_data = []
        for i in range(days_back):
            date = (today - timedelta(days=days_back-1-i)).isoformat()
            daily_data.append({
                "date": date,
                "count": daily_counts[date]
            })
        
        # 소속별 분포 (베이스데이터 제외)
        affiliations = [
            record["affiliation"] for record in real_login_history
            if datetime.fromisoformat(record["timestamp"]).date() >= period_ago
        ] if period != "year" else [
            record["affiliation"] for record in real_login_history
            if datetime.fromisoformat(record["timestamp"]).date().year == today.year
        ]
        affiliation_counts = Counter(affiliations)
        affiliation_data = dict(affiliation_counts)
        
        # 시간대별 이용 현황 제거됨
        
        # 피드백 통계
        total_feedbacks = len(feedback_history)
        
        # 호출 통계
        total_calls = len(call_history)
        
        # 다운로드 통계
        total_downloads = len(download_history)
        
        # 호출 차트 데이터 (기간별)
        call_daily_counts = defaultdict(int)
        for record in call_history:
            record_date = datetime.fromisoformat(record["timestamp"]).date()
            if record_date >= period_ago:
                call_daily_counts[record_date.isoformat()] += 1
        
        call_data = []
        for i in range(days_back):
            date = (today - timedelta(days=days_back-1-i)).isoformat()
            call_data.append({
                "date": date,
                "count": call_daily_counts[date]
            })
        
        # 다운로드 차트 데이터 (기간별)
        download_daily_counts = defaultdict(int)
        for record in download_history:
            record_date = datetime.fromisoformat(record["timestamp"]).date()
            if record_date >= period_ago:
                download_daily_counts[record_date.isoformat()] += 1
        
        download_data = []
        for i in range(days_back):
            date = (today - timedelta(days=days_back-1-i)).isoformat()
            download_data.append({
                "date": date,
                "count": download_daily_counts[date]
            })
        
        # 월별 데이터 (년도 탭용) - 현재 년도 1월~12월
        current_year = today.year
        monthly_counts = defaultdict(int)
        call_monthly_counts = defaultdict(int)
        download_monthly_counts = defaultdict(int)
        
        # 로그인 월별 데이터 (베이스데이터 포함 - 막대그래프용)
        for record in combined_login_history:
            record_date = datetime.fromisoformat(record["timestamp"]).date()
            if record_date.year == current_year:
                year_month = record_date.strftime("%Y-%m")
                monthly_counts[year_month] += 1
        
        # 호출 월별 데이터
        for record in call_history:
            record_date = datetime.fromisoformat(record["timestamp"]).date()
            if record_date.year == current_year:
                year_month = record_date.strftime("%Y-%m")
                call_monthly_counts[year_month] += 1
        
        # 다운로드 월별 데이터
        for record in download_history:
            record_date = datetime.fromisoformat(record["timestamp"]).date()
            if record_date.year == current_year:
                year_month = record_date.strftime("%Y-%m")
                download_monthly_counts[year_month] += 1
        
        monthly_data = []
        call_monthly_data = []
        download_monthly_data = []
        
        for month in range(1, 13):  # 1월부터 12월까지
            year_month = f"{current_year}-{month:02d}"
            monthly_data.append({
                "month": year_month,
                "count": monthly_counts[year_month]
            })
            call_monthly_data.append({
                "month": year_month,
                "count": call_monthly_counts[year_month]
            })
            download_monthly_data.append({
                "month": year_month,
                "count": download_monthly_counts[year_month]
            })
        
        return {
            "totalUsers": unique_users,
            "totalLogins": total_logins,
            "todayUsers": today_users,
            "periodUsers": period_users,
            "avgDailyUsers": avg_daily_users,
            "totalFeedbacks": total_feedbacks,
            "totalCalls": total_calls,
            "totalDownloads": total_downloads,
            "dailyData": daily_data,
            "monthlyData": monthly_data,
            "callData": call_data,
            "downloadData": download_data,
            "callMonthlyData": call_monthly_data,
            "downloadMonthlyData": download_monthly_data,
            "affiliationData": affiliation_data,
            "period": period,
            "periodName": period_name
        }
        
    except Exception as e:
        print(f"통계 데이터 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="통계 데이터를 생성하는 중 오류가 발생했습니다.")

@app.get("/api/feedbacks")
async def get_feedbacks(period: str = "week"):
    """피드백 상세 목록 API (기간별, 최신순)"""
    try:
        # 현재 시간 (한국 시간)
        now = datetime.now(pytz.timezone('Asia/Seoul'))
        today = now.date()
        
        # 기간 설정
        if period == "week":
            days_back = 7
        elif period == "month":
            days_back = 30
        else:  # all
            days_back = None
            
        # 기간별 필터링
        if days_back:
            period_ago = today - timedelta(days=days_back)
            filtered_feedbacks = [
                feedback for feedback in feedback_history
                if datetime.fromisoformat(feedback["timestamp"]).date() >= period_ago
            ]
        else:
            filtered_feedbacks = feedback_history
        
        # 최신순으로 정렬 (timestamp 기준 내림차순)
        sorted_feedbacks = sorted(
            filtered_feedbacks, 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        
        return {
            "feedbacks": sorted_feedbacks,
            "period": period,
            "count": len(sorted_feedbacks)
        }
    except Exception as e:
        print(f"피드백 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="피드백 목록을 조회하는 중 오류가 발생했습니다.")

@app.get("/api/calls")
async def get_calls():
    """호출 상세 목록 API (최신순)"""
    try:
        # 최신순으로 정렬 (timestamp 기준 내림차순)
        sorted_calls = sorted(
            call_history, 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        return {"calls": sorted_calls}
    except Exception as e:
        print(f"호출 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="호출 목록을 조회하는 중 오류가 발생했습니다.")

if __name__ == "__main__":
    print("🚀 PC방 제어시스템 백엔드 서버를 시작합니다...")
    # uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)  
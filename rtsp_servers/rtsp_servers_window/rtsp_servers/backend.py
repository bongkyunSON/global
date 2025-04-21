from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from subprocess import Popen
import threading
import time
import psutil
import os
import socket
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from typing import List, Dict, Optional, Tuple
import logging
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ 상수 및 설정 ============
# RTSP 서버 설정
RTSP_SERVERS = {
    "192.168.116.41": "서버 1",
    "192.168.118.42": "서버 2"
}

# 스트림 장소 목록 (코드명)
STREAM_LOCATIONS = [
    "1so", "2so", "1se", "2se", "3se",
    "2gan", "3gan", "4gan", "5gan", "6gan",
    "7gan", "8gan", "9gan", "10gan", "11gan", "dae"
]

# 스트림 장소 표시 이름 매핑
LOCATION_DISPLAY_NAMES = {
    "1so": "1소회의실", 
    "2so": "2소회의실", 
    "1se": "1세미나실", 
    "2se": "2세미나실", 
    "3se": "3세미나실",
    "2gan": "2간담회실", 
    "3gan": "3간담회실", 
    "4gan": "4간담회실", 
    "5gan": "5간담회실", 
    "6gan": "6간담회실",
    "7gan": "7간담회실", 
    "8gan": "8간담회실", 
    "9gan": "9간담회실", 
    "10gan": "10간담회실", 
    "11gan": "11간담회실", 
    "dae": "대회의실"
}

# 장치 리셋 IP 매핑
RESET_IPS = {
    "1so": "192.168.100.199", "2so": "192.168.101.199",
    "1se": "192.168.102.199", "2se": "192.168.103.199",
    "3se": "192.168.104.199", "2gan": "192.168.105.199",
    "3gan": "192.168.106.199", "4gan": "192.168.107.199",
    "5gan": "192.168.108.199", "6gan": "192.168.109.199",
    "7gan": "192.168.110.199", "8gan": "192.168.111.199",
    "9gan": "192.168.112.199", "10gan": "192.168.113.199",
    "11gan": "192.168.114.199", "dae": "192.168.120.199"
}

# 카메라 리스트: 회의장 이름, IP, 제어 방식
CAMERAS = [
    ("1so", "192.168.100.54", "visca"),
    ("2so", "192.168.101.54", "visca"),
    ("1se", "192.168.102.57", "http"),
    ("2se", "192.168.103.57", "visca"),
    ("3se", "192.168.104.54", "visca"),
    ("2gan", "192.168.105.57", "http"),
    ("3gan", "192.168.106.57", "http"),
    ("4gan", "192.168.107.57", "http"),
    ("5gan", "192.168.108.57", "visca"),
    ("6gan", "192.168.109.57", "http"),
    ("7gan", "192.168.110.57", "http"),
    ("8gan", "192.168.111.57", "visca"),
    ("9gan", "192.168.112.57", "http"),
    ("10gan", "192.168.113.57", "http"),
    ("11gan", "192.168.114.57", "http"),
]

# 카메라 인증 정보
CAMERA_AUTH = {
    "username": "admin",
    "password": "admin1234"
}

# 앱 생성
app = FastAPI(title="RTSP 서버 관리 API")

# 전역 변수로 프로세스 추적
rtsp_processes = []
rtmp_processes = []
should_restart = False

# ============ 데이터 모델 ============
class StreamRequest(BaseModel):
    location: str
    ip: str
    stream_key: Optional[str] = None

class CameraControl(BaseModel):
    camera_name: str
    power_on: bool

class DeviceReset(BaseModel):
    location: str

class ProcessInfo(BaseModel):
    pid: int
    location: str
    stream_key: Optional[str] = None

# ============ 헬퍼 함수 ============
def play_rtsp(location, ip):
    """RTSP 스트림을 ffplay로 실행하는 함수"""
    rtsp_url = f'rtsp://{ip}:554/{location}'
    
    # 기본 명령어
    cmd = ['ffplay', '-rtsp_transport', 'tcp', '-i', rtsp_url, 
            '-x', '640', '-y', '480', '-window_title', f'{location}']
    
    # ffplay 실행 경로 확인
    try:
        process = Popen(cmd)
        rtsp_processes.append(process)
        logger.info(f"RTSP 스트림 시작: {rtsp_url}")
        return process.pid
    except FileNotFoundError:
        # Mac Homebrew 설치 경로 시도
        try:
            cmd[0] = '/opt/homebrew/bin/ffplay'  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
            process = Popen(cmd)
            rtsp_processes.append(process)
            logger.info(f"Homebrew 경로에서 RTSP 스트림 시작: {rtsp_url}")
            return process.pid
        except Exception as e:
            # Intel Mac 경로 시도
            try:
                cmd[0] = '/usr/local/bin/ffplay'  # Homebrew에서 설치한 경우 (Intel Mac)
                process = Popen(cmd)
                rtsp_processes.append(process)
                logger.info(f"Homebrew Intel 경로에서 RTSP 스트림 시작: {rtsp_url}")
                return process.pid
            except Exception as e:
                logger.error(f"RTSP 스트림 실행 오류: {e}")
                return None

def _background_rtmp_task(location, ip, stream_key):
    """백그라운드에서 RTMP 스트리밍 처리"""
    global rtmp_processes, should_restart
    
    # 로그 디렉토리 설정
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    log_dir = os.path.join(desktop, "doogie_logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    rtsp_url = f'rtsp://{ip}:554/{location}'
    rtmp_url = f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
    
    # 기본 명령어
    cmd = [
        'ffmpeg', '-re', '-timeout', '10000000', '-rtsp_transport', 'tcp',
        '-i', rtsp_url, '-c:v', 'copy', '-c:a', 'copy', '-f', 'flv',
        rtmp_url, '-loglevel', 'debug', '-report'
    ]
    
    while should_restart:
        try:
            logger.info("FFmpeg 스트리밍 시작...")
            try:
                # Mac Homebrew 설치 경로 시도
                cmd[0] = '/opt/homebrew/bin/ffmpeg'  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
                try:
                    process_rtmp = Popen(cmd, cwd=log_dir)
                except FileNotFoundError:
                    cmd[0] = '/usr/local/bin/ffmpeg'  # Homebrew에서 설치한 경우 (Intel Mac)
                    process_rtmp = Popen(cmd, cwd=log_dir)
            except Exception as e:
                logger.error(f"오류 발생: {e}")
            finally:
                logger.info("FFmpeg 중단.")
                if should_restart:
                    logger.info("5초 후 다시 시도합니다.")
                    time.sleep(5)
        except Exception as e:
            logger.error(f"오류 발생: {e}")

def reset_device(ip):
    """장치 리셋 함수"""
    url = f"http://{ip}/api/v1/reboot.lua"
    username = "admin"
    password = "admin"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(username, password), timeout=5)
        if response.status_code == 200:
            logger.info(f"{ip}: Reset 성공")
            return True
        else:
            logger.error(f"{ip}: Reset 실패 - HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"{ip}: Exception occurred - {str(e)}")
        return False

def control_camera(ip, protocol, username, password, power_on):
    """카메라 제어 통합 함수"""
    if protocol == "http":
        return _toggle_http_camera(ip, username, password, power_on)
    elif protocol == "visca":
        command = "81 01 04 00 02 FF" if power_on else "81 01 04 00 03 FF"
        return _send_visca_command(ip, 52381, command)
    else:
        logger.error(f"알 수 없는 프로토콜: {protocol}")
        return False

def _toggle_http_camera(ip, username, password, power_on):
    """HTTP 방식으로 카메라 제어"""
    url = f"http://{ip}/command/main.cgi?System={'on' if power_on else 'standby'}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": f"http://{ip}/",
        "Origin": f"http://{ip}",
    }
    try:
        response = requests.get(url, auth=HTTPDigestAuth(username, password), headers=headers)
        if response.status_code == 200:
            logger.info(f"HTTP 카메라 {ip} 전원 {'켜짐' if power_on else '꺼짐'}")
            return True
        else:
            logger.error(f"요청 실패: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"연결 실패: {e}")
        return False

def _send_visca_command(ip, port, command):
    """VISCA 방식으로 카메라 제어"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(bytes.fromhex(command), (ip, port))
            logger.info(f"명령 전송 성공: {command} (IP: {ip}, PORT: {port})")
            return True
    except Exception as e:
        logger.error(f"VISCA 명령 전송 실패: {e}")
        return False

def get_process_info():
    """실행 중인 프로세스 정보 반환"""
    # 비정상 종료된 프로세스 제거
    global rtsp_processes, rtmp_processes
    
    # RTSP 프로세스 정보 수집
    rtsp_info = []
    for process in rtsp_processes[:]:
        if not psutil.pid_exists(process.pid):
            rtsp_processes.remove(process)
        else:
            rtsp_info.append({"pid": process.pid, "type": "rtsp"})
    
    # RTMP 프로세스 정보 수집
    rtmp_info = []
    for process in rtmp_processes[:]:
        if not psutil.pid_exists(process.pid):
            rtmp_processes.remove(process)
        else:
            rtmp_info.append({"pid": process.pid, "type": "rtmp"})
    
    return {"rtsp": rtsp_info, "rtmp": rtmp_info}

# ============ API 엔드포인트 ============
@app.get("/")
def read_root():
    return {"message": "RTSP 서버 관리 API가 작동 중입니다."}

@app.get("/servers")
def get_servers():
    return RTSP_SERVERS

@app.get("/locations")
def get_locations():
    # 프론트엔드에 전체 이름 리스트 반환
    return [LOCATION_DISPLAY_NAMES[location] for location in STREAM_LOCATIONS]

@app.get("/location_mapping")
def get_location_mapping():
    # 코드명과 표시 이름의 매핑 반환 (프론트엔드에서 필요한 경우)
    return LOCATION_DISPLAY_NAMES

@app.get("/cameras")
def get_cameras():
    return CAMERAS

@app.get("/reset_ips")
def get_reset_ips():
    return RESET_IPS

@app.post("/rtsp/play")
def start_rtsp_stream(stream_req: StreamRequest):
    # 표시 이름에서 코드명으로 변환
    location_code = None
    for code, display_name in LOCATION_DISPLAY_NAMES.items():
        if display_name == stream_req.location:
            location_code = code
            break
    
    if not location_code:
        # 직접 코드명으로 요청한 경우를 처리 (이전 버전 호환성)
        if stream_req.location in STREAM_LOCATIONS:
            location_code = stream_req.location
        else:
            raise HTTPException(status_code=400, detail="유효하지 않은 위치입니다.")
    
    if stream_req.ip not in RTSP_SERVERS:
        raise HTTPException(status_code=400, detail="유효하지 않은 서버 IP입니다.")
    
    pid = play_rtsp(location_code, stream_req.ip)
    if pid:
        return {"status": "success", "pid": pid}
    else:
        raise HTTPException(status_code=500, detail="RTSP 스트림 시작 실패")

@app.post("/rtmp/stream")
def start_rtmp_stream(stream_req: StreamRequest, background_tasks: BackgroundTasks):
    if not stream_req.stream_key:
        raise HTTPException(status_code=400, detail="스트림 키가 필요합니다.")
    
    # 표시 이름에서 코드명으로 변환
    location_code = None
    for code, display_name in LOCATION_DISPLAY_NAMES.items():
        if display_name == stream_req.location:
            location_code = code
            break
    
    if not location_code:
        # 직접 코드명으로 요청한 경우를 처리 (이전 버전 호환성)
        if stream_req.location in STREAM_LOCATIONS:
            location_code = stream_req.location
        else:
            raise HTTPException(status_code=400, detail="유효하지 않은 위치입니다.")
    
    if stream_req.ip not in RTSP_SERVERS:
        raise HTTPException(status_code=400, detail="유효하지 않은 서버 IP입니다.")
    
    global should_restart
    should_restart = True
    
    # 백그라운드 작업 시작
    background_tasks.add_task(_background_rtmp_task, location_code, stream_req.ip, stream_req.stream_key)
    
    return {"status": "success", "message": "RTMP 스트리밍 시작됨"}

@app.post("/rtmp/stop")
def stop_rtmp_stream():
    global should_restart, rtmp_processes
    should_restart = False
    
    for process in rtmp_processes:
        try:
            process.terminate()
        except Exception as e:
            logger.error(f"프로세스 종료 실패: {e}")
    
    rtmp_processes.clear()
    return {"status": "success", "message": "모든 RTMP 스트리밍 중지됨"}

@app.post("/rtsp/stop")
def stop_rtsp_stream():
    global rtsp_processes
    
    for process in rtsp_processes:
        try:
            process.terminate()
        except Exception as e:
            logger.error(f"프로세스 종료 실패: {e}")
    
    rtsp_processes.clear()
    return {"status": "success", "message": "모든 RTSP 스트리밍 중지됨"}

@app.post("/process/{pid}/stop")
def stop_process(pid: int):
    try:
        for process_list in [rtsp_processes, rtmp_processes]:
            for process in process_list[:]:
                if process.pid == pid:
                    process.terminate()
                    process_list.remove(process)
                    return {"status": "success", "message": f"프로세스 {pid} 종료됨"}
        
        raise HTTPException(status_code=404, detail=f"프로세스 ID {pid}를 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로세스 종료 오류: {str(e)}")

@app.get("/processes")
def get_processes():
    return get_process_info()

@app.post("/device/reset")
def reset_device_endpoint(device: DeviceReset):
    # 표시 이름에서 코드명으로 변환
    location_code = None
    for code, display_name in LOCATION_DISPLAY_NAMES.items():
        if display_name == device.location:
            location_code = code
            break
    
    if not location_code:
        # 직접 코드명으로 요청한 경우를 처리 (이전 버전 호환성)
        if device.location in RESET_IPS:
            location_code = device.location
        else:
            raise HTTPException(status_code=400, detail="유효하지 않은 위치입니다.")
    
    ip = RESET_IPS[location_code]
    result = reset_device(ip)
    
    if result:
        return {"status": "success", "message": f"{device.location} 리셋 성공"}
    else:
        raise HTTPException(status_code=500, detail=f"{device.location} 리셋 실패")

@app.post("/camera/control")
def control_camera_endpoint(camera: CameraControl):
    # 표시 이름에서 코드명으로 변환
    camera_code = None
    for code, display_name in LOCATION_DISPLAY_NAMES.items():
        if display_name == camera.camera_name:
            camera_code = code
            break
    
    if not camera_code:
        # 직접 코드명으로 요청한 경우를 처리 (이전 버전 호환성)
        camera_code = camera.camera_name
    
    for name, ip, protocol in CAMERAS:
        if name == camera_code:
            result = control_camera(ip, protocol, CAMERA_AUTH["username"], CAMERA_AUTH["password"], camera.power_on)
            if result:
                return {"status": "success", "message": f"{camera.camera_name} {'켜짐' if camera.power_on else '꺼짐'}"}
            else:
                raise HTTPException(status_code=500, detail=f"{camera.camera_name} 제어 실패")
    
    raise HTTPException(status_code=404, detail=f"카메라 {camera.camera_name}를 찾을 수 없습니다.")

@app.get("/camera/status")
def get_camera_status(name: str):
    """카메라 상태 확인 엔드포인트
    현재는 실제 상태 확인 기능이 없으므로 항상 false를 반환합니다.
    """
    # 표시 이름에서 코드명으로 변환
    camera_code = None
    for code, display_name in LOCATION_DISPLAY_NAMES.items():
        if display_name == name:
            camera_code = code
            break
    
    if not camera_code:
        # 직접 코드명으로 요청한 경우를 처리 (이전 버전 호환성)
        camera_code = name
    
    # 카메라 존재 여부 확인
    camera_exists = False
    for camera_name, _, _ in CAMERAS:
        if camera_name == camera_code:
            camera_exists = True
            break
    
    if not camera_exists:
        raise HTTPException(status_code=404, detail=f"카메라 {name}를 찾을 수 없습니다.")
    
    # 실제로는 카메라에 연결하여 상태를 확인해야 하지만,
    # 현재는 그 기능이 없으므로 항상 false를 반환합니다.
    return {"power_on": False}

# 서버 시작 함수
def start_server():
    # 로그 설정
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    
    logger.info("백엔드 서버 시작 중...")
    try:
        uvicorn.run("backend:app", host="0.0.0.0", port=8000, log_config=log_config)
    except Exception as e:
        logger.error(f"서버 시작 오류: {e}")
        # 오류가 발생하면 다른 포트로 시도
        try:
            logger.info("포트 8001로 재시도 중...")
            uvicorn.run("backend:app", host="0.0.0.0", port=8001, log_config=log_config)
        except Exception as e2:
            logger.error(f"백업 포트 시작 오류: {e2}")

if __name__ == "__main__":
    start_server() 
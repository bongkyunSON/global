from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    File,
    UploadFile,
    Form,
    APIRouter,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from subprocess import Popen
import threading
import time
import psutil
import os
import sys
import socket
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from typing import List, Dict, Optional, Tuple
import logging
import uvicorn
from datetime import datetime, timedelta
import shutil
import json
import glob
from image_size_ocr import (
    process_image_for_web,
    resize_image_only_for_web,
    ocr_only_for_web,
    poster_analysis_for_web,
    extract_poster_info_with_ocr,
)
import asyncio
import subprocess

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ 데이터 모델 ============
class StreamRequest(BaseModel):
    location: str
    ip: str
    stream_key: Optional[str] = None
    bitrate: Optional[int] = 3000  # 기본 비트레이트는 3000Kbps


class CameraControl(BaseModel):
    camera_name: str
    power_on: bool


class DeviceReset(BaseModel):
    location: str


class ProcessInfo(BaseModel):
    pid: int
    location: str
    stream_key: Optional[str] = None


class ImageSizeOCRRequest(BaseModel):
    width: Optional[int] = 400

# ============ 상수 및 설정 ============
# RTSP 서버 설정
RTSP_SERVERS = {"192.168.116.41": "서버 1", "192.168.118.42": "서버 2"}

# 스트림 장소 목록 (코드명)
STREAM_LOCATIONS = [
    "1so",
    "2so",
    "1se",
    "2se",
    "3se",
    "2gan",
    "3gan",
    "4gan",
    "5gan",
    "6gan",
    "7gan",
    "8gan",
    "9gan",
    "10gan",
    "11gan",
    "dae",
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
    "dae": "대회의실",
}

# 장치 리셋 IP 매핑
RESET_IPS = {
    "1so": "192.168.100.199",
    "2so": "192.168.101.199",
    "1se": "192.168.102.199",
    "2se": "192.168.103.199",
    "3se": "192.168.104.199",
    "2gan": "192.168.105.199",
    "3gan": "192.168.106.199",
    "4gan": "192.168.107.199",
    "5gan": "192.168.108.199",
    "6gan": "192.168.109.199",
    "7gan": "192.168.110.199",
    "8gan": "192.168.111.199",
    "9gan": "192.168.112.199",
    "10gan": "192.168.113.199",
    "11gan": "192.168.114.199",
    "dae": "192.168.120.199",
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
CAMERA_AUTH = {"username": "admin", "password": "Psrs0052"}

# 서버 설정
PORT = 8000
STATIC_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# 분석 히스토리 저장 디렉토리
ANALYSIS_HISTORY_DIR = os.path.join(os.path.dirname(__file__), "analysis_history")
OCR_DATA_DIR = os.path.join(ANALYSIS_HISTORY_DIR, "ocr_data")
AI_ANALYSIS_DATA_DIR = os.path.join(ANALYSIS_HISTORY_DIR, "ai_analysis_data")

# 디렉토리 생성
os.makedirs(OCR_DATA_DIR, exist_ok=True)
os.makedirs(AI_ANALYSIS_DATA_DIR, exist_ok=True)

# 추가 매핑 정의 (기존 변수들의 별칭)
LOCATION_MAPPING = LOCATION_DISPLAY_NAMES
CAMERA_CONTROLS = {name: {"ip": ip, "protocol": protocol} for name, ip, protocol in CAMERAS}
DEVICE_RESET_IPS = RESET_IPS

# 앱 생성
app = FastAPI(title="RTSP 서버 관리 API")

# API 라우터 생성
api_router = APIRouter()

# 정적 파일 서빙 설정
static_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(static_dir):
    # CSS, JS 등 에셋 파일들을 위한 정적 파일 서빙
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# 전역 변수 (프로세스 관리)
rtsp_processes = []
record_processes = []
rtmp_processes = []
is_recording = False  # 녹화 상태 플래그 추가



# ============ 헬퍼 함수 ============
def save_ocr_result(ocr_text, filename):
    """OCR 결과를 파일로 저장"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "ocr_text": ocr_text,
        }
        
        save_filename = f"ocr_{timestamp}_{filename}.json"
        save_path = os.path.join(OCR_DATA_DIR, save_filename)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"OCR 결과 저장 완료: {save_path}")
        return True
    except Exception as e:
        logger.error(f"OCR 결과 저장 실패: {str(e)}")
        return False

def save_ai_analysis_result(poster_info, filename):
    """AI 분석 결과를 파일로 저장"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "poster_info": poster_info,
        }
        
        save_filename = f"ai_analysis_{timestamp}_{filename}.json"
        save_path = os.path.join(AI_ANALYSIS_DATA_DIR, save_filename)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"AI 분석 결과 저장 완료: {save_path}")
        return True
    except Exception as e:
        logger.error(f"AI 분석 결과 저장 실패: {str(e)}")
        return False

def get_recent_analysis_history(analysis_type="all", limit=5):
    """최근 분석 히스토리 조회"""
    try:
        results = []
        
        if analysis_type in ["all", "ocr"]:
            # OCR 결과들 조회
            ocr_files = glob.glob(os.path.join(OCR_DATA_DIR, "*.json"))
            for file_path in sorted(ocr_files, key=os.path.getmtime, reverse=True):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data["type"] = "OCR"
                        results.append(data)
                except Exception as e:
                    logger.error(f"OCR 파일 읽기 실패 {file_path}: {str(e)}")
        
        if analysis_type in ["all", "ai"]:
            # AI 분석 결과들 조회
            ai_files = glob.glob(os.path.join(AI_ANALYSIS_DATA_DIR, "*.json"))
            for file_path in sorted(ai_files, key=os.path.getmtime, reverse=True):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data["type"] = "AI 분석"
                        results.append(data)
                except Exception as e:
                    logger.error(f"AI 분석 파일 읽기 실패 {file_path}: {str(e)}")
        
        # 시간순으로 정렬하고 limit 적용
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]
        
    except Exception as e:
        logger.error(f"분석 히스토리 조회 실패: {str(e)}")
        return []

def create_mpv_input_conf():
    """MPV 플레이어를 위한 단축키 설정 파일 생성"""
    mpv_config_dir = os.path.join(os.path.expanduser("~"), ".config", "mpv")
    if not os.path.exists(mpv_config_dir):
        os.makedirs(mpv_config_dir, exist_ok=True)

    input_conf_path = os.path.join(mpv_config_dir, "input.conf")

    # 단축키 설정 내용
    shortcuts = [
        "# RTSP 스트리밍용 MPV 단축키",
        "q quit",  # q: 종료
        "f cycle fullscreen",  # f: 전체화면 토글
        "SPACE cycle pause",  # 스페이스바: 일시정지/재생
        "RIGHT seek 10",  # 오른쪽 화살표: 10초 앞으로
        "LEFT seek -10",  # 왼쪽 화살표: 10초 뒤로
        "",
        "# 음향 조절 단축키 (다양한 옵션)",
        "UP add volume 10",  # 위쪽 화살표: 볼륨 크게 올리기
        "DOWN add volume -10",  # 아래쪽 화살표: 볼륨 크게 내리기
        "9 add volume -2",  # 9: 볼륨 조금 내리기
        "0 add volume 2",  # 0: 볼륨 조금 올리기
        "- add volume -10",  # -: 볼륨 크게 내리기
        "= add volume 10",  # =: 볼륨 크게 올리기
        "+ add volume 10",  # +: 볼륨 크게 올리기
        "_ add volume -10",  # _: 볼륨 크게 내리기
        "m cycle mute",  # m: 음소거 토글
        "M cycle mute",  # M: 음소거 토글 (대문자)
        "MUTE cycle mute",  # MUTE 키: 음소거 토글
        "CTRL+m set mute yes",  # Ctrl+m: 강제 음소거
        "CTRL+M set mute no",  # Ctrl+M: 음소거 해제
        "WHEEL_UP add volume 2",  # 마우스 휠 위: 볼륨 올리기
        "WHEEL_DOWN add volume -2",  # 마우스 휠 아래: 볼륨 내리기
        "",
        "# 추가 음향 조절",
        "a cycle audio",  # a: 오디오 트랙 변경
        "A cycle audio down",  # A: 오디오 트랙 변경 (역방향)
        "d cycle audio-delay",  # d: 오디오 지연 조정
        "",
        "# 기타 조절",
        "r cycle_values video-rotate 90 180 270 0",  # r: 화면 회전 (90도씩)
        "s screenshot",  # s: 스크린샷
        "1 add contrast -5",  # 1: 대비 감소
        "2 add contrast 5",  # 2: 대비 증가
        "3 add brightness -5",  # 3: 밝기 감소
        "4 add brightness 5",  # 4: 밝기 증가
        "5 add gamma -5",  # 5: 감마 감소
        "6 add gamma 5",  # 6: 감마 증가
        "7 add saturation -5",  # 7: 채도 감소
        "8 add saturation 5",  # 8: 채도 증가
        "",
        "# 재생 제어",
        "ESC set fullscreen no",  # ESC: 전체화면 해제
        "ENTER cycle fullscreen",  # 엔터: 전체화면 토글
        "p cycle pause",  # p: 일시정지/재생
        "P cycle pause",  # P: 일시정지/재생 (대문자)
        "",
        "# 고급 설정",
        "h cycle-values hwdec auto no",  # h: 하드웨어 디코딩 토글
        "i show-text '${filename}'",  # i: 파일 정보 표시
        "I show-text '볼륨: ${volume}% | 음소거: ${mute}'",  # I: 음량 정보 표시
        "o osd",  # o: OSD 정보 표시
        "O no-osd cycle osd-level",  # O: OSD 레벨 변경
        "v cycle sub-visibility",  # v: 자막 표시/숨김
        "c cycle audio",  # c: 오디오 트랙 변경
        "",
        "# 볼륨 프리셋",
        "CTRL+1 set volume 10",  # Ctrl+1: 볼륨 10%
        "CTRL+2 set volume 20",  # Ctrl+2: 볼륨 20%
        "CTRL+3 set volume 30",  # Ctrl+3: 볼륨 30%
        "CTRL+4 set volume 40",  # Ctrl+4: 볼륨 40%
        "CTRL+5 set volume 50",  # Ctrl+5: 볼륨 50%
        "CTRL+6 set volume 60",  # Ctrl+6: 볼륨 60%
        "CTRL+7 set volume 70",  # Ctrl+7: 볼륨 70%
        "CTRL+8 set volume 80",  # Ctrl+8: 볼륨 80%
        "CTRL+9 set volume 90",  # Ctrl+9: 볼륨 90%
        "CTRL+0 set volume 100",  # Ctrl+0: 볼륨 100%
    ]

    try:
        with open(input_conf_path, "w", encoding="utf-8") as f:
            f.write("\n".join(shortcuts))
        logger.info(f"MPV 단축키 설정 파일 생성: {input_conf_path}")
        return True
    except Exception as e:
        if os.path.exists(input_conf_path):
            logger.info(f"MPV 단축키 설정 파일 업데이트: {input_conf_path}")
            return True
        logger.error(f"MPV 단축키 설정 파일 생성 실패: {e}")
        return False


def log_mpv_keyboard_shortcuts():
    """MPV 키보드 단축키 정보를 로그에 기록"""
    logger.info("=== MPV 키보드 단축키 가이드 ===")
    logger.info("🎮 기본 조작: q(종료) | f(전체화면) | SPACE(재생/일시정지)")
    logger.info("⏯️  탐색: ←/→(10초 뒤로/앞으로) | p(일시정지/재생)")
    logger.info("🔊 음량 조절: ↑/↓(볼륨 크게) | +/-(볼륨 크게) | 9/0(볼륨 조금)")
    logger.info("🔇 음소거: m(음소거) | Ctrl+m(강제음소거) | 마우스휠로도 볼륨 조절 가능")
    logger.info("🌈 화질: 1/2(대비) | 3/4(밝기) | 5/6(감마) | 7/8(채도)")
    logger.info("🎵 오디오: a(트랙변경) | I(음량정보) | d(지연조정)")
    logger.info("⚡ 볼륨 프리셋: Ctrl+1~0 (10%~100%)")
    logger.info("📸 기타: s(스크린샷) | r(화면회전) | ESC(전체화면해제)")
    logger.info("=====================================")


def play_rtsp(location, ip, bitrate=3000):
    """🔄 향상된 RTSP 스트림 재생 함수"""
    rtsp_url = f"rtsp://{ip}:554/{location}"

    logger.info(f"🎬 RTSP 스트림 재생 시도: {rtsp_url}")

    # 비트레이트 값 검증
    if bitrate < 1000:
        bitrate = 1000
        logger.warning(f"비트레이트가 너무 낮아 1000Kbps로 조정했습니다.")
    elif bitrate > 10000:
        bitrate = 10000
        logger.warning(f"비트레이트가 너무 높아 10000Kbps로 조정했습니다.")

    logger.info(f"재생 비트레이트: {bitrate}Kbps")

    # RTSP 서버 연결 가능성 체크 (더 짧은 타임아웃)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, 554))
        sock.close()
        if result != 0:
            logger.warning(f"[{location}] RTSP 서버 ({ip}:554) 연결 실패, 그래도 재생 시도합니다.")
    except Exception as e:
        logger.warning(f"[{location}] RTSP 서버 연결 체크 오류: {e}")

    try:
        # MPV 우선 시도 (향상된 설정)
        logger.info(f"🎯 MPV 플레이어로 RTSP 스트림 시작: {location}")
        create_mpv_input_conf()
        log_mpv_keyboard_shortcuts()

        # 🔄 향상된 MPV 명령어 (안정성 옵션 추가)
        cmd = [
            "/opt/homebrew/bin/mpv",
            "--rtsp-transport=tcp",
            rtsp_url,
            "--title=RTSP: " + location + " - 서버: " + ip,
            "--volume=50",
            "--mute=no",  # 음소거 상태 명시적 설정
            "--force-window=yes",
            "--keep-open=yes",
            "--geometry=800x600+100+100",
            "--osd-level=2",
            "--player-operation-mode=pseudo-gui",
            "--terminal=no",
            "--input-default-bindings=yes",  # 기본 단축키 활성화
            "--input-vo-keyboard=yes",  # 키보드 입력 활성화
            # 네트워크 안정성 옵션들
            "--network-timeout=30",  # 네트워크 타임아웃 30초
            "--cache=yes",
            "--cache-secs=10",
            "--demuxer-max-bytes=25M",
            "--video-sync=audio",
            # 🔄 RTSP 스트리밍 최적화 (필수 옵션만)
            "--stream-lavf-o=rtsp_flags=prefer_tcp",  # TCP 선호
            "--stream-lavf-o=stimeout=5000000",  # 스트림 타임아웃 5초
        ]

        logger.info(f"🔄 향상된 MPV 실행 명령: {' '.join(cmd[:8])}... (총 {len(cmd)}개 옵션)")
        process = Popen(cmd)
        rtsp_processes.append(process)
        
        logger.info(f"✅ MPV로 향상된 RTSP 스트림 시작: {rtsp_url} (PID: {process.pid})")
        return process.pid
        
    except FileNotFoundError:
        # 다양한 MPV 경로 시도
        mpv_paths = [
            "/opt/homebrew/bin/mpv",  # Apple Silicon Mac
            "/usr/local/bin/mpv",     # Intel Mac
            "/usr/bin/mpv",           # Linux
            "mpv"                     # PATH에서 찾기
        ]
        
        for mpv_path in mpv_paths:
            try:
                cmd[0] = mpv_path
                process = Popen(cmd)
                rtsp_processes.append(process)
                logger.info(f"✅ MPV ({mpv_path})로 향상된 RTSP 스트림 시작: {rtsp_url} (PID: {process.pid})")
                log_mpv_keyboard_shortcuts()
                return process.pid
            except Exception:
                continue
        
        logger.warning(f"MPV를 찾을 수 없어 ffplay로 대체 시도: {location}")
        
        # ffplay 대체 시도 (향상된 설정)
        try:
            cmd = [
                "ffplay",
                "-rtsp_transport", "tcp",
                "-i", rtsp_url,
                "-x", "640", "-y", "480",
                "-window_title", f"{location}",
                "-volume", "50",
                
                # 🔄 ffplay 안정성 및 성능 옵션들
                "-fflags", "nobuffer+genpts+flush_packets",  # 버퍼링 최소화
                "-flags", "low_delay",  # 지연 최소화
                "-framedrop",  # 프레임 드롭 허용 (끊김 방지)
                "-strict", "experimental",  # 실험적 기능 허용
                "-vf", "fps=30",  # FPS 제한
                "-probesize", "32",  # 프로브 크기 최소화 (빠른 시작)
                "-analyzeduration", "0",  # 분석 시간 최소화
                "-sync", "audio",  # 오디오 동기화
                "-autoexit",  # 스트림 종료 시 자동 종료
            ]

            # ffplay 경로들 시도
            ffplay_paths = [
                "/opt/homebrew/bin/ffplay",  # Apple Silicon Mac
                "/usr/local/bin/ffplay",     # Intel Mac
                "/usr/bin/ffplay",           # Linux
                "ffplay"                     # PATH에서 찾기
            ]
            
            for ffplay_path in ffplay_paths:
                try:
                    cmd[0] = ffplay_path
                    process = subprocess.Popen(cmd)
                    rtsp_processes.append(process)
                    logger.info(f"✅ ffplay ({ffplay_path})로 향상된 RTSP 스트림 시작: {rtsp_url} (PID: {process.pid})")
                    return process.pid
                except Exception:
                    continue
            
            logger.error(f"❌ ffplay도 찾을 수 없습니다: {location}")
            return None
            
        except Exception as e:
            logger.error(f"❌ RTSP 스트림 실행 오류: {e}")
            return None
    
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류 발생: {e}")
        return None


def record_rtsp(location, ip, bitrate=3000):
    """RTSP 스트림을 녹화하는 함수 - FFmpeg 사용"""
    global record_processes, is_recording

    if is_recording:
        logger.info("이미 녹화 중입니다. 먼저 녹화를 중지하세요.")
        return None

    # 비트레이트 값 검증
    if bitrate < 1000:
        bitrate = 1000
        logger.warning(f"비트레이트가 너무 낮아 1000Kbps로 조정했습니다.")
    elif bitrate > 10000:
        bitrate = 10000
        logger.warning(f"비트레이트가 너무 높아 10000Kbps로 조정했습니다.")

    logger.info(f"녹화 비트레이트: {bitrate}Kbps")

    # 녹화 파일 경로 설정 (크로스 플랫폼)
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    recordings_dir = os.path.join(desktop, "rtsp_recordings")
    if not os.path.exists(recordings_dir):
        os.makedirs(recordings_dir)

    # 로그 디렉토리 설정
    log_dir = os.path.join(desktop, "rtsp_recordings", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 현재 시간으로 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # MP4 파일 경로 설정
    mp4_output_file = os.path.join(recordings_dir, f"{location}_{timestamp}.mp4")
    log_file = os.path.join(log_dir, f"{location}_{timestamp}_log.txt")

    rtsp_url = f"rtsp://{ip}:554/{location}"

    # 직접 트랜스코딩 방식으로 MP4 저장 (호환성과 안정성 향상)
    cmd = [
        "ffmpeg",
        "-y",  # 기존 파일 덮어쓰기
        "-rtsp_transport",
        "tcp",  # TCP 사용 (더 안정적)
        "-timeout",
        "30000000",  # 30초 타임아웃 (30,000,000 마이크로초)
        "-i",
        rtsp_url,  # 입력 RTSP 스트림
        "-c:v",
        "libx264",  # 비디오 코덱: H.264
        "-preset",
        "veryfast",  # 인코딩 속도 (빠른 인코딩)
        "-tune",
        "zerolatency",  # 지연 최소화 튜닝
        "-profile:v",
        "main",  # 프로파일 (호환성 개선)
        "-level",
        "4.0",  # 레벨 (호환성 개선)
        "-pix_fmt",
        "yuv420p",  # 픽셀 포맷 (호환성 개선)
        "-r",
        "30",  # 프레임 레이트 30fps로 고정
        "-g",
        "60",  # GOP 크기 (키프레임 간격)
        "-keyint_min",
        "60",  # 최소 키프레임 간격
        "-sc_threshold",
        "0",  # 장면 변화 탐지 임계값 (0: 비활성화)
        "-b:v",
        f"{bitrate}k",  # 비디오 비트레이트
        "-maxrate",
        f"{bitrate*1.5}k",  # 최대 비트레이트
        "-bufsize",
        f"{bitrate*3}k",  # 버퍼 크기
        "-c:a",
        "aac",  # 오디오 코덱: AAC
        "-b:a",
        "192k",  # 오디오 비트레이트
        "-ar",
        "48000",  # 오디오 샘플 레이트
        "-af",
        "aresample=async=1000",  # 오디오 타이밍 조정
        "-threads",
        "4",  # 사용할 스레드 수
        "-movflags",
        "+faststart",  # 웹 스트리밍 최적화
        "-f",
        "mp4",  # 출력 포맷 명시
        mp4_output_file,  # 출력 파일
    ]

    logger.info(f"실행 명령: {' '.join(cmd)}")

    # ffmpeg 실행 경로 확인 (크로스 플랫폼)
    try:
        # 로그 파일로 출력 리디렉션
        with open(log_file, "w") as log:
            try:
                process = Popen(cmd, stdout=log, stderr=log)
                record_processes.append(process)
                is_recording = True
                logger.info(f"RTSP 스트림 녹화 시작 (MP4 트랜스코딩): {rtsp_url}")
                logger.info(f"녹화 파일: {mp4_output_file}")
                logger.info(f"로그 파일: {log_file}")

                # 영상 확인용 ffplay 실행
                play_ffplay_monitor(rtsp_url, location)

                return process.pid

            except FileNotFoundError:
                # Homebrew 경로 시도 (Apple Silicon Mac)
                cmd[0] = "/opt/homebrew/bin/ffmpeg"
                try:
                    process = Popen(cmd, stdout=log, stderr=log)
                    record_processes.append(process)
                    is_recording = True
                    logger.info(f"MKV 형식으로 RTSP 스트림 녹화 시작: {rtsp_url}")
                    logger.info(f"녹화 파일: {mp4_output_file}")
                    logger.info(f"로그 파일: {log_file}")

                    # 영상 확인용 ffplay 실행
                    play_ffplay_monitor(rtsp_url, location)

                    return process.pid

                except FileNotFoundError:
                    # Intel Mac 시도
                    try:
                        # MacOS (Intel) 시도
                        cmd[0] = "/usr/local/bin/ffmpeg"
                        process = Popen(cmd, stdout=log, stderr=log)
                        record_processes.append(process)
                        is_recording = True
                        logger.info(f"Mac에서 RTSP 스트림 녹화 시작 (MP4): {rtsp_url}")
                        logger.info(f"녹화 파일: {mp4_output_file}")
                        logger.info(f"로그 파일: {log_file}")

                        # 영상 확인용 ffplay 실행
                        play_ffplay_monitor(rtsp_url, location)

                        return process.pid
                    except FileNotFoundError:
                        # MKV 파일로 시도 (낮은 호환성이지만 더 안정적)
                        mkv_output_file = os.path.join(
                            recordings_dir, f"{location}_{timestamp}.mkv"
                        )
                        cmd = [
                            "/usr/local/bin/ffmpeg",
                            "-y",
                            "-rtsp_transport",
                            "tcp",
                            "-timeout",
                            "30000000",
                            rtsp_url,
                            "-c",
                            "copy",  # 재인코딩 없이 복사 (더 빠름)
                            "-f",
                            "matroska",
                            mkv_output_file,
                        ]
                        try:
                            process = Popen(cmd, stdout=log, stderr=log)
                            record_processes.append(process)
                            is_recording = True
                            logger.info(
                                f"Mac에서 MKV 형식으로 RTSP 스트림 녹화 시작: {rtsp_url}"
                            )
                            logger.info(f"녹화 파일: {mkv_output_file}")
                            logger.info(f"로그 파일: {log_file}")

                            # 영상 확인용 ffplay 실행
                            play_ffplay_monitor(rtsp_url, location)

                            return process.pid
                        except FileNotFoundError:
                            # Intel Mac 전용 시도
                            try:
                                cmd[0] = "/usr/local/bin/ffmpeg"
                                process = Popen(cmd, stdout=log, stderr=log)
                                record_processes.append(process)
                                is_recording = True
                                logger.info(
                                    f"Intel Mac에서 RTSP 스트림 녹화 시작 (MP4): {rtsp_url}"
                                )
                                logger.info(f"녹화 파일: {mp4_output_file}")
                                logger.info(f"로그 파일: {log_file}")

                                # 영상 확인용 ffplay 실행
                                play_ffplay_monitor(rtsp_url, location)

                                return process.pid
                            except FileNotFoundError:
                                # Intel Mac MKV 시도
                                mkv_output_file = os.path.join(
                                    recordings_dir, f"{location}_{timestamp}.mkv"
                                )
                                cmd = [
                                    "/usr/local/bin/ffmpeg",
                                    "-y",
                                    "-rtsp_transport",
                                    "tcp",
                                    "-timeout",
                                    "30000000",
                                    rtsp_url,
                                    "-c",
                                    "copy",
                                    "-f",
                                    "matroska",
                                    mkv_output_file,
                                ]
                                try:
                                    process = Popen(cmd, stdout=log, stderr=log)
                                    record_processes.append(process)
                                    is_recording = True
                                    logger.info(
                                        f"Intel Mac에서 MKV 형식으로 RTSP 스트림 녹화 시작: {rtsp_url}"
                                    )
                                    logger.info(f"녹화 파일: {mkv_output_file}")
                                    logger.info(f"로그 파일: {log_file}")

                                    # 영상 확인용 ffplay 실행
                                    play_ffplay_monitor(rtsp_url, location)

                                    return process.pid
                                except Exception as e:
                                    logger.error(f"FFmpeg 실행 오류: {e}")
                                    return None

    except Exception as e:
        logger.error(f"RTSP 스트림 녹화 오류: {e}")
        return None


def play_ffplay_monitor(rtsp_url, location):
    """녹화 중인 영상을 모니터링 (mpv 또는 ffplay 사용)"""
    # MPV 단축키 설정 파일 생성
    create_mpv_input_conf()

    # mpv 명령어 설정 - 전체 경로 사용
    cmd = [
        "/opt/homebrew/bin/mpv",
        "--rtsp-transport=tcp",
        rtsp_url,
        "--geometry=640x480",
        "--force-window=yes",
        f"--title={location} (녹화 모니터링 중)",
        "--volume=50",
        "--no-terminal",  # 터미널 출력 비활성화
        "--osd-level=1",
    ]

    logger.info(f"모니터링 실행 명령: {' '.join(cmd)}")

    # mpv 실행 경로 확인 (크로스 플랫폼)
    try:
        process = Popen(cmd)
        rtsp_processes.append(process)  # 모니터링용 프로세스도 rtsp 목록에 추가
        logger.info(f"MPV로 녹화 모니터링 시작: {rtsp_url}")
        log_mpv_keyboard_shortcuts()
        return process.pid
    except FileNotFoundError:
        # Mac Homebrew 설치 경로 시도
        try:
            cmd[0] = (
                "/opt/homebrew/bin/mpv"  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
            )
            process = Popen(cmd)
            rtsp_processes.append(process)
            logger.info(f"Homebrew 경로에서 MPV로 녹화 모니터링 시작: {rtsp_url}")
            log_mpv_keyboard_shortcuts()
            return process.pid
        except Exception as e:
            try:
                cmd[0] = "/usr/local/bin/mpv"  # Intel Mac에서 Homebrew로 설치한 경우
                process = Popen(cmd)
                rtsp_processes.append(process)
                logger.info(
                    f"Intel Mac Homebrew 경로에서 MPV로 녹화 모니터링 시작: {rtsp_url}"
                )
                log_mpv_keyboard_shortcuts()
                return process.pid
            except Exception as e:
                logger.error(f"MPV 실행 오류, ffplay로 대체 시도: {e}")

                # mpv 실패 시 ffplay 사용 시도
                cmd = [
                    "ffplay",
                    "-rtsp_transport",
                    "tcp",
                    "-i",
                    rtsp_url,
                    "-x",
                    "640",
                    "-y",
                    "480",
                    "-window_title",
                    f"{location} (녹화 모니터링 중)",
                    "-volume",
                    "50",
                ]

                try:
                    process = Popen(cmd)
                    rtsp_processes.append(process)
                    logger.info(f"ffplay로 녹화 모니터링 시작: {rtsp_url}")
                    return process.pid
                except FileNotFoundError:
                    # Mac Homebrew 설치 경로 시도
                    try:
                        cmd[0] = (
                            "/opt/homebrew/bin/ffplay"  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
                        )
                        process = Popen(cmd)
                        rtsp_processes.append(process)
                        logger.info(
                            f"Homebrew 경로에서 ffplay로 녹화 모니터링 시작: {rtsp_url}"
                        )
                        return process.pid
                    except Exception as e:
                        try:
                            cmd[0] = (
                                "/usr/local/bin/ffplay"  # Intel Mac에서 Homebrew로 설치한 경우
                            )
                            process = Popen(cmd)
                            rtsp_processes.append(process)
                            logger.info(
                                f"Intel Mac Homebrew 경로에서 ffplay로 녹화 모니터링 시작: {rtsp_url}"
                            )
                            return process.pid
                        except Exception as e:
                            logger.error(f"녹화 모니터링 실행 오류: {e}")
                            return None


def stop_recording():
    """녹화 중지 함수"""
    global record_processes, is_recording

    if not is_recording:
        logger.info("녹화 중인 스트림이 없습니다.")
        return False

    for process in record_processes:
        try:
            process.terminate()
        except Exception as e:
            logger.error(f"녹화 프로세스 종료 실패: {e}")

    record_processes.clear()
    is_recording = False
    logger.info("녹화가 중지되었습니다.")
    return True


def _background_rtmp_task(location, ip, stream_key, bitrate=3000):
    """백그라운드에서 RTMP 스트리밍 처리"""
    global rtmp_processes, should_restart

    # 로그 디렉토리 설정
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    log_dir = os.path.join(desktop, "doogie_logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    rtsp_url = f"rtsp://{ip}:554/{location}"
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"

    # 비트레이트 값 검증 및 조정
    if bitrate < 1000:
        bitrate = 1000
        logger.warning(f"비트레이트가 너무 낮아 1000Kbps로 조정했습니다.")
    elif bitrate > 10000:
        bitrate = 10000
        logger.warning(f"비트레이트가 너무 높아 10000Kbps로 조정했습니다.")

    logger.info(f"스트리밍 비트레이트: {bitrate}Kbps")

    # 기본 명령어
    cmd = [
        "ffmpeg",
        "-re",
        "-timeout",
        "10000000",
        "-rtsp_transport",
        "tcp",
        "-i",
        rtsp_url,
        "-c:v",
        "libx264",
        "-b:v",
        f"{bitrate}k",  # 비트레이트 설정
        "-maxrate",
        f"{bitrate}k",
        "-bufsize",
        f"{bitrate*2}k",
        "-preset",
        "veryfast",  # 인코딩 속도/품질 설정
        "-tune",
        "zerolatency",
        "-c:a",
        "aac",
        "-b:a",
        "128k",  # 오디오 비트레이트
        "-ar",
        "44100",
        "-f",
        "flv",
        rtmp_url,
        "-loglevel",
        "debug",
        "-report",
    ]

    while should_restart:
        try:
            logger.info("FFmpeg 스트리밍 시작...")
            try:
                # Mac Homebrew 설치 경로 시도
                cmd[0] = (
                    "/opt/homebrew/bin/ffmpeg"  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
                )
                try:
                    process_rtmp = Popen(cmd, cwd=log_dir)
                except FileNotFoundError:
                    cmd[0] = (
                        "/usr/local/bin/ffmpeg"  # Homebrew에서 설치한 경우 (Intel Mac)
                    )
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
    password = "Psrs0052"
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
        response = requests.get(
            url, auth=HTTPDigestAuth(username, password), headers=headers
        )
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
    """모든 프로세스 정보 반환"""
    rtsp_info = []
    rtmp_info = []
    record_info = []  # 녹화 프로세스 정보 추가

    # RTSP 프로세스 정보
    for process in rtsp_processes:
        if process.poll() is None:  # 프로세스가 실행 중인지 확인
            rtsp_info.append({"pid": process.pid, "type": "rtsp"})

    # RTMP 프로세스 정보
    for process in rtmp_processes:
        if process.poll() is None:  # 프로세스가 실행 중인지 확인
            rtmp_info.append({"pid": process.pid, "type": "rtmp"})

    # 녹화 프로세스 정보
    for process in record_processes:
        if process.poll() is None:  # 프로세스가 실행 중인지 확인
            record_info.append({"pid": process.pid, "type": "record"})

    return {
        "rtsp": rtsp_info,
        "rtmp": rtmp_info,
        "record": record_info,  # 녹화 프로세스 정보 추가
    }


# ============ API 엔드포인트 ============
@app.get("/")
def read_root():
    """웹 앱 메인 페이지 서빙"""
    index_file = os.path.join(
        os.path.dirname(__file__), "frontend", "dist", "index.html"
    )
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "RTSP 서버 관리 API가 작동 중입니다."}


@api_router.get("/servers")
def get_servers():
    return RTSP_SERVERS


@api_router.get("/locations")
def get_locations():
    # 프론트엔드에 전체 이름 리스트 반환
    return [LOCATION_DISPLAY_NAMES[location] for location in STREAM_LOCATIONS]


@api_router.get("/location_mapping")
def get_location_mapping():
    # 코드명과 표시 이름의 매핑 반환 (프론트엔드에서 필요한 경우)
    return LOCATION_DISPLAY_NAMES


@api_router.get("/cameras")
def get_cameras():
    return CAMERAS


@api_router.get("/reset_ips")
def get_reset_ips():
    return RESET_IPS


@api_router.post("/rtsp/play")
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

    # 비트레이트 값 검증
    bitrate = stream_req.bitrate
    if bitrate < 1000:
        bitrate = 1000
        logger.warning(f"비트레이트가 너무 낮아 1000Kbps로 조정했습니다.")
    elif bitrate > 10000:
        bitrate = 10000
        logger.warning(f"비트레이트가 너무 높아 10000Kbps로 조정했습니다.")

    pid = play_rtsp(location_code, stream_req.ip, bitrate)
    if pid:
        return {
            "status": "success",
            "message": f"RTSP 스트리밍 시작됨 (비트레이트: {bitrate}Kbps)",
            "pid": pid,
        }
    else:
        raise HTTPException(status_code=500, detail="RTSP 스트림 시작 실패")


@api_router.post("/rtmp/stream")
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

    # 비트레이트 값 검증
    bitrate = stream_req.bitrate
    if bitrate < 1000:
        bitrate = 1000
        logger.warning(f"비트레이트가 너무 낮아 1000Kbps로 조정했습니다.")
    elif bitrate > 10000:
        bitrate = 10000
        logger.warning(f"비트레이트가 너무 높아 10000Kbps로 조정했습니다.")

    global should_restart
    should_restart = True

    # 백그라운드 작업 시작
    background_tasks.add_task(
        _background_rtmp_task,
        location_code,
        stream_req.ip,
        stream_req.stream_key,
        bitrate,
    )

    return {
        "status": "success",
        "message": f"RTMP 스트리밍 시작됨 (비트레이트: {bitrate}Kbps)",
    }


@api_router.post("/rtmp/stop")
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


@api_router.post("/rtsp/stop")
def stop_rtsp_stream():
    """🔄 모든 RTSP 스트림 중지"""
    global rtsp_processes

    if not rtsp_processes:
        logger.info("현재 실행 중인 RTSP 스트림이 없습니다.")
        return {"status": "info", "message": "실행 중인 RTSP 스트림이 없습니다."}

    # 모든 스트림 중지
    stopped_count = 0
    for process in rtsp_processes:
        try:
            if process.poll() is None:  # 프로세스가 아직 실행 중이면
                process.terminate()
                try:
                    process.wait(timeout=3)  # 3초 대기
                except subprocess.TimeoutExpired:
                    process.kill()  # 강제 종료
                stopped_count += 1
                logger.info(f"RTSP 스트림 프로세스 종료: PID {process.pid}")
        except Exception as e:
            logger.error(f"프로세스 종료 오류: {e}")

    # 리스트 초기화
    rtsp_processes.clear()

    logger.info(f"총 {stopped_count}개의 RTSP 스트림을 중지했습니다.")
    return {
        "status": "success",
        "message": f"총 {stopped_count}개의 RTSP 스트림을 중지했습니다.",
        "stopped_count": stopped_count,
    }


@api_router.post("/rtsp/record")
def start_rtsp_recording(stream_req: StreamRequest):
    """RTSP 스트림 녹화 시작"""
    location = stream_req.location
    ip = stream_req.ip

    # 위치 이름이 표시 이름인 경우 코드명으로 변환
    for code, display in LOCATION_DISPLAY_NAMES.items():
        if location == display:
            location = code
            break

    # 비트레이트 값 검증
    bitrate = stream_req.bitrate
    if bitrate < 1000:
        bitrate = 1000
        logger.warning(f"비트레이트가 너무 낮아 1000Kbps로 조정했습니다.")
    elif bitrate > 10000:
        bitrate = 10000
        logger.warning(f"비트레이트가 너무 높아 10000Kbps로 조정했습니다.")

    # RTSP 스트림 녹화 시작
    pid = record_rtsp(location, ip, bitrate)

    if pid:
        return {
            "status": "success",
            "message": f"RTSP 스트림 녹화 시작: {location} (비트레이트: {bitrate}Kbps)",
            "pid": pid,
        }
    else:
        raise HTTPException(status_code=500, detail="RTSP 스트림 녹화 시작 실패")


@api_router.post("/rtsp/record/stop")
def stop_rtsp_recording():
    """RTSP 스트림 녹화 중지"""
    global record_processes

    success = stop_recording()

    if success:
        return {"status": "success", "message": "RTSP 스트림 녹화가 중지되었습니다."}
    else:
        return {"status": "info", "message": "녹화 중인 스트림이 없습니다."}


@api_router.get("/rtsp/record/status")
def get_recording_status():
    """현재 녹화 상태 반환"""
    return {"is_recording": is_recording}


@api_router.post("/process/{pid}/stop")
def stop_process(pid: int):
    """특정 프로세스 강제 종료"""
    try:
        # psutil을 사용하여 프로세스 종료
        process = psutil.Process(pid)
        process_name = process.name()
        process.terminate()

        # 프로세스 리스트에서 제거
        global rtsp_processes, record_processes, rtmp_processes
        rtsp_processes = [p for p in rtsp_processes if p.pid != pid]
        record_processes = [p for p in record_processes if p.pid != pid]
        rtmp_processes = [p for p in rtmp_processes if p.pid != pid]

        logger.info(f"프로세스 종료 성공: {process_name} (PID: {pid})")
        return {
            "status": "success",
            "message": f"프로세스 {process_name} (PID: {pid})를 종료했습니다.",
        }

    except psutil.NoSuchProcess:
        logger.warning(f"프로세스를 찾을 수 없습니다: PID {pid}")
        return {"status": "error", "message": f"프로세스 PID {pid}를 찾을 수 없습니다."}

    except psutil.AccessDenied:
        logger.error(f"프로세스 종료 권한이 없습니다: PID {pid}")
        return {
            "status": "error",
            "message": f"프로세스 PID {pid} 종료 권한이 없습니다.",
        }

    except Exception as e:
        logger.error(f"프로세스 종료 오류: {e}")
        return {"status": "error", "message": f"프로세스 종료 오류: {str(e)}"}


@api_router.get("/processes")
def get_processes():
    """실행 중인 프로세스 목록 반환"""
    return get_process_info()


@api_router.post("/device/reset")
def reset_device_endpoint(device: DeviceReset):
    # 표시 이름에서 코드명으로 변환
    location = device.location
    for code, display in LOCATION_DISPLAY_NAMES.items():
        if display == location:
            location = code
            break

    # 해당 위치의 IP 가져오기
    if location not in RESET_IPS:
        raise HTTPException(
            status_code=404, detail=f"위치 '{location}'를 찾을 수 없습니다."
        )

    ip = RESET_IPS[location]

    try:
        success = reset_device(ip)
        if success:
            return {
                "status": "success",
                "message": f"{LOCATION_DISPLAY_NAMES.get(location, location)} 장치 리셋 성공",
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"{LOCATION_DISPLAY_NAMES.get(location, location)} 장치 리셋 실패",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장치 리셋 오류: {str(e)}")


@api_router.post("/camera/control")
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
            result = control_camera(
                ip,
                protocol,
                CAMERA_AUTH["username"],
                CAMERA_AUTH["password"],
                camera.power_on,
            )
            if result:
                return {
                    "status": "success",
                    "message": f"{camera.camera_name} {'켜짐' if camera.power_on else '꺼짐'}",
                }
            else:
                raise HTTPException(
                    status_code=500, detail=f"{camera.camera_name} 제어 실패"
                )

    raise HTTPException(
        status_code=404, detail=f"카메라 {camera.camera_name}를 찾을 수 없습니다."
    )


@api_router.get("/camera/status")
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
        raise HTTPException(
            status_code=404, detail=f"카메라 {name}를 찾을 수 없습니다."
        )

    # 실제로는 카메라에 연결하여 상태를 확인해야 하지만,
    # 현재는 그 기능이 없으므로 항상 false를 반환합니다.
    return {"power_on": False}


@api_router.post("/image/process")
async def process_image(
    file: UploadFile = File(...),
    width: Optional[int] = Form(400),
    api_key: Optional[str] = Form(None),
):
    """이미지를 업로드하여 크기 조정 및 OCR 처리"""
    # 파일 확장자 확인
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 파일 형식입니다. JPG 또는 PNG 파일만 가능합니다.",
        )

    # 임시 디렉토리 생성
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)

    # 파일 저장
    temp_file_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 이미지 처리 (API 키 전달)
        result = process_image_for_web(temp_file_path, width, api_key)

        # 처리 완료 후 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "이미지 처리 중 오류가 발생했습니다."),
            )

    except Exception as e:
        # 오류 발생 시 임시 파일 정리
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"이미지 처리 중 오류: {str(e)}")


@api_router.post("/image/resize")
async def resize_image_only(file: UploadFile = File(...), width: int = Form(400)):
    """이미지 크기 조정만 수행"""
    # 파일 확장자 확인
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 파일 형식입니다. JPG 또는 PNG 파일만 가능합니다.",
        )

    # 임시 디렉토리 생성
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)

    # 파일 저장
    temp_file_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 이미지 크기 조정만 수행
        result = resize_image_only_for_web(temp_file_path, width)

        # 처리 완료 후 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "이미지 크기 조정 중 오류가 발생했습니다."),
            )

    except Exception as e:
        # 오류 발생 시 임시 파일 정리
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(
            status_code=500, detail=f"이미지 크기 조정 중 오류: {str(e)}"
        )


@api_router.post("/image/ocr")
async def ocr_image_only(file: UploadFile = File(...), api_key: str = Form(...)):
    """OCR만 수행"""
    # 파일 확장자 확인
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 파일 형식입니다. JPG 또는 PNG 파일만 가능합니다.",
        )

    # 임시 디렉토리 생성
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)

    # 파일 저장
    temp_file_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # OCR만 수행
        result = ocr_only_for_web(temp_file_path, api_key)

        # 처리 완료 후 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        if result["success"]:
            # OCR 결과 저장
            if result.get("ocr_text"):
                save_ocr_result(result["ocr_text"], file.filename)
            return result
        else:
            # OCR 실패 시에도 결과 반환 (오류 메시지 포함)
            return result

    except Exception as e:
        # 오류 발생 시 임시 파일 정리
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"OCR 처리 중 오류: {str(e)}")


@api_router.post("/poster/analyze")
async def analyze_poster(file: UploadFile = File(...), api_key: str = Form(...)):
    """포스터 이미지를 분석하여 구조화된 정보를 추출"""
    # 파일 확장자 확인
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 파일 형식입니다. JPG 또는 PNG 파일만 가능합니다.",
        )

    # 임시 디렉토리 생성
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)

    # 파일 저장
    temp_file_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 포스터 분석 수행
        result = poster_analysis_for_web(temp_file_path, api_key)

        # 처리 완료 후 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        if result["success"]:
            # AI 분석 결과 저장
            if result.get("poster_info"):
                save_ai_analysis_result(result["poster_info"], file.filename)
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "포스터 분석 중 오류가 발생했습니다."),
            )

    except Exception as e:
        # 오류 발생 시 임시 파일 정리
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"포스터 분석 중 오류: {str(e)}")


@api_router.post("/poster/extract-with-ocr")
async def extract_poster_with_ocr(file: UploadFile = File(...), api_key: str = Form(...)):
    """포스터 이미지에서 OCR 텍스트와 구조화된 정보를 함께 추출"""
    # 파일 확장자 확인
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 파일 형식입니다. JPG 또는 PNG 파일만 가능합니다.",
        )

    # 임시 디렉토리 생성
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)

    # 파일 저장
    temp_file_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # OCR과 포스터 정보 추출 수행
        result = extract_poster_info_with_ocr(temp_file_path, api_key)

        # 처리 완료 후 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        if result["success"]:
            # OCR과 AI 분석 결과 모두 저장
            if result.get("ocr_text"):
                save_ocr_result(result["ocr_text"], file.filename)
            if result.get("poster_info"):
                save_ai_analysis_result(result["poster_info"], file.filename)
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "포스터 정보 추출 중 오류가 발생했습니다."),
            )

    except Exception as e:
        # 오류 발생 시 임시 파일 정리
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"포스터 정보 추출 중 오류: {str(e)}")


@api_router.get("/rtsp/status")
def get_rtsp_stream_status():
    """RTSP 스트림 상태 조회"""
    global rtsp_processes

    active_streams = []
    
    # 죽은 프로세스 정리
    rtsp_processes = [p for p in rtsp_processes if p.poll() is None]
    
    for process in rtsp_processes:
        if process.poll() is None:  # 프로세스가 살아있으면
            try:
                # psutil로 상세 정보 가져오기
                p = psutil.Process(process.pid)
                active_streams.append({
                    "pid": process.pid,
                    "status": "running",
                    "cpu_percent": p.cpu_percent(),
                    "memory_mb": round(p.memory_info().rss / 1024 / 1024, 2),
                    "create_time": datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # 프로세스가 없거나 접근 권한이 없으면 스킵
                continue

    return {
        "status": "success",
        "active_count": len(active_streams),
        "streams": active_streams
    }


@api_router.get("/rtsp/health")
def get_rtsp_health():
    """RTSP 시스템 상태 확인"""
    global rtsp_processes
    
    # 죽은 프로세스 정리
    rtsp_processes = [p for p in rtsp_processes if p.poll() is None]
    
    return {
        "status": "healthy",
        "total_processes": len(rtsp_processes),
        "timestamp": datetime.now().isoformat()
    }


@api_router.post("/rtsp/restart-system/status")
def get_restart_system_status():
    """재시작 시스템 상태 조회 (비활성화됨)"""
    return {
        "status": "disabled",
        "message": "자동 재시작 시스템이 비활성화되었습니다.",
        "managed_processes": 0,
        "active_restarts": 0
    }


@api_router.get("/analysis/history")
def get_analysis_history(analysis_type: str = "all", limit: int = 5):
    """분석 히스토리 조회"""
    try:
        history = get_recent_analysis_history(analysis_type, limit)
        return {"success": True, "data": history}
    except Exception as e:
        logger.error(f"분석 히스토리 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 히스토리 조회 중 오류: {str(e)}")


# API 라우터를 앱에 포함
app.include_router(api_router, prefix="/api")

# version.json 파일 서빙을 위한 엔드포인트 추가
@app.get("/version.json")
def get_version():
    """version.json 파일 내용 반환"""
    try:
        with open("version.json", "r") as f:
            import json
            version_data = json.load(f)
        return version_data
    except FileNotFoundError:
        return {"version": "1.0.0", "build": 1, "releaseDate": "2024-12-30", "description": "RTSP 스트리밍 관리 웹 애플리케이션"}
    except Exception as e:
        logger.error(f"version.json 읽기 오류: {e}")
        return {"version": "1.0.0", "build": 1, "releaseDate": "2024-12-30", "description": "RTSP 스트리밍 관리 웹 애플리케이션"}


# React 앱 라우팅을 위한 catch-all 라우트
@app.get("/{full_path:path}")
def serve_react_app(full_path: str):
    """React 앱의 라우팅을 처리하기 위한 catch-all 라우트"""
    # API 경로는 제외
    if (
        full_path.startswith("api/")
        or full_path.startswith("docs")
        or full_path.startswith("redoc")
    ):
        raise HTTPException(status_code=404, detail="Not found")

    index_file = os.path.join(
        os.path.dirname(__file__), "frontend", "dist", "index.html"
    )
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Frontend not found")


# 서버 시작 함수
def start_server():
    # 로그 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("rtsp_server.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # 서버 시작 로그
    logger.info("=" * 50)
    logger.info("🚀 RTSP 스트리밍 서버 시작")
    logger.info("=" * 50)

    # 앱 구성 정보 로그
    logger.info(f"📍 서버 주소: http://localhost:{PORT}")
    logger.info(f"📁 정적 파일 경로: {STATIC_DIR}")
    logger.info(f"🎯 지원 위치: {list(LOCATION_MAPPING.keys())}")
    logger.info(f"🖥️  지원 서버: {list(RTSP_SERVERS.keys())}")
    logger.info(f"📷 카메라 제어: {list(CAMERA_CONTROLS.keys())}")
    logger.info(f"🔄 장치 리셋: {list(DEVICE_RESET_IPS.keys())}")

    # 환경 정보
    logger.info(f"🐍 Python 버전: {sys.version}")
    logger.info(f"💻 운영체제: {os.name}")

    # 의존성 체크
    try:
        import psutil
        logger.info(f"✅ psutil 버전: {psutil.__version__}")
    except ImportError:
        logger.warning("⚠️ psutil을 찾을 수 없습니다. 프로세스 관리 기능이 제한될 수 있습니다.")

    # Uvicorn 서버 시작
    logger.info("🌟 Uvicorn 서버 시작 중...")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")


if __name__ == "__main__":
    start_server()

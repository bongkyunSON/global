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
from datetime import datetime

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
record_processes = []  # 녹화 프로세스 추가
should_restart = False
is_recording = False  # 녹화 상태 플래그 추가

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

# ============ 헬퍼 함수 ============
def create_mpv_input_conf():
    """MPV 플레이어를 위한 단축키 설정 파일 생성"""
    mpv_config_dir = os.path.join(os.path.expanduser("~"), ".config", "mpv")
    if not os.path.exists(mpv_config_dir):
        os.makedirs(mpv_config_dir, exist_ok=True)
    
    input_conf_path = os.path.join(mpv_config_dir, "input.conf")
    
    # 음량을 미세하게 조절하는 키 설정
    config_content = """
# 음량 조절 단축키
9 add volume -2         # 9키: 음량 감소 (기본값 -5보다 작게)
0 add volume 2          # 0키: 음량 증가 (기본값 5보다 작게)
- add volume -10        # -키: 음량 크게 감소
= add volume 10         # =키: 음량 크게 증가
m cycle mute           # m키: 음소거 토글
/ cycle mute           # /키: 음소거 토글 (추가 키)

# 일시정지 및 재생 관련
SPACE cycle pause      # 스페이스바: 일시정지/재생
p cycle pause          # p키: 일시정지/재생

# 탐색 관련
RIGHT seek 5           # 오른쪽 화살표: 5초 앞으로
LEFT seek -5           # 왼쪽 화살표: 5초 뒤로
UP seek 30             # 위쪽 화살표: 30초 앞으로
DOWN seek -30          # 아래쪽 화살표: 30초 뒤로
PGUP seek 60           # Page Up: 1분 앞으로
PGDWN seek -60         # Page Down: 1분 뒤로

# 전체화면 관련
f cycle fullscreen     # f키: 전체화면 전환
ESC set fullscreen no  # ESC: 전체화면 종료
"""
    
    # 파일이 없거나 내용이 다른 경우에만 쓰기
    if not os.path.exists(input_conf_path):
        with open(input_conf_path, 'w') as f:
            f.write(config_content)
        logger.info(f"MPV 단축키 설정 파일 생성: {input_conf_path}")
    else:
        with open(input_conf_path, 'r') as f:
            existing_content = f.read()
        if existing_content.strip() != config_content.strip():
            with open(input_conf_path, 'w') as f:
                f.write(config_content)
            logger.info(f"MPV 단축키 설정 파일 업데이트: {input_conf_path}")
    
    return input_conf_path

def log_mpv_keyboard_shortcuts():
    """MPV 키보드 단축키 정보를 로그에 기록"""
    logger.info("=== MPV 키보드 단축키 가이드 ===")
    logger.info("음량 조절: 9(작게 감소), 0(작게 증가), -(크게 감소), =(크게 증가), m 또는 /(음소거)")
    logger.info("탐색: ← →(5초 이동), ↑ ↓(30초 이동), Page Up/Down(1분 이동)")
    logger.info("재생 제어: 스페이스바/p(일시정지/재생)")
    logger.info("화면: f(전체화면), ESC(전체화면 종료)")
    logger.info("============================")

def play_rtsp(location, ip, bitrate=3000):
    """RTSP 스트림을 재생하는 함수 (mpv 또는 ffplay 사용)"""
    rtsp_url = f'rtsp://{ip}:554/{location}'
    
    # 비트레이트 값 검증
    if bitrate < 1000:
        bitrate = 1000
        logger.warning(f"비트레이트가 너무 낮아 1000Kbps로 조정했습니다.")
    elif bitrate > 10000:
        bitrate = 10000
        logger.warning(f"비트레이트가 너무 높아 10000Kbps로 조정했습니다.")
    
    logger.info(f"스트리밍 비트레이트: {bitrate}Kbps")
    
    # mpv 사용 시도
    try:
        # 사용자 정의 설정 파일 생성 (음량 조절 단축키 등)
        create_mpv_input_conf()
        log_mpv_keyboard_shortcuts()
        
        # 명시적으로 전체 경로 사용하고 추가 옵션 설정
        cmd = ['/opt/homebrew/bin/mpv', 
               '--rtsp-transport=tcp', 
               rtsp_url,
               '--title=RTSP: ' + location + ' (서버: ' + ip + ')',
               '--volume=50',
               '--force-window=yes',  # 강제로 창 표시
               '--no-terminal',       # 터미널 출력 비활성화
               '--geometry=50%',      # 화면 크기 50%로 설정
               '--osd-level=1']       # 화면 표시 정보 활성화
        
        logger.info(f"실행 명령: {' '.join(cmd)}")
        process = Popen(cmd)
        rtsp_processes.append(process)
        logger.info(f"MPV로 RTSP 스트림 시작: {rtsp_url}")
        return process.pid
    except FileNotFoundError:
        # Mac Homebrew 설치 경로 시도
        try:
            cmd[0] = '/opt/homebrew/bin/mpv'  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
            process = Popen(cmd)
            rtsp_processes.append(process)
            logger.info(f"Homebrew 경로에서 MPV로 RTSP 스트림 시작: {rtsp_url}")
            log_mpv_keyboard_shortcuts()
            return process.pid
        except Exception as e:
            try:
                cmd[0] = '/usr/local/bin/mpv'  # Intel Mac에서 Homebrew로 설치한 경우
                process = Popen(cmd)
                rtsp_processes.append(process)
                logger.info(f"Intel Mac Homebrew 경로에서 MPV로 RTSP 스트림 시작: {rtsp_url}")
                log_mpv_keyboard_shortcuts()
                return process.pid
            except Exception as e:
                logger.error(f"MPV 실행 오류, ffplay로 대체 시도: {e}")
                
                # mpv 실패 시 ffplay로 대체 시도
                cmd = ['ffplay', '-rtsp_transport', 'tcp', '-i', rtsp_url, 
                      '-x', '640', '-y', '480', '-window_title', f'{location}', '-volume', '50']
                
                try:
                    process = Popen(cmd)
                    rtsp_processes.append(process)
                    logger.info(f"ffplay로 RTSP 스트림 시작: {rtsp_url}")
                    return process.pid
                except FileNotFoundError:
                    # Mac Homebrew 설치 경로 시도
                    try:
                        cmd[0] = '/opt/homebrew/bin/ffplay'  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
                        process = Popen(cmd)
                        rtsp_processes.append(process)
                        logger.info(f"Homebrew 경로에서 ffplay로 RTSP 스트림 시작: {rtsp_url}")
                        return process.pid
                    except Exception as e:
                        try:
                            cmd[0] = '/usr/local/bin/ffplay'  # Intel Mac에서 Homebrew로 설치한 경우
                            process = Popen(cmd)
                            rtsp_processes.append(process)
                            logger.info(f"Intel Mac Homebrew 경로에서 ffplay로 RTSP 스트림 시작: {rtsp_url}")
                            return process.pid
                        except Exception as e:
                            logger.error(f"RTSP 스트림 실행 오류: {e}")
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
    
    rtsp_url = f'rtsp://{ip}:554/{location}'
    
    # 직접 트랜스코딩 방식으로 MP4 저장 (호환성과 안정성 향상)
    cmd = [
        'ffmpeg',
        '-y',                      # 기존 파일 덮어쓰기
        '-rtsp_transport', 'tcp',  # TCP 사용
        '-i', rtsp_url,            # 입력 RTSP 스트림
        '-c:v', 'libx264',         # 비디오 코덱: H.264
        '-preset', 'veryfast',     # 인코딩 속도 (빠른 인코딩)
        '-tune', 'zerolatency',    # 지연 최소화 튜닝
        '-profile:v', 'main',      # 프로파일 (호환성 개선)
        '-level', '4.0',           # 레벨 (호환성 개선)
        '-pix_fmt', 'yuv420p',     # 픽셀 포맷 (호환성 개선)
        '-r', '30',                # 프레임 레이트 30fps로 고정
        '-g', '60',                # GOP 크기 (키프레임 간격)
        '-keyint_min', '60',       # 최소 키프레임 간격
        '-sc_threshold', '0',      # 장면 변화 탐지 임계값 (0: 비활성화)
        '-b:v', f'{bitrate}k',     # 비디오 비트레이트
        '-maxrate', f'{bitrate*1.5}k', # 최대 비트레이트
        '-bufsize', f'{bitrate*3}k',   # 버퍼 크기
        '-c:a', 'aac',             # 오디오 코덱: AAC
        '-b:a', '192k',            # 오디오 비트레이트
        '-ar', '48000',            # 오디오 샘플 레이트
        '-af', 'aresample=async=1000', # 오디오 타이밍 조정
        '-threads', '4',           # 사용할 스레드 수
        '-movflags', '+faststart',  # 웹 스트리밍 최적화
        mp4_output_file            # 출력 파일
    ]
    
    logger.info(f"실행 명령: {' '.join(cmd)}")
    
    # ffmpeg 실행 경로 확인 (크로스 플랫폼)
    try:
        # 로그 파일로 출력 리디렉션
        with open(log_file, 'w') as log:
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
            except Exception as e:
                logger.error(f"MP4 녹화 실패: {e}")
                
                # 2. 대체 방식으로 MKV 저장 시도
                mkv_output_file = os.path.join(recordings_dir, f"{location}_{timestamp}.mkv")
                cmd = [
                    'ffmpeg',
                    '-y',
                    '-rtsp_transport', 'tcp',
                    '-i', rtsp_url,
                    '-c:v', 'libx264',
                    '-preset', 'veryfast',
                    '-tune', 'zerolatency',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-ar', '48000',
                    '-f', 'matroska',
                    mkv_output_file
                ]
                
                try:
                    process = Popen(cmd, stdout=log, stderr=log)
                    record_processes.append(process)
                    is_recording = True
                    logger.info(f"MKV 형식으로 RTSP 스트림 녹화 시작: {rtsp_url}")
                    logger.info(f"녹화 파일: {mkv_output_file}")
                    logger.info(f"로그 파일: {log_file}")
                    
                    # 영상 확인용 ffplay 실행
                    play_ffplay_monitor(rtsp_url, location)
                    
                    return process.pid
                except Exception as e:
                    logger.error(f"MKV 녹화 방식도 실패: {e}")
                    return None
    except FileNotFoundError:
        # Mac Homebrew 설치 경로 시도
        try:
            cmd[0] = '/opt/homebrew/bin/ffmpeg'  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
            with open(log_file, 'w') as log:
                try:
                    process = Popen(cmd, stdout=log, stderr=log)
                    record_processes.append(process)
                    is_recording = True
                    logger.info(f"Mac에서 RTSP 스트림 녹화 시작 (MP4): {rtsp_url}")
                    logger.info(f"녹화 파일: {mp4_output_file}")
                    logger.info(f"로그 파일: {log_file}")
                    
                    # 영상 확인용 ffplay 실행
                    play_ffplay_monitor(rtsp_url, location)
                    
                    return process.pid
                except Exception as e:
                    logger.error(f"Mac에서 MP4 녹화 실패: {e}")
                    
                    # 대체 방식으로 MKV 저장 시도
                    mkv_output_file = os.path.join(recordings_dir, f"{location}_{timestamp}.mkv")
                    cmd = [
                        '/opt/homebrew/bin/ffmpeg',
                        '-y',
                        '-rtsp_transport', 'tcp',
                        '-i', rtsp_url,
                        '-c:v', 'libx264',
                        '-preset', 'veryfast',
                        '-tune', 'zerolatency',
                        '-c:a', 'aac',
                        '-b:a', '192k',
                        '-ar', '48000',
                        '-f', 'matroska',
                        mkv_output_file
                    ]
                    
                    try:
                        process = Popen(cmd, stdout=log, stderr=log)
                        record_processes.append(process)
                        is_recording = True
                        logger.info(f"Mac에서 MKV 형식으로 RTSP 스트림 녹화 시작: {rtsp_url}")
                        logger.info(f"녹화 파일: {mkv_output_file}")
                        logger.info(f"로그 파일: {log_file}")
                        
                        # 영상 확인용 ffplay 실행
                        play_ffplay_monitor(rtsp_url, location)
                        
                        return process.pid
                    except Exception as e:
                        logger.error(f"Mac에서 MKV 녹화 방식도 실패: {e}")
                        return None
        except Exception as e:
            try:
                cmd[0] = '/usr/local/bin/ffmpeg'  # Intel Mac에서 Homebrew로 설치한 경우
                with open(log_file, 'w') as log:
                    try:
                        process = Popen(cmd, stdout=log, stderr=log)
                        record_processes.append(process)
                        is_recording = True
                        logger.info(f"Intel Mac에서 RTSP 스트림 녹화 시작 (MP4): {rtsp_url}")
                        logger.info(f"녹화 파일: {mp4_output_file}")
                        logger.info(f"로그 파일: {log_file}")
                        
                        # 영상 확인용 ffplay 실행
                        play_ffplay_monitor(rtsp_url, location)
                        
                        return process.pid
                    except Exception as e:
                        logger.error(f"Intel Mac에서 MP4 녹화 실패: {e}")
                        
                        # 대체 방식으로 MKV 저장 시도
                        mkv_output_file = os.path.join(recordings_dir, f"{location}_{timestamp}.mkv")
                        cmd = [
                            '/usr/local/bin/ffmpeg',
                            '-y',
                            '-rtsp_transport', 'tcp',
                            '-i', rtsp_url,
                            '-c:v', 'libx264',
                            '-preset', 'veryfast',
                            '-tune', 'zerolatency',
                            '-c:a', 'aac',
                            '-b:a', '192k',
                            '-ar', '48000',
                            '-f', 'matroska',
                            mkv_output_file
                        ]
                        
                        try:
                            process = Popen(cmd, stdout=log, stderr=log)
                            record_processes.append(process)
                            is_recording = True
                            logger.info(f"Intel Mac에서 MKV 형식으로 RTSP 스트림 녹화 시작: {rtsp_url}")
                            logger.info(f"녹화 파일: {mkv_output_file}")
                            logger.info(f"로그 파일: {log_file}")
                            
                            # 영상 확인용 ffplay 실행
                            play_ffplay_monitor(rtsp_url, location)
                            
                            return process.pid
                        except Exception as e:
                            logger.error(f"Intel Mac에서 모든 녹화 방식 실패: {e}")
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
        '/opt/homebrew/bin/mpv',
        '--rtsp-transport=tcp',
        rtsp_url,
        '--geometry=640x480',
        '--force-window=yes',
        f'--title={location} (녹화 모니터링 중)',
        '--volume=50',
        '--no-terminal',       # 터미널 출력 비활성화
        '--osd-level=1'
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
            cmd[0] = '/opt/homebrew/bin/mpv'  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
            process = Popen(cmd)
            rtsp_processes.append(process)
            logger.info(f"Homebrew 경로에서 MPV로 녹화 모니터링 시작: {rtsp_url}")
            log_mpv_keyboard_shortcuts()
            return process.pid
        except Exception as e:
            try:
                cmd[0] = '/usr/local/bin/mpv'  # Intel Mac에서 Homebrew로 설치한 경우
                process = Popen(cmd)
                rtsp_processes.append(process)
                logger.info(f"Intel Mac Homebrew 경로에서 MPV로 녹화 모니터링 시작: {rtsp_url}")
                log_mpv_keyboard_shortcuts()
                return process.pid
            except Exception as e:
                logger.error(f"MPV 실행 오류, ffplay로 대체 시도: {e}")
                
                # mpv 실패 시 ffplay 사용 시도
                cmd = [
                    'ffplay',
                    '-rtsp_transport', 'tcp',
                    '-i', rtsp_url,
                    '-x', '640',
                    '-y', '480',
                    '-window_title', f'{location} (녹화 모니터링 중)',
                    '-volume', '50'
                ]
                
                try:
                    process = Popen(cmd)
                    rtsp_processes.append(process)
                    logger.info(f"ffplay로 녹화 모니터링 시작: {rtsp_url}")
                    return process.pid
                except FileNotFoundError:
                    # Mac Homebrew 설치 경로 시도
                    try:
                        cmd[0] = '/opt/homebrew/bin/ffplay'  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
                        process = Popen(cmd)
                        rtsp_processes.append(process)
                        logger.info(f"Homebrew 경로에서 ffplay로 녹화 모니터링 시작: {rtsp_url}")
                        return process.pid
                    except Exception as e:
                        try:
                            cmd[0] = '/usr/local/bin/ffplay'  # Intel Mac에서 Homebrew로 설치한 경우
                            process = Popen(cmd)
                            rtsp_processes.append(process)
                            logger.info(f"Intel Mac Homebrew 경로에서 ffplay로 녹화 모니터링 시작: {rtsp_url}")
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
        
    rtsp_url = f'rtsp://{ip}:554/{location}'
    rtmp_url = f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
    
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
        'ffmpeg', '-re', '-timeout', '10000000', '-rtsp_transport', 'tcp',
        '-i', rtsp_url, 
        '-c:v', 'libx264', 
        '-b:v', f'{bitrate}k',  # 비트레이트 설정
        '-maxrate', f'{bitrate}k', 
        '-bufsize', f'{bitrate*2}k',
        '-preset', 'veryfast',  # 인코딩 속도/품질 설정
        '-tune', 'zerolatency',
        '-c:a', 'aac', 
        '-b:a', '128k',  # 오디오 비트레이트
        '-ar', '44100',
        '-f', 'flv',
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
    """모든 프로세스 정보 반환"""
    rtsp_info = []
    rtmp_info = []
    record_info = []  # 녹화 프로세스 정보 추가
    
    # RTSP 프로세스 정보
    for process in rtsp_processes:
        if process.poll() is None:  # 프로세스가 실행 중인지 확인
            rtsp_info.append({
                "pid": process.pid,
                "type": "rtsp"
            })
    
    # RTMP 프로세스 정보
    for process in rtmp_processes:
        if process.poll() is None:  # 프로세스가 실행 중인지 확인
            rtmp_info.append({
                "pid": process.pid,
                "type": "rtmp"
            })
    
    # 녹화 프로세스 정보
    for process in record_processes:
        if process.poll() is None:  # 프로세스가 실행 중인지 확인
            record_info.append({
                "pid": process.pid,
                "type": "record"
            })
    
    return {
        "rtsp": rtsp_info,
        "rtmp": rtmp_info,
        "record": record_info  # 녹화 프로세스 정보 추가
    }

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
        return {"status": "success", "message": f"RTSP 스트리밍 시작됨 (비트레이트: {bitrate}Kbps)", "pid": pid}
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
    background_tasks.add_task(_background_rtmp_task, location_code, stream_req.ip, stream_req.stream_key, bitrate)
    
    return {"status": "success", "message": f"RTMP 스트리밍 시작됨 (비트레이트: {bitrate}Kbps)"}

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

@app.post("/rtsp/record")
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
        return {"status": "success", "message": f"RTSP 스트림 녹화 시작: {location} (비트레이트: {bitrate}Kbps)", "pid": pid}
    else:
        raise HTTPException(status_code=500, detail="RTSP 스트림 녹화 시작 실패")

@app.post("/rtsp/record/stop")
def stop_rtsp_recording():
    """RTSP 스트림 녹화 중지"""
    global record_processes
    
    success = stop_recording()
    
    if success:
        return {"status": "success", "message": "RTSP 스트림 녹화가 중지되었습니다."}
    else:
        return {"status": "info", "message": "녹화 중인 스트림이 없습니다."}

@app.get("/rtsp/record/status")
def get_recording_status():
    """현재 녹화 상태 반환"""
    return {"is_recording": is_recording}

@app.post("/process/{pid}/stop")
def stop_process(pid: int):
    """특정 프로세스 종료"""
    global rtsp_processes, rtmp_processes, record_processes, is_recording
    
    # 모든 프로세스 목록에서 검색
    for process_list in [rtsp_processes, rtmp_processes, record_processes]:
        for i, process in enumerate(process_list):
            if process.pid == pid:
                try:
                    process.terminate()
                    process_list.pop(i)
                    
                    # 녹화 프로세스였다면 상태 업데이트
                    if process_list == record_processes and len(record_processes) == 0:
                        is_recording = False
                        
                    return {"status": "success", "message": f"프로세스 {pid} 종료됨"}
                except Exception as e:
                    logger.error(f"프로세스 {pid} 종료 실패: {e}")
                    raise HTTPException(status_code=500, detail=f"프로세스 종료 실패: {str(e)}")
    
    raise HTTPException(status_code=404, detail=f"프로세스 {pid}를 찾을 수 없습니다.")

@app.get("/processes")
def get_processes():
    """실행 중인 프로세스 목록 반환"""
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
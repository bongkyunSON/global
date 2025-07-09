@echo off
echo PC Control System - Windows Client
echo ===================================

REM 파이썬 설치 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 오류: Python이 설치되어 있지 않습니다.
    echo Python 3.8 이상을 설치해주세요.
    pause
    exit /b 1
)

REM 필요한 패키지 설치
echo 필요한 패키지를 설치하는 중...
pip install -r requirements.txt

REM 클라이언트 실행
echo 클라이언트를 시작합니다...
python client.py

pause 
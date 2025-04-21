@echo off
setlocal enabledelayedexpansion

REM 시작 메시지 표시
echo ===== 언론 파일 복사 도구 =====
echo.

REM 사용자로부터 파일 접두사 입력 받기ㅈ
set /p FILE_PREFIX="파일명을 입력하세요 (예: PHP202504021041): "

if "%FILE_PREFIX%"=="" (
    echo 파일 접두사를 입력해야 합니다.
    pause
    exit /b 1
)

REM Python이 설치되어 있는지 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python이 설치되어 있지 않습니다. 설치를 시작합니다...
    echo Python 설치 후 이 배치 파일을 다시 실행하세요.
    echo 다운로드 URL: https://www.python.org/downloads/
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

REM paramiko 패키지가 설치되어 있는지 확인
pip show paramiko >nul 2>&1
if %errorlevel% neq 0 (
    echo paramiko 패키지를 설치합니다...
    pip install paramiko
    if %errorlevel% neq 0 (
        echo paramiko 설치에 실패했습니다.
        pause
        exit /b 1
    )
)

REM 스크립트 실행
echo.
echo %FILE_PREFIX% 파일을 복사합니다...
echo.
python press_copy.py %FILE_PREFIX%

if %errorlevel% equ 0 (
    echo.
    echo 작업이 완료되었습니다.
) else (
    echo.
    echo 작업 중 오류가 발생했습니다.
)

pause 
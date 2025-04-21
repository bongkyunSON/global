#!/bin/bash

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

echo "========== 유튜브 스트리밍 시스템 시작 =========="

# 백그라운드에서 백엔드 서버 시작
echo "백엔드 서버 시작 중..."
if pgrep -f "python3 backend.py" > /dev/null; then
    echo "백엔드 서버가 이미 실행 중입니다."
else
    python3 backend.py &
    echo "백엔드 서버가 시작되었습니다."
fi

# 프론트엔드 앱 시작
echo "프론트엔드 앱 시작 중..."
cd rtsp-manager

if ! command -v npm &> /dev/null; then
    echo "NPM이 설치되어 있지 않습니다. 먼저 install_mac.command를 실행하세요."
    exit 1
fi

# 이미 실행 중인 프로세스 확인
if pgrep -f "node.*next" > /dev/null; then
    echo "프론트엔드 앱이 이미 실행 중입니다."
else
    npm run dev &
    echo "프론트엔드 앱이 시작되었습니다."
fi

echo "브라우저를 열어 http://localhost:3000 에 접속하세요."
echo "시스템이 실행 중입니다. 터미널 창을 닫으면 프로그램이 종료됩니다."
echo "아무 키나 누르면 프로그램이 종료됩니다."

# 브라우저 자동 실행
sleep 3
open http://localhost:3000

# 종료하지 않도록 대기
read -n 1 -s

# 프로세스 종료
echo "시스템을 종료합니다..."
pkill -f "python3 backend.py"
pkill -f "node.*next"

echo "시스템이 종료되었습니다." 
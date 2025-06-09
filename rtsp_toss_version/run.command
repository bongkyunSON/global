#!/bin/bash

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

echo "========== RTSP 스트리밍 서버 시작 =========="
echo ""

# 가상환경 정보 가져오기
if [ -f "venv_info.sh" ]; then
    source venv_info.sh
    echo "📦 가상환경 확인: $VENV_PATH"
else
    echo "❌ 가상환경 정보를 찾을 수 없습니다."
    echo "   먼저 'setup.command'를 실행해주세요."
    echo ""
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

# 가상환경 존재 확인
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 가상환경이 존재하지 않습니다."
    echo "   'setup.command'를 다시 실행해주세요."
    echo ""
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

# 가상환경 활성화
echo "🔌 가상환경 활성화 중..."
source "$VENV_PATH/bin/activate"

if [ $? -ne 0 ]; then
    echo "❌ 가상환경 활성화에 실패했습니다."
    echo "   'setup.command'를 다시 실행해주세요."
    echo ""
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

echo "✅ 가상환경 활성화 완료"

# Python 버전 확인
echo "🐍 Python 버전: $(python --version)"

# 필요한 파일 확인
echo "📄 필요한 파일 확인 중..."
if [ ! -f "backend.py" ]; then
    echo "❌ backend.py 파일을 찾을 수 없습니다."
    echo ""
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

# 이미 실행 중인 프로세스 확인 및 종료
echo "🔍 기존 프로세스 확인 중..."
if pgrep -f "python.*backend.py" > /dev/null; then
    echo "🛑 기존 백엔드 서버를 종료합니다..."
    pkill -f "python.*backend.py"
    sleep 2
fi

if pgrep -f "npm.*run.*dev\|node.*vite\|vite" > /dev/null; then
    echo "🛑 기존 프론트엔드 서버를 종료합니다..."
    pkill -f "npm.*run.*dev"
    pkill -f "node.*vite"
    pkill -f "vite"
    sleep 2
fi

# 포트 확인
echo "🌐 포트 8000 확인 중..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 포트 8000이 사용 중입니다. 강제 해제 중..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# 백엔드 서버 시작
echo ""
echo "🚀 백엔드 서버 시작 중..."
python backend.py &
BACKEND_PID=$!

# 백엔드 서버 시작 대기
echo "⏳ 백엔드 서버 시작 대기 중..."
sleep 3

# 백엔드 서버 확인
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ 백엔드 서버가 시작되었습니다 (PID: $BACKEND_PID)"
else
    echo "❌ 백엔드 서버 시작에 실패했습니다."
    echo ""
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

# 프론트엔드 서버 시작 (있는 경우)
FRONTEND_PID=""
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    echo ""
    echo "🌐 프론트엔드 서버 시작 중..."
    cd frontend
    
    # Node.js 확인
    if ! command -v npm &> /dev/null; then
        echo "⚠️ npm이 설치되어 있지 않습니다."
        echo "   백엔드만 실행됩니다."
        cd ..
    else
        npm run dev &
        FRONTEND_PID=$!
        cd ..
        
        # 프론트엔드 서버 시작 대기
        echo "⏳ 프론트엔드 서버 시작 대기 중..."
        sleep 3
        
        if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "✅ 프론트엔드 서버가 시작되었습니다 (PID: $FRONTEND_PID)"
        else
            echo "⚠️ 프론트엔드 서버 시작에 실패했습니다. 백엔드만 실행됩니다."
            FRONTEND_PID=""
        fi
    fi
else
    echo ""
    echo "ℹ️ 프론트엔드 폴더가 없습니다. 백엔드만 실행됩니다."
fi

# 서버 정보 출력
echo ""
echo "========== 서버 실행 중 =========="
echo "🎯 백엔드 서버: http://localhost:8000"
if [ -n "$FRONTEND_PID" ]; then
    echo "🌐 프론트엔드 서버: http://localhost:3000"
    echo ""
    echo "🚀 프론트엔드 서버가 자동으로 열립니다..."
    sleep 2
    open http://localhost:3000
else
    echo ""
    echo "🚀 백엔드 서버가 자동으로 열립니다..."
    sleep 2
    open http://localhost:8000
fi

echo ""
echo "서버가 실행 중입니다."
echo "종료하려면 아무 키나 누르세요..."
echo ""

# 종료 대기
read -n 1

# 서버 종료
echo ""
echo "🛑 서버를 종료합니다..."

if [ -n "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
    echo "   백엔드 서버 종료 중..."
    kill $BACKEND_PID 2>/dev/null
fi

if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "   프론트엔드 서버 종료 중..."
    kill $FRONTEND_PID 2>/dev/null
fi

# 강제 종료 (혹시 모를 경우)
pkill -f "python.*backend.py" 2>/dev/null
pkill -f "npm.*run.*dev" 2>/dev/null
pkill -f "node.*vite" 2>/dev/null
pkill -f "vite" 2>/dev/null

sleep 1

echo "✅ 서버가 종료되었습니다."
echo ""
echo "아무 키나 눌러서 종료..."
read -n 1 
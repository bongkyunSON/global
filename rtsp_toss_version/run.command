#!/bin/bash

# RTSP 스트리밍 서버 실행 스크립트 (Python 3.12 + 자동 재연결)
# 더블클릭으로 실행 가능

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

echo "========== 🔄 RTSP 스트리밍 서버 시작 =========="
echo "자동 재연결 기능이 포함된 RTSP 서버를 시작합니다."
echo ""

# 가상환경 정보 가져오기
if [ -f "venv_info.sh" ]; then
    source venv_info.sh
    echo "📦 가상환경 확인: $VENV_PATH"
    echo "🐍 Python 버전: Python 3.12"
else
    echo "❌ 가상환경 정보를 찾을 수 없습니다."
    echo "   먼저 'setup.command'를 실행해주세요."
    echo ""
    echo "💡 설치 방법:"
    echo "   1. 'setup.command' 파일을 더블클릭"
    echo "   2. 설치가 완료된 후 다시 실행"
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
echo "🔌 Python 3.12 가상환경 활성화 중..."
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
PYTHON_VERSION=$(python --version 2>&1)
echo "✅ Python 버전: $PYTHON_VERSION"

# 분석 히스토리 디렉토리 확인 및 생성
echo ""
echo "📁 분석 히스토리 디렉토리 확인 중..."
if [ ! -d "analysis_history" ]; then
    echo "📁 분석 히스토리 디렉토리 생성 중..."
    mkdir -p analysis_history/ocr_data
    mkdir -p analysis_history/ai_analysis_data
    echo "✅ 분석 히스토리 디렉토리가 생성되었습니다."
else
    echo "✅ 분석 히스토리 디렉토리가 존재합니다."
fi

# 필요한 파일 확인
echo ""
echo "📄 필요한 파일 확인 중..."
if [ ! -f "backend.py" ]; then
    echo "❌ backend.py 파일을 찾을 수 없습니다."
    echo "   프로젝트 파일이 올바른지 확인해주세요."
    echo ""
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

# FFmpeg와 MPV 확인
echo "🎬 미디어 도구 확인 중..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ FFmpeg가 설치되어 있지 않습니다."
    echo "   'setup.command'를 다시 실행해주세요."
fi

if ! command -v mpv &> /dev/null; then
    echo "⚠️ MPV가 설치되어 있지 않습니다."
    echo "   'setup.command'를 다시 실행해주세요."
fi

# 이미 실행 중인 프로세스 확인 및 종료
echo ""
echo "🔍 기존 프로세스 확인 중..."
if pgrep -f "python.*backend.py" > /dev/null; then
    echo "🛑 기존 백엔드 서버를 종료합니다..."
    pkill -f "python.*backend.py"
    sleep 2
    echo "   기존 서버 종료 완료"
fi

if pgrep -f "npm.*run.*dev\|node.*vite\|vite" > /dev/null; then
    echo "🛑 기존 프론트엔드 서버를 종료합니다..."
    pkill -f "npm.*run.*dev"
    pkill -f "node.*vite"
    pkill -f "vite"
    sleep 2
    echo "   기존 프론트엔드 서버 종료 완료"
fi

# 포트 확인 및 정리
echo "🌐 포트 8000 확인 중..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 포트 8000이 사용 중입니다. 강제 해제 중..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
    echo "   포트 정리 완료"
fi

# 백엔드 서버 시작
echo ""
echo "🚀 RTSP 백엔드 서버 시작 중..."
echo "   🔄 자동 재연결 모니터링 시스템 포함"
echo "   📊 분석 히스토리 관리 시스템 포함"
python backend.py &
BACKEND_PID=$!

# 백엔드 서버 시작 대기
echo "⏳ 백엔드 서버 시작 대기 중..."
for i in {1..10}; do
    sleep 1
    if kill -0 $BACKEND_PID 2>/dev/null; then
        if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "✅ 백엔드 서버가 시작되었습니다 (PID: $BACKEND_PID)"
            break
        fi
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ 백엔드 서버 시작에 실패했습니다."
        echo "   오류 로그를 확인해주세요."
        echo ""
        echo "아무 키나 눌러서 종료..."
        read -n 1
        exit 1
    fi
done

# 프론트엔드 서버 시작 (있는 경우)
FRONTEND_PID=""
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    echo ""
    echo "🌐 웹 인터페이스 확인 중..."
    
    # 빌드된 파일이 있는지 확인하고 최신 상태인지 체크
    if [ -d "frontend/dist" ]; then
        # 소스 파일이 빌드 파일보다 최신인지 확인
        if [ "frontend/src" -nt "frontend/dist" ] 2>/dev/null; then
            echo "⚠️ 소스 파일이 빌드 파일보다 최신입니다."
            echo "🔄 프론트엔드 새로 빌드 중..."
            
            # Node.js 확인
            if command -v npm &> /dev/null; then
                cd frontend
                npm run build
                if [ $? -eq 0 ]; then
                    echo "✅ 프론트엔드 빌드 완료"
                else
                    echo "⚠️ 프론트엔드 빌드 실패 - 기존 빌드 사용"
                fi
                cd ..
            else
                echo "⚠️ npm이 설치되어 있지 않습니다. 기존 빌드를 사용합니다."
            fi
        fi
        
        echo "✅ 최적화된 웹 인터페이스 사용 (빌드된 버전)"
        echo "   웹 인터페이스는 백엔드 서버에서 제공됩니다."
    else
        # Node.js 확인
        if ! command -v npm &> /dev/null; then
            echo "⚠️ npm이 설치되어 있지 않습니다."
            echo "   백엔드만 실행됩니다."
        else
            echo "🚀 개발용 웹 인터페이스 시작 중..."
            cd frontend
            npm run dev &
            FRONTEND_PID=$!
            cd ..
            
            # 프론트엔드 서버 시작 대기
            echo "⏳ 프론트엔드 서버 시작 대기 중..."
            sleep 5
            
            if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
                echo "✅ 개발용 웹 인터페이스가 시작되었습니다 (PID: $FRONTEND_PID)"
            else
                echo "⚠️ 개발용 웹 인터페이스 시작에 실패했습니다."
                echo "   최적화된 웹 인터페이스를 사용합니다."
                FRONTEND_PID=""
            fi
        fi
    fi
else
    echo ""
    echo "ℹ️ 프론트엔드 폴더가 없습니다. 백엔드만 실행됩니다."
fi

# 서버 정보 출력
echo ""
echo "========== 🎉 서버 실행 중 =========="
echo ""
echo "🌟 RTSP 스트리밍 서버가 성공적으로 시작되었습니다!"
echo ""
echo "📡 서버 주소:"
echo "   🎯 메인 서버: http://localhost:8000"

if [ -n "$FRONTEND_PID" ]; then
    echo "   🌐 개발 서버: http://localhost:3000"
    WEB_URL="http://localhost:3000"
else
    WEB_URL="http://localhost:8000"
fi

echo ""
echo "💫 주요 기능:"
echo "   🔄 RTSP 스트림 자동 재연결 (플레이어가 꺼져도 자동 복구)"
echo "   📺 실시간 스트리밍 재생"
echo "   🎮 카메라 원격 제어"
echo "   🔧 장치 리셋 기능"
echo "   🤖 AI 포스터 분석 (Upstage OCR + AI 분석)"
echo "   📊 분석 히스토리 (최근 5개 분석 결과 저장/조회)"
echo "   💾 OCR 및 AI 분석 결과 자동 저장"
echo ""
echo "🚀 웹 브라우저가 자동으로 열립니다..."

# 브라우저 자동 열기
sleep 2
open "$WEB_URL"

echo ""
echo "💡 사용 팁:"
echo "   • RTSP 스트림이 끊어져도 자동으로 재연결됩니다"
echo "   • 웹 인터페이스에서 모든 기능을 사용하세요"
echo "   • 분석 히스토리 탭에서 과거 분석 결과를 확인하세요"
echo "   • AI 포스터 분석 결과는 자동으로 저장됩니다"
echo "   • 문제 발생 시 서버를 재시작해보세요"
echo ""
echo "⭐ 서버가 실행 중입니다."
echo "   종료하려면 아무 키나 누르세요..."
echo ""

# 종료 대기
read -n 1

# 서버 종료
echo ""
echo "🛑 서버를 종료합니다..."
echo ""

if [ -n "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
    echo "   📡 백엔드 서버 종료 중..."
    kill $BACKEND_PID 2>/dev/null
    sleep 1
fi

if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "   🌐 프론트엔드 서버 종료 중..."
    kill $FRONTEND_PID 2>/dev/null
    sleep 1
fi

# 강제 종료 (혹시 모를 경우)
echo "   🧹 남은 프로세스 정리 중..."
pkill -f "python.*backend.py" 2>/dev/null
pkill -f "npm.*run.*dev" 2>/dev/null
pkill -f "node.*vite" 2>/dev/null
pkill -f "vite" 2>/dev/null

# RTSP 프로세스도 정리 (사용자가 열었던 스트림들)
pkill -f "mpv.*rtsp" 2>/dev/null
pkill -f "ffplay.*rtsp" 2>/dev/null

sleep 1

echo ""
echo "✅ 모든 서버와 스트림이 종료되었습니다."
echo ""
echo "🔄 자동 재연결 모니터링도 중지되었습니다."
echo "📊 분석 히스토리는 analysis_history/ 폴더에 저장되어 있습니다."
echo ""
echo "감사합니다! 다시 사용하시려면 이 파일을 더블클릭하세요."
echo ""
echo "아무 키나 눌러서 종료..."
read -n 1 
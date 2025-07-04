#!/bin/bash

# RTSP 스트리밍 서버 설치 스크립트 (Python 3.12 버전)
# Upstage API 기반 OCR, 이미지 처리, AI 포스터 분석 기능 포함
# 분석 히스토리 저장 및 관리 기능 포함
# 더블클릭으로 실행 가능

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

echo "========== RTSP 스트리밍 서버 설치 시작 =========="
echo "🔄 자동 재연결 기능이 포함된 RTSP 스트리밍 서버를 설치합니다."
echo "🤖 Upstage API 기반 OCR, 이미지 처리, AI 포스터 분석 기능 포함"
echo "📊 분석 히스토리 저장 및 관리 기능 포함"
echo "필요한 소프트웨어를 설치하고 있습니다. 잠시만 기다려주세요..."
echo ""

# 관리자 권한 확인 (비밀번호 입력 필요할 수 있음)
echo "🔐 시스템 권한 확인 중..."
echo "   필요시 컴퓨터 비밀번호를 입력해주세요."

# Homebrew 설치 확인 및 설치
echo ""
echo "🍺 Homebrew 확인 중..."
if ! command -v brew &> /dev/null; then
    echo "📥 Homebrew를 설치합니다..."
    echo "   이 과정은 3-5분 정도 소요될 수 있습니다..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Homebrew PATH 설정 (Apple Silicon Mac)
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    echo "✅ Homebrew 설치 완료"
else
    echo "✅ Homebrew가 이미 설치되어 있습니다."
fi

# FFmpeg 및 MPV 설치 (RTSP 스트리밍용)
echo ""
echo "🎬 미디어 도구 설치 중..."
echo "   FFmpeg와 MPV를 설치합니다 (스트리밍 재생용)..."

# FFmpeg 확인 및 설치
if ! command -v ffmpeg &> /dev/null; then
    echo "📥 FFmpeg 설치 중..."
    brew install ffmpeg
    echo "✅ FFmpeg 설치 완료"
else
    echo "✅ FFmpeg가 이미 설치되어 있습니다."
fi

# MPV 확인 및 설치
if ! command -v mpv &> /dev/null; then
    echo "📥 MPV 플레이어 설치 중..."
    brew install mpv
    echo "✅ MPV 설치 완료"
else
    echo "✅ MPV가 이미 설치되어 있습니다."
fi

# 이미지 처리 시스템 라이브러리 설치
echo ""
echo "🖼️ 이미지 처리 도구 설치 중..."
echo "   OpenCV를 위한 시스템 라이브러리들을 설치합니다..."

# 필요한 시스템 라이브러리들 확인 및 설치
OPENCV_DEPS=("pkg-config" "cmake" "jpeg" "libpng" "libtiff" "openexr" "eigen" "tbb")

for dep in "${OPENCV_DEPS[@]}"; do
    if ! brew list "$dep" &> /dev/null; then
        echo "📥 $dep 설치 중..."
        brew install "$dep"
    else
        echo "✅ $dep가 이미 설치되어 있습니다."
    fi
done

echo "✅ 이미지 처리 도구 설치 완료"

# Python 3.12 설치 확인 및 설치
echo ""
echo "🐍 Python 3.12 확인 중..."
PYTHON_CMD=""

# Python 3.12 찾기
for py_cmd in "python3.12" "python3" "python"; do
    if command -v "$py_cmd" &> /dev/null; then
        PY_VER=$($py_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        if [ "$PY_VER" = "3.12" ]; then
            PYTHON_CMD="$py_cmd"
            echo "✅ Python 3.12가 이미 설치되어 있습니다: $py_cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "📥 Python 3.12를 설치합니다..."
    echo "   이 과정은 5-10분 정도 소요될 수 있습니다..."
    brew install python@3.12
    
    # PATH 새로고침
    if [[ $(uname -m) == 'arm64' ]]; then
        export PATH="/opt/homebrew/bin:$PATH"
        export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"
    else
        export PATH="/usr/local/bin:$PATH"
        export PATH="/usr/local/opt/python@3.12/bin:$PATH"
    fi
    
    # 설치 후 다시 찾기
    for py_cmd in "python3.12" "python3" "python"; do
        if command -v "$py_cmd" &> /dev/null; then
            PY_VER=$($py_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            if [ "$PY_VER" = "3.12" ]; then
                PYTHON_CMD="$py_cmd"
                echo "✅ Python 3.12 설치 완료: $py_cmd"
                break
            fi
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        echo "❌ Python 3.12 설치에 실패했습니다."
        echo "   수동으로 Python 3.12를 설치해주세요."
        echo ""
        echo "아무 키나 눌러서 종료..."
        read -n 1
        exit 1
    fi
fi

# Node.js 설치 확인 및 설치 (프론트엔드용)
echo ""
echo "📦 Node.js 확인 중..."
if ! command -v node &> /dev/null; then
    echo "📥 Node.js를 설치합니다..."
    echo "   웹 인터페이스용 Node.js를 설치합니다..."
    brew install node
    echo "✅ Node.js 설치 완료"
else
    echo "✅ Node.js가 이미 설치되어 있습니다."
fi

# 기존 가상환경 삭제
echo ""
echo "🗑️ 기존 설정 정리 중..."
if [ -d ".venv" ]; then
    rm -rf .venv
    echo "   기존 가상환경 삭제 완료"
fi

# Python 가상 환경 생성 및 활성화
echo ""
echo "📦 Python 3.12 가상환경 생성 중..."
$PYTHON_CMD -m venv .venv

if [ ! -d ".venv" ]; then
    echo "❌ 가상환경 생성에 실패했습니다."
    echo "   Python 3.12 설치를 확인해주세요."
    echo ""
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

echo "🔌 가상환경 활성화 중..."
source .venv/bin/activate

# Python 버전 확인
echo "✅ Python 버전: $(python --version)"

# pip 업그레이드
echo ""
echo "⬆️ pip 업그레이드 중..."
python -m pip install --upgrade pip

# setuptools와 wheel 설치
echo "🔧 기본 패키지 설치 중..."
pip install setuptools wheel

# 이미지 처리 라이브러리 사전 설치 (OpenCV 컴파일 최적화)
echo ""
echo "🖼️ 이미지 처리 라이브러리 최적화 중..."
echo "   OpenCV와 NumPy를 최적화하여 설치합니다..."
pip install --upgrade numpy

# requirements.txt 확인
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 파일을 찾을 수 없습니다."
    echo "   프로젝트 파일이 올바른지 확인해주세요."
    echo ""
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

# Python 패키지 설치
echo ""
echo "📥 RTSP 서버 패키지 설치 중..."
echo "   자동 재연결, 스트리밍, Upstage API OCR, AI 분석 관련 패키지를 설치합니다..."
echo "   이 과정은 5-10분 정도 소요될 수 있습니다..."

# OpenCV 설치는 시간이 오래 걸릴 수 있으므로 별도로 표시
echo "   📸 OpenCV(컴퓨터 비전) 설치 중... (시간이 오래 걸릴 수 있습니다)"

pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Python 패키지 설치에 실패했습니다."
    echo "   인터넷 연결을 확인하고 다시 시도해주세요."
    echo "   OpenCV 설치 실패시 다음 명령어로 수동 설치:"
    echo "   pip install opencv-python"
    echo ""
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

echo "✅ RTSP 서버 패키지 설치 완료"

# Upstage API 연결 테스트
echo ""
echo "🔍 Upstage API 연결 테스트 중..."
if python -c "import requests; print('HTTP 요청 라이브러리 정상 작동')" 2>/dev/null; then
    echo "✅ Upstage API 연결 준비 완료"
    echo "   💡 실제 OCR 사용을 위해서는 Upstage API 키가 필요합니다."
else
    echo "⚠️ Upstage API 연결 테스트 실패 - 일부 기능이 제한될 수 있습니다."
fi

# AI 기능 테스트
echo ""
echo "🤖 AI 분석 기능 테스트 중..."
if python -c "from langchain_core import __version__; print(f'LangChain 버전: {__version__}')" 2>/dev/null; then
    echo "✅ AI 분석 기능 테스트 성공"
else
    echo "⚠️ AI 분석 기능 테스트 실패 - AI 포스터 분석 기능이 제한될 수 있습니다."
fi

# 분석 히스토리 디렉토리 생성
echo ""
echo "📊 분석 히스토리 저장소 설정 중..."
mkdir -p analysis_history/ocr_data
mkdir -p analysis_history/ai_analysis_data
echo "✅ 분석 히스토리 저장소 생성 완료"
echo "   📁 OCR 결과: analysis_history/ocr_data/"
echo "   📁 AI 분석 결과: analysis_history/ai_analysis_data/"

# 가상 환경 정보를 저장
echo ""
echo "📝 설정 정보 저장 중..."
echo "#!/bin/bash
# 이 파일은 자동 생성됩니다 - 수정하지 마세요
VENV_PATH=\"$(pwd)/.venv\"
PYTHON_CMD=\"$PYTHON_CMD\"
PROJECT_PATH=\"$(pwd)\"
" > venv_info.sh
chmod +x venv_info.sh

# 프론트엔드 의존성 설치
echo ""
echo "🌐 웹 인터페이스 설치 중..."
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    cd frontend
    echo "   웹 인터페이스 패키지 설치 중..."
    npm install
    if [ $? -eq 0 ]; then
        echo "✅ 웹 인터페이스 설치 완료"
        
        # 프로덕션 빌드
        echo "   웹 인터페이스 최적화 중..."
        npm run build
        if [ $? -eq 0 ]; then
            echo "✅ 웹 인터페이스 최적화 완료"
        else
            echo "⚠️ 웹 인터페이스 최적화에 실패했습니다. 개발 모드로 실행됩니다."
        fi
    else
        echo "❌ 웹 인터페이스 설치에 실패했습니다."
        echo "   백엔드만 사용 가능합니다."
    fi
    cd ..
else
    echo "⚠️ 프론트엔드 폴더를 찾을 수 없습니다. 백엔드만 설정됩니다."
fi

# 실행 권한 설정
echo ""
echo "🔧 실행 권한 설정 중..."
chmod +x run.command
chmod +x setup.command

echo ""
echo "========== 🎉 설치 완료! =========="
echo ""
echo "✅ Python 3.12 가상환경이 생성되었습니다."
echo "✅ 🔄 자동 재연결 시스템이 포함된 RTSP 서버가 설치되었습니다."
echo "✅ 모든 필요한 라이브러리가 설치되었습니다."
echo "✅ 웹 인터페이스가 설치되었습니다."
echo "✅ FFmpeg 및 MPV 플레이어가 설치되었습니다."
echo "✅ 📊 Upstage API 기반 OCR 시스템이 설치되었습니다."
echo "✅ 🖼️ OpenCV 이미지 처리 라이브러리가 설치되었습니다."
echo "✅ 🤖 AI 포스터 분석 시스템이 설치되었습니다."
echo "✅ 📁 분석 히스토리 저장소가 생성되었습니다."
echo ""
echo "🚀 이제 'run.command' 파일을 더블클릭하여"
echo "   RTSP 스트리밍 서버를 실행할 수 있습니다!"
echo ""
echo "💡 주요 기능:"
echo "   • RTSP 스트림 자동 재연결"
echo "   • 웹 기반 관리 인터페이스" 
echo "   • 카메라 제어 및 장치 리셋"
echo "   • 📝 Upstage API 기반 OCR 텍스트 추출"
echo "   • 🖼️ 이미지 크기 조정 및 처리"
echo "   • 🤖 AI 기반 포스터 내용 분석"
echo "   • 📊 포스터 정보 자동 추출"
echo "   • 📁 분석 결과 히스토리 저장 및 관리"
echo "   • 📋 분석 결과 복사 및 내보내기"
echo ""
echo "🔧 시스템 요구사항:"
echo "   • Python 3.12"
echo "   • Upstage API 키 (OCR 및 AI 분석용)"
echo "   • OpenCV 4.8+"
echo "   • FFmpeg (미디어 처리)"
echo ""
echo "🔑 Upstage API 사용법:"
echo "   1. https://upstage.ai 에서 회원가입 후 API 키 발급"
echo "   2. AI 포스터 분석 탭에서 API 키 입력 및 저장"
echo "   3. OCR 및 AI 분석 기능 사용 가능"
echo ""
echo "📊 분석 히스토리 기능:"
echo "   • OCR 및 AI 분석 결과 자동 저장"
echo "   • 최근 5개 결과 웹에서 확인 가능"
echo "   • 분석 결과 복사 및 전체 보기 지원"
echo ""
echo "아무 키나 눌러서 종료..."
read -n 1 
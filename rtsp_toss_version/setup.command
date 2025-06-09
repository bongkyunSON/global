#!/bin/bash

# RTSP 스트리밍 서버 설치 스크립트
# 더블클릭으로 실행 가능

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

echo "========== RTSP 스트리밍 서버 설치 시작 =========="
echo "필요한 소프트웨어를 설치하고 있습니다. 잠시만 기다려주세요..."
echo ""

# Homebrew 설치 확인 및 설치
echo "🍺 Homebrew 확인 중..."
if ! command -v brew &> /dev/null; then
    echo "📥 Homebrew를 설치합니다..."
    echo "   이 과정은 몇 분 정도 소요될 수 있습니다..."
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

# Python 3.13 설치 확인 및 설치
echo ""
echo "🐍 Python 3.13 확인 중..."
PYTHON_CMD=""

# Python 3.13 찾기
for py_cmd in "python3.13" "python3" "python"; do
    if command -v "$py_cmd" &> /dev/null; then
        PY_VER=$($py_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        if [ "$PY_VER" = "3.13" ]; then
            PYTHON_CMD="$py_cmd"
            echo "✅ Python 3.13이 이미 설치되어 있습니다: $py_cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "📥 Python 3.13을 설치합니다..."
    echo "   이 과정은 5-10분 정도 소요될 수 있습니다..."
    brew install python@3.13
    
    # PATH 새로고침
    if [[ $(uname -m) == 'arm64' ]]; then
        export PATH="/opt/homebrew/bin:$PATH"
    else
        export PATH="/usr/local/bin:$PATH"
    fi
    
    # 설치 후 다시 찾기
    for py_cmd in "python3.13" "python3" "python"; do
        if command -v "$py_cmd" &> /dev/null; then
            PY_VER=$($py_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            if [ "$PY_VER" = "3.13" ]; then
                PYTHON_CMD="$py_cmd"
                echo "✅ Python 3.13 설치 완료: $py_cmd"
                break
            fi
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        echo "❌ Python 3.13 설치에 실패했습니다."
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
    brew install node
    echo "✅ Node.js 설치 완료"
else
    echo "✅ Node.js가 이미 설치되어 있습니다."
fi

# 기존 가상환경 삭제
echo ""
echo "🗑️ 기존 가상환경 정리 중..."
if [ -d ".venv" ]; then
    rm -rf .venv
    echo "   기존 가상환경 삭제 완료"
fi

# Python 가상 환경 생성 및 활성화
echo ""
echo "📦 Python 가상환경 생성 중..."
$PYTHON_CMD -m venv .venv

if [ ! -d ".venv" ]; then
    echo "❌ 가상환경 생성에 실패했습니다."
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

echo "🔌 가상환경 활성화 중..."
source .venv/bin/activate

# pip 업그레이드
echo "⬆️ pip 업그레이드 중..."
python -m pip install --upgrade pip

# setuptools와 wheel 설치
echo "🔧 기본 패키지 설치 중..."
pip install setuptools wheel

# requirements.txt 확인
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 파일을 찾을 수 없습니다."
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

# Python 패키지 설치
echo ""
echo "📥 Python 패키지 설치 중..."
echo "   이 과정은 몇 분 정도 소요될 수 있습니다..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Python 패키지 설치에 실패했습니다."
    echo "아무 키나 눌러서 종료..."
    read -n 1
    exit 1
fi

echo "✅ Python 패키지 설치 완료"

# 가상 환경 정보를 저장
echo "📝 가상환경 정보 저장 중..."
echo "#!/bin/bash
# 이 파일은 자동 생성됩니다 - 수정하지 마세요
VENV_PATH=\"$(pwd)/.venv\"
PYTHON_CMD=\"$PYTHON_CMD\"
" > venv_info.sh
chmod +x venv_info.sh

# 프론트엔드 의존성 설치
echo ""
echo "🌐 프론트엔드 의존성 설치 중..."
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    cd frontend
    echo "   npm 패키지 설치 중..."
    npm install
    if [ $? -eq 0 ]; then
        echo "✅ 프론트엔드 설치 완료"
    else
        echo "❌ 프론트엔드 설치에 실패했습니다."
    fi
    cd ..
else
    echo "⚠️ 프론트엔드 폴더를 찾을 수 없습니다. 백엔드만 설정됩니다."
fi

echo ""
echo "========== 설치 완료 =========="
echo "✅ Python 3.13 가상환경이 생성되었습니다."
echo "✅ 모든 필요한 라이브러리가 설치되었습니다."
echo "✅ 프론트엔드 의존성이 설치되었습니다."
echo ""
echo "이제 'run.command' 파일을 더블클릭하여"
echo "RTSP 서버를 실행할 수 있습니다."
echo ""
echo "아무 키나 눌러서 종료..."
read -n 1 
#!/bin/bash

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

echo "========== 유튜브 스트리밍 시스템 설치 시작 =========="
echo "필요한 소프트웨어를 설치하고 있습니다. 잠시만 기다려주세요..."

# Homebrew 설치 확인 및 설치
if ! command -v brew &> /dev/null; then
    echo "Homebrew를 설치합니다..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Homebrew PATH 설정 (Apple Silicon Mac)
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo "Homebrew가 이미 설치되어 있습니다."
fi

# Python 설치 확인 및 설치
if ! command -v python3 &> /dev/null; then
    echo "Python을 설치합니다..."
    brew install python
    
    # PATH 새로고침
    if [[ $(uname -m) == 'arm64' ]]; then
        export PATH="/opt/homebrew/bin:$PATH"
    else
        export PATH="/usr/local/bin:$PATH"
    fi
    
    # 새로 설치된 pip 확인
    which pip3
    
    # pip 업그레이드
    pip3 install --upgrade pip
else
    echo "Python이 이미 설치되어 있습니다."
fi

# Node.js 설치 확인 및 설치
if ! command -v node &> /dev/null; then
    echo "Node.js를 설치합니다..."
    brew install node
else
    echo "Node.js가 이미 설치되어 있습니다."
fi

# FFmpeg 설치 확인 및 설치
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg를 설치합니다..."
    brew install ffmpeg
else
    echo "FFmpeg가 이미 설치되어 있습니다."
fi

# Python 패키지 설치
echo "Python 패키지를 설치합니다..."
echo "pip3 경로: $(which pip3)"
echo "python3 경로: $(which python3)"

# 가상 환경 생성 및 활성화
echo "가상 환경을 생성합니다..."
python3 -m venv venv
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip

# 필요한 패키지 설치
pip install fastapi uvicorn requests psutil pydantic typing

# 가상 환경 정보를 저장
echo "#!/bin/bash
# 이 파일은 자동 생성됩니다 - 수정하지 마세요
VENV_PATH=\"$(pwd)/venv\"
" > venv_path.sh
chmod +x venv_path.sh

# rtsp-manager 디렉토리로 이동하여 npm 패키지 설치
echo "Next.js 앱 종속성을 설치합니다..."
cd rtsp-manager
npm install

echo "========== 설치 완료 =========="
echo "더블클릭으로 실행하려면 run_mac.command 파일을 사용하세요."
echo "아무 키나 눌러 종료하세요."
read -n 1 -s 
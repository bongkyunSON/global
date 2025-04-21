#!/bin/bash

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

echo "스크립트에 실행 권한을 부여합니다..."

chmod +x install_mac.command
chmod +x 실행.command
chmod +x make_scripts_executable.command

echo "완료되었습니다. 이제 install_mac.command와 실행.command를 더블클릭하여 실행할 수 있습니다."
echo "아무 키나 눌러 종료하세요."
read -n 1 -s 
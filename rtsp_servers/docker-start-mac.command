#!/bin/bash
# RTSP 서버 Docker 실행 스크립트 (Mac 용)

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

echo "========== RTSP 서버 시작 중 =========="

# Docker가 실행 중인지 확인
if ! docker info > /dev/null 2>&1; then
  echo "Docker가 실행되고 있지 않습니다. Docker Desktop을 먼저 실행해주세요."
  echo "아무 키나 누르면 종료합니다..."
  read -n 1
  exit 1
fi

# 이전 컨테이너 정리
echo "이전 컨테이너를 정리합니다..."
docker rm -f rtsp-server 2>/dev/null || true

# 로컬에 이미지가 없으면 빌드
if [[ "$(docker images -q bongkyunson/global:version1.1.2 2> /dev/null)" == "" ]]; then
  echo "Docker 이미지를 다운로드합니다..."
  docker pull bongkyunson/global:version1.1.2
fi

# 컨테이너 실행 - 명시적 포트 매핑 사용
echo "RTSP 서버를 시작합니다..."
docker run -d --name rtsp-server -p 8000:8000 -p 3000:3000 bongkyunson/global:version1.1.2

# 서비스가 시작될 때까지 기다림
echo "서비스가 시작될 때까지 기다리는 중..."
sleep 10

# 브라우저 열기
echo "브라우저를 엽니다..."
open http://localhost:3000

echo ""
echo "========== 사용 방법 =========="
echo "1. 브라우저에서 RTSP 서버 웹 인터페이스를 사용할 수 있습니다."
echo "2. 종료하려면 아무 키나 누르세요."
echo "========== ======== =========="

# 키 입력 대기
read -n 1 -s

# 컨테이너 종료
echo "RTSP 서버를 종료합니다..."
docker stop rtsp-server

echo "종료되었습니다." 
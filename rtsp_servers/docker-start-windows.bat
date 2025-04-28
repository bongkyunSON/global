@echo off
rem RTSP 서버 Docker 실행 스크립트 (Windows 용)

echo ========== RTSP 서버 시작 중 ==========

rem Docker가 실행 중인지 확인
docker info > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Docker가 실행되고 있지 않습니다. Docker Desktop을 먼저 실행해주세요.
  echo 아무 키나 누르면 종료합니다...
  pause > nul
  exit /b
)

rem 이전 컨테이너 정리
echo 이전 컨테이너를 정리합니다...
docker rm -f rtsp-server > nul 2>&1

rem 로컬에 이미지가 없으면 빌드
docker images -q rtsp-server:latest 2> nul | findstr /r "." > nul
if %ERRORLEVEL% NEQ 0 (
  echo Docker 이미지를 빌드합니다. 처음 실행 시 몇 분 정도 소요됩니다...
  docker build -t rtsp-server:latest .
)

rem 컨테이너 실행 - 호스트 네트워크 모드 사용
echo RTSP 서버를 시작합니다...
docker run -d --name rtsp-server -p 8000:8000 -p 3000:3000 bongkyunson/global:version1.1.2

rem 브라우저 열기
echo 잠시 후 브라우저가 열립니다...
timeout /t 5 > nul
start http://localhost:3000

echo.
echo ========== 사용 방법 ==========
echo 1. 브라우저에서 RTSP 서버 웹 인터페이스를 사용할 수 있습니다.
echo 2. 종료하려면 아무 키나 누르세요.
echo ========== ======== ==========

rem 키 입력 대기
pause > nul

rem 컨테이너 종료
echo RTSP 서버를 종료합니다...
docker stop rtsp-server

echo 종료되었습니다. 
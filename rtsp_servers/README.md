# RTSP 서버 Docker 배포 안내서

이 문서는 RTSP 서버 프로젝트를 Docker를 사용하여 배포하고 실행하는 방법을 설명합니다.

## 1. 사전 준비사항

### Docker Desktop 설치

- **Windows**: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop) 다운로드 후 설치
- **Mac**: [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop) 다운로드 후 설치

## 2. 설치 및 실행 방법

### 비개발자용 간편 실행 방법

1. Docker Desktop을 실행합니다.
2. 배포된 파일 중 운영체제에 맞는 실행 스크립트를 더블클릭합니다:
   - Windows: `docker-start-windows.bat`
   - Mac: `docker-start-mac.command`
3. 처음 실행 시 Docker 이미지 빌드에 몇 분이 소요될 수 있습니다.
4. 브라우저가 자동으로 열리면서 RTSP 서버 웹 인터페이스가 표시됩니다.
5. 종료하려면 실행 창에서 아무 키나 누르세요.

### 수동 실행 방법 (개발자용)

```bash
# 이미지 빌드
docker build -t rtsp-server .

# 컨테이너 실행
docker run -d --name rtsp-server -p 8000:8000 -p 3000:3000 rtsp-server
```

## 3. 문제 해결

### 실행 오류 시 확인사항

1. **Docker Desktop이 실행 중인지 확인**
   - Docker 아이콘이 상태표시줄/작업표시줄에 표시되어 있어야 합니다.

2. **포트 충돌 문제**
   - 다른 애플리케이션이 8000번 또는 3000번 포트를 사용 중인 경우 충돌이 발생할 수 있습니다.
   - 이 경우 실행 스크립트를 텍스트 편집기로 열어서 포트 번호를 변경하세요.

3. **이미지 재빌드**
   - 문제가 지속되면 이미지를 삭제하고 다시 빌드해보세요:
   ```bash
   docker rm -f rtsp-server
   docker rmi rtsp-server
   ```
   - 이후 실행 스크립트를 다시 실행하세요.

## 4. 추가 정보

- 웹 인터페이스 URL: http://localhost:3000
- API 서버 URL: http://localhost:8000

## 5. 배포 방법 (관리자용)

다른 사용자에게 배포할 때 필요한 파일:

1. `Dockerfile`
2. 프로젝트 소스코드 전체
3. `docker-start-windows.bat` (Windows 사용자용)
4. `docker-start-mac.command` (Mac 사용자용)
5. 이 README.md 파일

또는 Docker Hub에 이미지를 업로드한 후 스크립트를 수정하여 `docker build` 대신 `docker pull` 명령을 사용하도록 할 수 있습니다. 
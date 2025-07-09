# PC방용 로그인 제어 시스템

## 프로젝트 개요

PC방 좌석처럼 각 PC에서 로그인을 하지 않으면 해당 PC의 사용이 불가능하도록 제어하는 시스템입니다.

## 시스템 구성

- **제어 PC**: 1대 (macOS) - 중앙 관리 서버
- **제어 대상 PC**: 6대 (Windows) - 클라이언트 PC들

## 주요 기능

1. **로그인 제어**: Windows PC에서 로그인 필수 (이름 + 소속)
2. **화면 잠금**: 로그인하지 않으면 PC 사용 불가
3. **실시간 모니터링**: 전체 PC 상태 실시간 확인
4. **Slack 연동**: 로그인 시 Slack 메시지 전송
5. **동시 로그인 방지**: 같은 사용자의 중복 로그인 방지

## 기술 스택

- **Backend**: FastAPI + WebSocket
- **Frontend**: React + Vite
- **Windows Client**: Python + tkinter
- **Database**: SQLite
- **Deployment**: Docker Compose

## 프로젝트 구조

```
pc_control_system/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py         # 메인 애플리케이션
│   │   ├── models.py       # 데이터 모델
│   │   ├── websocket_manager.py  # WebSocket 연결 관리
│   │   └── slack_integration.py  # Slack 연동
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React 관리 대시보드
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── contexts/       # React 컨텍스트
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── windows_client/         # Windows 클라이언트
│   ├── client.py          # 메인 클라이언트
│   ├── login_screen.py    # 로그인 화면
│   ├── requirements.txt
│   └── run_client.bat
├── docker-compose.yml
└── README.md
```

## 실행 방법

### 1. 서버 실행 (macOS)

```bash
# 프로젝트 디렉토리로 이동
cd pc_control_system

# Docker Compose로 서버 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 2. Windows 클라이언트 실행

```bash
# 각 Windows PC에서 실행
cd windows_client
run_client.bat

# 또는 수동으로 실행
python client.py
```

## 개발 환경 설정

### 서버 (macOS)

1. Docker & Docker Compose 설치
2. Git 클론 후 프로젝트 디렉토리로 이동
3. `docker-compose up -d`로 실행

### 클라이언트 (Windows)

1. Python 3.8+ 설치
2. `windows_client` 폴더를 각 PC에 복사
3. `run_client.bat` 실행

## 네트워크 설정

### 서버 IP 주소 설정

Windows 클라이언트에서 `client.py` 파일의 `server_host` 변수를 서버 IP 주소로 변경:

```python
self.server_host = "192.168.1.100"  # 서버 IP 주소로 변경
```

### 포트 설정

- 백엔드 API: 8000
- 프론트엔드: 3000
- 방화벽에서 해당 포트 허용 필요

## 주요 기능

### 1. 로그인 제어

- 전체 화면 로그인 창
- 이름 + 소속 입력 필수
- 중복 로그인 방지

### 2. 실시간 모니터링

- 웹 대시보드에서 모든 PC 상태 확인
- 실시간 상태 업데이트
- 활동 로그 확인

### 3. 관리 기능

- 강제 로그아웃
- Slack 알림 설정
- PC 상태 통계

### 4. Slack 연동

- 로그인/로그아웃 알림
- 웹훅 URL 설정
- 실시간 메시지 전송

## 접속 방법

### 관리 대시보드

- 브라우저에서 `http://서버IP:3000` 접속
- 실시간 PC 상태 모니터링
- Slack 설정 및 관리

### API 문서

- `http://서버IP:8000/docs` (Swagger UI)
- `http://서버IP:8000/redoc` (ReDoc)

## 문제 해결

### 클라이언트 연결 문제

1. 서버 IP 주소 확인
2. 방화벽 설정 확인
3. 네트워크 연결 상태 확인

### 로그인 실패

1. 서버 상태 확인
2. 중복 로그인 여부 확인
3. 네트워크 연결 확인

### Docker 관련 문제

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs backend
docker-compose logs frontend

# 재시작
docker-compose restart
```

## 사용 시나리오

### 1. 초기 설정

1. 서버 PC에서 Docker Compose 실행
2. 각 Windows PC에 클라이언트 설치
3. 네트워크 설정 및 IP 주소 구성

### 2. 일반 사용

1. Windows PC에서 클라이언트 실행
2. 로그인 화면에서 이름과 소속 입력
3. 로그인 성공 시 PC 사용 가능

### 3. 관리자 모니터링

1. 웹 브라우저에서 관리 대시보드 접속
2. 실시간 PC 상태 확인
3. 필요시 강제 로그아웃 실행

### 4. Slack 연동

1. 관리 대시보드에서 Slack 설정
2. 웹훅 URL 및 채널 설정
3. 로그인/로그아웃 알림 자동 전송

## 보안 고려사항

- 네트워크 내부에서만 사용 권장
- 방화벽 설정으로 외부 접근 차단
- 관리자 권한으로 클라이언트 실행 권장

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

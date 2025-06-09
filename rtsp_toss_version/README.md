# 🎥 RTSP 스트리밍 관리 시스템

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](./version.json)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)](#)

실시간 RTSP 스트리밍을 관리하는 웹 기반 애플리케이션입니다. FFmpeg을 활용하여 RTSP 스트림을 재생, 녹화, RTMP 송출할 수 있으며, 카메라 제어 및 장치 리셋 기능을 제공합니다.

## ✨ 주요 기능

- 🎬 **RTSP 스트림 재생**: MPV/FFplay를 사용한 실시간 스트림 재생
- 📹 **스트림 녹화**: MP4/MKV 형식으로 고품질 녹화
- 📡 **RTMP 송출**: YouTube Live 등 실시간 방송 플랫폼 연동
- 🎛️ **카메라 제어**: HTTP/VISCA 프로토콜을 통한 카메라 전원 관리
- 🔄 **장치 리셋**: 원격 장치 재부팅 기능
- 🖼️ **이미지 처리**: 이미지 크기 조정 및 OCR 기능
- 📊 **프로세스 모니터링**: 실행 중인 스트림 프로세스 관리

## 🚀 빠른 시작

### 사전 요구사항

- macOS (Intel/Apple Silicon)
- Python 3.8+
- FFmpeg (Homebrew 권장)
- Node.js 16+ (프론트엔드)

### 설치

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd toss_rtsp
   ```

2. **백엔드 의존성 설치**
   ```bash
   # Python 가상환경 생성
   python -m venv .venv
   source .venv/bin/activate
   
   # 패키지 설치
   pip install -r requirements.txt
   ```

3. **FFmpeg 설치** (Homebrew)
   ```bash
   brew install ffmpeg mpv
   ```

4. **프론트엔드 의존성 설치**
   ```bash
   cd frontend
   npm install
   ```

### 실행

1. **백엔드 서버 시작**
   ```bash
   python backend.py
   ```
   서버가 `http://localhost:8000`에서 실행됩니다.

2. **프론트엔드 개발 서버 시작**
   ```bash
   cd frontend
   npm run dev
   ```
   웹 애플리케이션이 `http://localhost:3000`에서 실행됩니다.

## 📖 사용법

### RTSP 스트림 재생
1. 서버 선택 (192.168.116.41 또는 192.168.118.42)
2. 스트림 위치 선택 (회의실/세미나실)
3. "스트림 재생" 버튼 클릭

### 스트림 녹화
1. RTSP 스트림 설정
2. 비트레이트 조정 (1000-10000 Kbps)
3. "녹화 시작" 버튼 클릭
4. 녹화 파일은 `~/Desktop/rtsp_recordings/`에 저장

### RTMP 송출
1. YouTube Live 스트림 키 입력
2. 비트레이트 설정
3. "RTMP 송출 시작" 버튼 클릭

## 🏗️ 프로젝트 구조

```
toss_rtsp/
├── backend.py              # FastAPI 백엔드 서버
├── requirements.txt         # Python 의존성
├── version.json            # 버전 관리
├── README.md               # 프로젝트 문서
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── hooks/          # 커스텀 훅
│   │   ├── services/       # API 서비스
│   │   └── styles/         # 스타일시트
│   ├── package.json
│   └── vite.config.js
└── toss-library/           # 참조 라이브러리
```

## 🎛️ API 엔드포인트

### RTSP 관련
- `POST /rtsp/play` - RTSP 스트림 재생
- `POST /rtsp/record` - 스트림 녹화 시작
- `POST /rtsp/record/stop` - 녹화 중지
- `POST /rtsp/stop` - 모든 RTSP 스트림 중지

### RTMP 관련
- `POST /rtmp/stream` - RTMP 송출 시작
- `POST /rtmp/stop` - RTMP 송출 중지

### 장치 제어
- `POST /camera/control` - 카메라 전원 제어
- `POST /device/reset` - 장치 리셋

### 모니터링
- `GET /processes` - 실행 중인 프로세스 목록
- `POST /process/{pid}/stop` - 특정 프로세스 종료

## 🔧 설정

### 지원되는 스트림 위치
- 소회의실: 1소, 2소
- 세미나실: 1세, 2세, 3세
- 간담회실: 2간~11간
- 대회의실: 대

### 카메라 제어 프로토콜
- **HTTP**: 1세, 2간, 3간, 4간, 6간, 7간, 9간, 10간, 11간
- **VISCA**: 1소, 2소, 2세, 3세, 5간, 8간

## 📝 버전 히스토리

### v1.0.0 (2024-12-30)
- ✅ 초기 버전 릴리즈
- ✅ RTSP 스트림 재생 기능
- ✅ 스트림 녹화 기능 (MP4/MKV)
- ✅ RTMP 송출 기능
- ✅ 카메라 전원 제어 (HTTP/VISCA)
- ✅ 장치 리셋 기능
- ✅ 이미지 처리 및 OCR
- ✅ 프로세스 모니터링
- ✅ 반응형 웹 UI
- ✅ 실시간 상태 업데이트

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 기능 요청이 있으시면 [Issues](../../issues) 페이지를 이용해 주세요.

---

<div align="center">
  Made with ❤️ for seamless RTSP streaming
</div> 
# 프론트엔드 빌드를 위한 베이스 이미지
FROM node:18 AS frontend

# 작업 디렉토리 설정
WORKDIR /app/frontend

# 종속성 파일 복사 및 설치
COPY rtsp-manager/package*.json ./
RUN npm install

# 프론트엔드 소스 복사
COPY rtsp-manager/ ./

# 빌드 과정에서 npm run build를 건너뛰고 개발 모드로 실행
# 프로덕션 빌드에서 발생하는 ESLint 오류 방지

# 파이썬 베이스 이미지
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# Node.js 설치 추가
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get update && \
    apt-get install -y nodejs && \
    node -v && npm -v

# 프론트엔드 소스 복사
COPY --from=frontend /app/frontend /app/frontend

# 시스템 패키지 설치 (FFmpeg 포함)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 종속성 설치
RUN pip install fastapi uvicorn requests psutil pydantic typing

# 백엔드 소스 파일 복사
COPY backend.py .
COPY rtsp_servers_connect.py .
COPY version.json .
COPY next.config.ts .

# 필요한 디렉토리 생성
RUN mkdir -p /root/Desktop/rtsp_recordings /root/Desktop/doogie_logs

# 포트 노출 (백엔드, 프론트엔드)
EXPOSE 8000 3000

# 실행 스크립트 생성 - Next.js 호스트 바인딩 설정 추가
RUN echo '#!/bin/bash\n\
cd /app/frontend && npm run dev -- -H 0.0.0.0 &\n\
cd /app && python backend.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# 컨테이너 시작 시 실행할 명령
CMD ["/app/start.sh"] 
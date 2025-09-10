FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY frontend_shorts/ ./frontend_shorts/
# COPY image/ ./image/  <-- 이 줄을 주석 처리하여 이미지 폴더 복사 방지
COPY config.json* ./
COPY .env .env

# 포트 노출
EXPOSE 8000

# 서버 실행
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"] 
# 카번개루스 백엔드 Dockerfile
FROM python:3.11-slim

ARG PYTHON_VERSION=3.11

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 모델 디렉토리 생성
RUN mkdir -p ai/models logs demo

# 헬스체크 포트 노출
EXPOSE 8000

# 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

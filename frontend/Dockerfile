# Python 3.11 기본 이미지
FROM python:3.11-slim

# 컨테이너 내부 작업 폴더
WORKDIR /app

# Python 패키지 목록 복사
COPY requirements.txt .

# 필요한 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit 코드 복사
COPY frontend/frontend.py .

# 컨테이너 시작 시 Streamlit 실행
CMD ["streamlit", "run", "frontend.py", "--server.address=0.0.0.0", "--server.port=8501"]

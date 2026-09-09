FROM huggingface/transformers-torch-light

# 컨테이너 안에서 작업할 폴더
WORKDIR /app

# 필요한 Python 패키지 목록 복사
COPY requirements.txt .

# requirements.txt에 있는 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# FastAPI 백엔드 코드 복사
COPY backend/backend.py .

COPY models/t5-small /models/t5-small

# FastAPI 서버 실행
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]

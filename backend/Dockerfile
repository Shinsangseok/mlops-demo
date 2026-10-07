FROM huggingface/transformers-torch-light

# 컨테이너 안에서 작업할 폴더
WORKDIR /app

# 필요한 Python 패키지 목록 복사
COPY requirements.txt .

# requirements.txt에 있는 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 실행용 일반 사용자 생성
RUN groupadd -g 10001 appgroup \
    && useradd -m -u 10001 -g appgroup -s /usr/sbin/nologin appuser

# 애플리케이션 파일 복사
COPY --chown=appuser:appgroup backend/backend.py .
COPY --chown=appuser:appgroup models/t5-small /models/t5-small

# root가 아닌 일반 사용자로 실행
USER appuser

# FastAPI 서버 실행
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]

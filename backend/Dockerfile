# FastAPI + sentence-transformers + Tesseract (OCR fallback for scanned PDFs).
# Build from repo: docker build -f backend/Dockerfile backend

FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/data/hf_home

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Match runtime cache path (see app/embeddings.py) so the image cold-starts without re-downloading the model.
RUN mkdir -p /app/data/hf_home \
    && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

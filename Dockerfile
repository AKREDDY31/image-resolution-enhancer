# syntax=docker/dockerfile:1
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade "pip<25" "setuptools<70" "wheel<0.43" && \
    pip install --no-build-isolation basicsr==1.4.2 && \
    pip install -r requirements.txt

COPY . .

ENV LOW_MEMORY_MODE=0 \
    MAX_INPUT_DIM=2048

CMD ["sh", "-c", "streamlit run app.py --server.port ${PORT:-8080} --server.address 0.0.0.0"]

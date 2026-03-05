FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

ENV HF_HOME=/app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache

RUN mkdir -p /app/model_cache

COPY download_models.py /tmp/download_models.py
RUN python /tmp/download_models.py

COPY app/ ./app/

EXPOSE 3001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]
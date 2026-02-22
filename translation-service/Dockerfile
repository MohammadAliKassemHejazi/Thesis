FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# Added libpq-dev for psycopg2 and python3-dev for header files
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Use a timeout for large ML packages like torch and transformers
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt 

# Set environment variables for model caching
ENV HF_HOME=/app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache

# Pre-download models to bake them into the image
RUN python -c " \
from transformers import MarianMTModel, MarianTokenizer; \
models = ['Helsinki-NLP/opus-mt-en-es', 'Helsinki-NLP/opus-mt-en-fr', 'Helsinki-NLP/opus-mt-en-de']; \
for m in models: \
    print(f'Downloading {m}...'); \
    MarianTokenizer.from_pretrained(m); \
    MarianMTModel.from_pretrained(m); \
"

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 3001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]

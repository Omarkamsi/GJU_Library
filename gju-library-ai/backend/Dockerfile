FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY . /app/
RUN pip install --no-cache-dir .
# Install CPU-only torch first to avoid pulling the 2GB CUDA build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
# Now install ML extras — torch is already present so these stay small
RUN pip install --no-cache-dir FlagEmbedding sentence-transformers

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# Run migrations then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8080"]

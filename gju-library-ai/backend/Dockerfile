FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first so FlagEmbedding doesn't pull the 2GB CUDA build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install ML libraries (torch already satisfied above, stays CPU-only)
RUN pip install --no-cache-dir FlagEmbedding sentence-transformers

# Copy pyproject.toml and create stub packages so editable install resolves
COPY pyproject.toml /app/
RUN mkdir -p app ingest && \
    touch app/__init__.py ingest/__init__.py && \
    pip install --no-cache-dir -e .

# Copy full source (overwrites stubs)
COPY . /app/

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8080"]

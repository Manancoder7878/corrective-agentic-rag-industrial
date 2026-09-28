FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FASTEMBED_CACHE_PATH=/app/.cache/fastembed \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml .

RUN uv pip install --system -r pyproject.toml uvicorn

# fastembed weights into the image so runtime doesnot download them
RUN mkdir -p /app/.cache/fastembed /app/.cache/huggingface && \
    python -c "from fastembed import TextEmbedding, SparseTextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5', cache_dir='/app/.cache/fastembed'); SparseTextEmbedding(model_name='Qdrant/bm25', cache_dir='/app/.cache/fastembed')"

COPY src/ ./src/
COPY data/ ./data/
COPY .streamlit/ ./.streamlit/

EXPOSE 8000
EXPOSE 8501

CMD ["uvicorn", "src.api.app:api", "--host", "0.0.0.0", "--port", "8000"]
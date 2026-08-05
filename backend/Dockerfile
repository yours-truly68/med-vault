# -----------------------------------------------------------------------------
# Stage 1: Build dependencies & Python packages (CPU-only)
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libtesseract-dev \
    libleptonica-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Install dependencies using CPU-only PyTorch index to prevent downloading 3GB+ CUDA/NVIDIA packages
RUN pip install --prefix=/install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production Runtime (CPU-only)
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/install/bin:${PATH}" \
    PYTHONPATH="/install/lib/python3.13/site-packages:${PYTHONPATH}"

# Install runtime system dependencies for Tesseract OCR and network checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /install

# Copy application source code
COPY . .

# Create non-root app user
RUN useradd -u 1000 -m appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

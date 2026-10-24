FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files, reports, logs, seeds, demo
COPY app/ app/
COPY seeds/ seeds/
COPY reports/ reports/
COPY logs/ logs/
COPY demo/ demo/

ENV PYTHONUNBUFFERED=1
ENV API_PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=5s --timeout=3s --retries=5 --start_period=10s \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

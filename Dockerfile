FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH="/app"

COPY . /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
        postgresql-client \
        libpq-dev \
        gcc \
        python3-dev \
    && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD alembic upgrade head && uvicorn app:app --host 0.0.0.0 --port 8000

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

RUN chmod +x /app/wait-for-postgres.sh

ENV POSTGRES_HOST=aoe2-postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_USER=aoe2user
ENV POSTGRES_DB=aoe2db

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]



FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH="/app"

COPY . /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN chmod +x /app/wait-for-postgres.sh

ENV POSTGRES_HOST=aoe2-postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_USER=aoe2user
ENV POSTGRES_DB=aoe2db

CMD ["sh", "-c", "./wait-for-postgres.sh && python app.py"]

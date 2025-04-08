# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . /app
RUN ls /app/mgz_hd

# Install PostgreSQL client, upgrade pip, and install Python dependencies
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Make the wait script executable
RUN chmod +x /app/wait-for-postgres.sh

# Set environment variables for pg_isready (optional)
ENV POSTGRES_HOST=aoe2-postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_USER=aoe2user
ENV POSTGRES_DB=aoe2db

# Run DB migration before starting the app
CMD ["sh", "-c", "./wait-for-postgres.sh && flask db upgrade && python app.py"]

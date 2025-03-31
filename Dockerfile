# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Install PostgreSQL client, upgrade pip, and install Python dependencies
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Make the wait script executable
RUN chmod +x /app/wait-for-postgres.sh

# Set environment variables for pg_isready (optional but cleaner)
ENV POSTGRES_HOST=aoe2-postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_USER=aoe2user
ENV POSTGRES_DB=aoe2db

# Start the app using wait-for-postgres
CMD ["./wait-for-postgres.sh"]

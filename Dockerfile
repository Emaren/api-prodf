# Dockerfile

FROM python:3.12-slim

# Install git early to support submodule fetch
RUN apt-get update && \
    apt-get install -y git

# Set the working directory
WORKDIR /app

# Copy entire repo including .git to allow submodule updates
COPY . /app

# Add app to PYTHONPATH so submodules can be imported
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Initialize git submodules (requires .git to exist in the build context)
RUN git submodule update --init --recursive

# Optional debug: confirm mgz_hd contents
RUN ls /app/mgz_hd

# Install PostgreSQL client, upgrade pip, and install dependencies
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Make the wait script executable
RUN chmod +x /app/wait-for-postgres.sh

# Environment variables (used optionally by wait-for-postgres.sh)
ENV POSTGRES_HOST=aoe2-postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_USER=aoe2user
ENV POSTGRES_DB=aoe2db

# Run the app with DB migration
CMD ["sh", "-c", "./wait-for-postgres.sh && flask db upgrade && python app.py"]

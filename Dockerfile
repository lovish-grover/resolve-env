FROM python:3.10-slim

WORKDIR /app

# Install curl for the healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your environment files
COPY . /app/

# OpenEnv strict networking requirements
EXPOSE 8000
ENV PYTHONPATH="/app"

# OpenEnv mandatory healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI server using the app.py we built earlier
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
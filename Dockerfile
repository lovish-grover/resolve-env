FROM public.ecr.aws/docker/library/python:3.10-slim

WORKDIR /app

# Install curl for the healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your environment files
COPY . /app/

# OpenEnv strict networking requirements
EXPOSE 7860
ENV PYTHONPATH="/app"

# Native Python healthcheck (bypasses the need for curl)
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
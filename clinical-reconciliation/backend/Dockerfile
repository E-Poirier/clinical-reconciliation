# Phase 5: Backend Dockerfile
# Base: python:3.11-slim per PLAN.md
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY src/ src/

# Expose port 8000
EXPOSE 8000

# Run uvicorn (no reload in production container)
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]

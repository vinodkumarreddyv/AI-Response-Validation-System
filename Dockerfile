# Multi-stage Dockerfile for AI Response Validation System
# Stage 1: Build React Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Copy built frontend from Stage 1 into backend app dist
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Download vector store if missing
RUN python scripts/download_vector_store.py || true

# Default port: 7860 (Hugging Face Spaces default) or dynamic via $PORT
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]

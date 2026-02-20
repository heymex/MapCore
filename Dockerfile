# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

# ----- Stage 1: Build frontend -----
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ----- Stage 2: Runtime -----
FROM python:3.12-slim
WORKDIR /app

# Install Python deps
COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY server/ ./server/

# Copy built frontend
COPY --from=frontend-build /build/dist ./frontend/dist

# Expose port
EXPOSE 8001

# Run with uvicorn
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8001"]

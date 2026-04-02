# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# Output goes to ../backend/static via vite.config.ts outDir

# Stage 2: Runtime
FROM python:3.12-slim

# Install WireGuard tools and system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    wireguard-tools \
    iptables \
    iproute2 \
    procps \
    conntrack \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Copy built frontend (placed in backend/static by vite build)
COPY --from=frontend-build /app/backend/static ./static

# Copy entrypoint
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create data and certs directories
RUN mkdir -p /app/data /etc/wireguard /app/certs

EXPOSE 7777 7778

ENTRYPOINT ["/entrypoint.sh"]

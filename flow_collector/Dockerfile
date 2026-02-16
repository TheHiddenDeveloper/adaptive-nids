# Multi-stage build for minimal image size
FROM python:3.11-slim AS builder

# Install build dependencies for NFStream (libpcap headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with compiler flags for Arch compatibility
WORKDIR /app
COPY flow_collector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Install runtime libpcap (no dev headers needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap1 \
    && rm -rf /var/lib/apt/lists/*

# Copy built dependencies
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
WORKDIR /app
COPY flow_collector/ .
COPY shared/ ../shared/

# Create non-root user (security best practice)
RUN useradd -m -u 1000 nidsuser && \
    chown -R nidsuser:nidsuser /app

USER nidsuser

# Expose metrics port
EXPOSE 9090

# Critical: Run with --network=host in production for packet capture
# Example: docker run --network=host --cap-add=NET_RAW --cap-add=NET_ADMIN nids-collector
ENTRYPOINT ["python", "main.py"]
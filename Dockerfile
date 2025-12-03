# Multi-stage build for optimized image size


# Stage 1: Base Image with Python and System Dependencies
FROM python:3.9-slim-bullseye as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # MQTT Broker
    mosquitto \
    mosquitto-clients \
    # mDNS/Avahi
    avahi-daemon \
    avahi-utils \
    dbus \
    # I2C tools for sensors
    i2c-tools \
    # Python development
    gcc \
    python3-dev \
    # Network tools (for debugging)
    iputils-ping \
    net-tools \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Stage 2: Python Dependencies
FROM base as dependencies

# Create app directory
WORKDIR /app
# Copy requirements file
COPY requirements.txt .
# Install Python packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# Stage 3: Final Application Image
FROM base as final

# Copy Python packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Create app directory
WORKDIR /app

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs /app/models

# Copy application code
COPY *.py ./
COPY sensors/ ./sensors/

# Copy models (if they exist)
COPY *.pkl ./models/ 2>/dev/null || true

# Copy configuration files
COPY mosquitto.conf /etc/mosquitto/conf.d/custom.conf
COPY avahi-daemon.conf /etc/avahi/avahi-daemon.conf 2>/dev/null || true

# Set permissions
RUN chmod +x *.py

# Expose ports
EXPOSE 1883   
EXPOSE 5353/udp   

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD mosquitto_sub -h localhost -t 'health/heartbeat' -C 1 -W 5 || exit 1
# HEALTHCHECK --interval=6m --timeout=10s --start-period=1m --retries=3 \
#     CMD mosquitto_sub -h localhost -t 'health/heartbeat' -C 1 -W 360 || exit 1



# Create startup script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["python3", "inferenceEngine.py"]
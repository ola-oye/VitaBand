# Multi-stage build for optimized image size


# Stage 1: Base Image with Python and System Dependencies
FROM python:3.12-slim-bullseye as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    # MQTT Broker
    mosquitto \
    mosquitto-clients \
    # mDNS/Avahi
    avahi-daemon \
    avahi-utils \
    dbus \
    libnss-mdns \
    # I2C tools for sensors
    i2c-tools \
    # Python development
    gcc \
    python3-dev \
    # Network tools (for debugging)
    iputils-ping \
    net-tools \
    iproute2 \
    # Process management tools
    procps \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Stage 2: Python Dependencies
FROM base as dependencies

# Create tmp_install directory
WORKDIR /tmp_install
# Copy requirements file
COPY requirements.txt .
# Install Python packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# Stage 3: Final Application Image
FROM base as final

# Copy Python packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Create app directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/data \
             /app/logs \
             /app/output \
             /app/model \
             /app/config \
             /var/run/dbus \
             /var/run/avahi-daemon \
             /var/lib/mosquitto \
             /etc/mosquitto/conf.d
# Copy application code
COPY app/ ./app/
COPY model/ ./model/
COPY sensors/ ./sensors/
COPY config/ ./config/
# Copy requirements file for reference
COPY requirements.txt .

# Copy configuration files
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY mosquitto.conf /etc/mosquitto/conf.d/custom.conf
COPY avahi-daemon.conf /etc/avahi/avahi-daemon.conf
COPY mqtt.service /etc/avahi/services/mqtt.service


# Set permissions
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    chmod 644 /etc/mosquitto/conf.d/custom.conf && \
    chmod 644 /etc/avahi/avahi-daemon.conf && \
    chmod 644 /etc/avahi/services/mqtt.service && \
    chown -R mosquitto:mosquitto /var/lib/mosquitto && \
    mkdir -p /var/log/mosquitto && \
    chown mosquitto:mosquitto /var/log/mosquitto

# Expose ports
EXPOSE 1883
EXPOSE 8883
EXPOSE 9001
EXPOSE 5353/udp   

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD mosquitto_sub -h localhost -t 'health/heartbeat' -C 1 -W 5 || exit 1
# HEALTHCHECK --interval=6m --timeout=10s --start-period=1m --retries=3 \
#     CMD mosquitto_sub -h localhost -t 'health/heartbeat' -C 1 -W 360 || exit 1


# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["python3", "app/inferenceEngine.py"]
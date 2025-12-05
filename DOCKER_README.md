# VitaBand Health Monitoring System - Docker Guide

Complete guide for running the VitaBand health monitoring system in Docker containers.

---

## 📦 What's Included

The Docker container includes:
- ✅ Python 3.9 runtime
- ✅ Mosquitto MQTT broker
- ✅ Avahi mDNS daemon
- ✅ All Python dependencies
- ✅ I2C support for sensors
- ✅ Health monitoring application

---

## 🚀 Quick Start

### Method 1: Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Method 2: Using Shell Scripts

```bash
# Make scripts executable
chmod +x build.sh run.sh

# Build image
./build.sh

# Run container
./run.sh

# View logs
docker logs -f vitaband
```

### Method 3: Manual Docker Commands

```bash
# Build
docker build -t vitaband:latest .

# Run
docker run -d \
  --name vitaband \
  --hostname vitaband \
  --network host \
  --privileged \
  --device /dev/i2c-1:/dev/i2c-1 \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/models:/app/models \
  vitaband:latest
```

---

## 📁 Project Structure

project/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-entrypoint.sh
│   ├── mosquitto.conf
│   ├── avahi-daemon.conf
│   ├── mqtt.service
│   ├── build.sh
│   └── run.sh
├── app/
│   ├── inferenceEngine.py
│   ├── mqtt_publisher.py
│   ├── sensor_manager.py
│   └── sensors/
├── models/
│   ├── rf_model.pkl
│   └── scaler.pkl
└── config/
    └── mqtt_config.py
```

---

## 🔧 Configuration

### Environment Variables

Set in `docker-compose.yml` or pass with `-e`:

```yaml
environment:
  - MQTT_BROKER=localhost      # MQTT broker address
  - MQTT_PORT=1883            # MQTT port
  - LOG_LEVEL=INFO            # Logging level
  - PYTHONUNBUFFERED=1        # Python output buffering
```

### Volumes (Persistent Data)

```yaml
volumes:
  - ./data:/app/data          # Application data
  - ./logs:/app/logs          # Log files
  - ./model:/app/model      # ML models
  - ./output:/app/output      # CSV outputs
```

### Ports

```yaml
ports:
  - "1883:1883"               # MQTT
  - "5353:5353/udp"          # mDNS
```

**Note:** Using `network_mode: host` for mDNS requires host network.

---

## 🛠️ Common Commands

### Building

```bash
# Build with custom tag
docker build -t vitaband:v1.0 .

# Build without cache
docker build --no-cache -t vitaband:latest .

# Build for different platform (e.g., Raspberry Pi ARM)
docker buildx build --platform linux/arm/v7 -t vitaband:latest .
```

### Running

```bash
# Start container
docker-compose up -d

# Start and view logs
docker-compose up

# Restart container
docker-compose restart

# Stop container
docker-compose stop

# Stop and remove
docker-compose down
```

### Monitoring

```bash
# View logs (follow)
docker logs -f vitaband

# View last 100 lines
docker logs --tail 100 vitaband

# Check container status
docker ps

# Check resource usage
docker stats vitaband

# Health check
docker inspect --format='{{.State.Health.Status}}' vitaband
```

### Debugging

```bash
# Access container shell
docker exec -it vitaband bash

# Run specific command in container
docker exec vitaband python3 test_sensors.py

# Check MQTT broker
docker exec vitaband mosquitto_sub -h localhost -t 'health/#' -C 5

# Check Avahi
docker exec vitaband avahi-browse -a -t
```

---

## 🔍 Troubleshooting

### Issue 1: Container Won't Start

**Check logs:**
```bash
docker logs vitaband
```

**Common causes:**
- I2C device not available: Remove `--device /dev/i2c-1` if no sensors
- Port conflict: Check if port 1883 is in use
- Permission issues: Ensure user has Docker permissions

### Issue 2: MQTT Not Working

**Test MQTT inside container:**
```bash
docker exec vitaband mosquitto_sub -h localhost -t '$SYS/#' -C 5
```

**Check Mosquitto config:**
```bash
docker exec vitaband cat /etc/mosquitto/conf.d/custom.conf
```

### Issue 3: mDNS Not Advertising

**Check Avahi status:**
```bash
docker exec vitaband pgrep -a avahi
```

**Note:** mDNS requires `--network host` mode.

### Issue 4: Sensors Not Detected

**Check I2C devices:**
```bash
docker exec vitaband i2cdetect -y 1
```

**Ensure privileged mode:**
```yaml
privileged: true
devices:
  - /dev/i2c-1:/dev/i2c-1
```

### Issue 5: Permission Denied Errors

```bash
# On host, ensure user is in docker group
sudo usermod -aG docker $USER

# Re-login or restart
newgrp docker
```

---

## 🚀 Deployment Scenarios

### Development (Laptop)

```yaml
# docker-compose.yml
services:
  vitaband:
    build: .
    volumes:
      # Mount code for live updates
      - ./src:/app/src
      - ./*.py:/app/
    environment:
      - LOG_LEVEL=DEBUG
```

### Production (Raspberry Pi)

```yaml
# docker-compose.yml
services:
  vitaband:
    image: vitaband:latest
    restart: always
    privileged: true
    devices:
      - /dev/i2c-1:/dev/i2c-1
    network_mode: host
```

### Cloud Deployment

```yaml
# Use external MQTT broker
environment:
  - MQTT_BROKER=mqtt.example.com
  - MQTT_PORT=1883
  
# Remove sensor device access
# devices: []
```

---

## 📊 Monitoring & Logs

### Log Locations

```
Container:
  /app/logs/              # Application logs
  /var/log/mosquitto/     # MQTT logs
  
Host (mounted):
  ./logs/                 # Application logs
```

### Health Checks

Docker automatically runs health checks every 30 seconds:

```bash
# Check health status
docker inspect vitaband | grep -A 10 Health

# View health check logs
docker inspect vitaband | jq '.[0].State.Health'
```

---

## 🔄 Updates & Maintenance

### Update Application Code

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Update Dependencies

```bash
# Edit requirements.txt
nano requirements.txt

# Rebuild image
docker-compose build --no-cache

# Restart
docker-compose up -d
```

### Backup Data

```bash
# Backup volumes
docker run --rm \
  -v vitaband_mosquitto-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/mosquitto-backup.tar.gz -C /data .
```

### Clean Up

```bash
# Remove stopped containers
docker-compose down

# Remove volumes (WARNING: deletes data!)
docker-compose down -v

# Remove images
docker rmi vitaband:latest

# Clean everything
docker system prune -a
```

---

## 🎯 Best Practices

1. **Use Docker Compose** for easier management
2. **Mount volumes** for data persistence
3. **Set restart policy** for automatic recovery
4. **Monitor logs** regularly
5. **Use health checks** for monitoring
6. **Tag images** with versions
7. **Keep Dockerfile** simple and documented
8. **Use .dockerignore** to reduce image size
9. **Test locally** before deploying
10. **Backup volumes** regularly

---

## 📝 Quick Reference

| Task | Command |
|------|---------|
| **Build** | `docker-compose build` |
| **Start** | `docker-compose up -d` |
| **Stop** | `docker-compose stop` |
| **Logs** | `docker-compose logs -f` |
| **Shell** | `docker exec -it vitaband bash` |
| **Restart** | `docker-compose restart` |
| **Status** | `docker-compose ps` |
| **Remove** | `docker-compose down` |

---

## 🆘 Getting Help

**Check logs:**
```bash
docker-compose logs -f vitaband
```

**Access shell:**
```bash
docker exec -it vitaband bash
```

**Test components:**
```bash
# MQTT
docker exec vitaband mosquitto_sub -h localhost -t 'health/#' -v

# Python
docker exec vitaband python3 -c "import paho.mqtt.client; print('MQTT OK')"

# Sensors
docker exec vitaband python3 test_sensors.py
```

---

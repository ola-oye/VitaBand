#!/bin/bash
# Run script for VitaBand Docker container

set -e

echo "Starting VitaBand Container"

# Configuration
CONTAINER_NAME="vitaband"
IMAGE_NAME="vitaband:latest"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if image exists
if ! docker images ${IMAGE_NAME} | grep -q health-monitor; then
    echo "${RED}Error: Docker image not found!${NC}"
    echo "Build the image first with: ./build.sh"
    exit 1
fi

# Stop and remove existing container if running
if docker ps -a | grep -q ${CONTAINER_NAME}; then
    echo "${YELLOW}Stopping existing container...${NC}"
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
fi

# Create required directories
echo "Creating directories..."
mkdir -p data logs models output

# Run the container
echo ""
echo "${YELLOW}Starting container: ${CONTAINER_NAME}${NC}"
echo ""

docker run -d \
    --name ${CONTAINER_NAME} \
    --hostname vitaband \
    --network host \
    --privileged \
    --device /dev/i2c-1:/dev/i2c-1 \
    --restart unless-stopped \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/models:/app/models \
    -v $(pwd)/output:/app/output \
    -e PYTHONUNBUFFERED=1 \
    -e MQTT_BROKER=localhost \
    ${IMAGE_NAME}

# Check if container started
sleep 2

if docker ps | grep -q ${CONTAINER_NAME}; then
    echo ""
    echo "${GREEN}--------------------------------------------------"
    echo "Container started successfully!"
    echo "--------------------------------------------------${NC}"
    echo ""
    echo "Container status:"
    docker ps --filter name=${CONTAINER_NAME}
    echo ""
    echo "View logs:"
    echo "  docker logs -f ${CONTAINER_NAME}"
    echo ""
    echo "Stop container:"
    echo "  docker stop ${CONTAINER_NAME}"
    echo ""
    echo "Access shell:"
    echo "  docker exec -it ${CONTAINER_NAME} bash"
else
    echo ""
    echo "${RED}Container failed to start!${NC}"
    echo "Check logs with: docker logs ${CONTAINER_NAME}"
    exit 1
fi
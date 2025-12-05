#!/bin/bash
# Build script for VitaBand Docker image

set -e

echo "Building VitaBand Docker Image"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="vitaband"
IMAGE_TAG="latest"

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "Error: Dockerfile not found!"
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "Warning: requirements.txt not found!"
fi

# Build the image
echo ""
echo "${YELLOW}Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
echo ""

docker build \
    --tag ${IMAGE_NAME}:${IMAGE_TAG} \
    --tag ${IMAGE_NAME}:$(date +%Y%m%d) \
    --progress=plain \
    .

# Check build status
if [ $? -eq 0 ]; then
    echo ""
    echo "${GREEN}------------------------------------------"
    echo "Build completed successfully!"
    echo "------------------------------------------${NC}"
    echo ""
    echo "Image details:"
    docker images ${IMAGE_NAME}
    echo ""
    echo "To run the container:"
    echo "  ./run.sh"
    echo ""
    echo "Or with docker-compose:"
    echo "  docker-compose up -d"
else
    echo ""
    echo "Build failed!"
    exit 1
fi
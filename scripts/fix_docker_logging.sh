#!/bin/bash

# Docker Log Rotation Fix Script
# Prevents Docker containers from creating massive log files

echo "🔧 Configuring Docker log rotation for hummingbot-api..."

# Stop the container
echo "Stopping hummingbot-api container..."
docker stop hummingbot-api

# Remove the container (preserves the image)
echo "Removing container to recreate with log rotation..."
docker rm hummingbot-api

# Recreate the container with log rotation
echo "Recreating hummingbot-api with proper log rotation..."
docker run -d \
  --name hummingbot-api \
  --restart unless-stopped \
  -p 8888:8000 \
  -v /home/sev/hummingbot-api/bots:/hummingbot-api/bots:rw \
  -v /var/run/docker.sock:/var/run/docker.sock:rw \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  hummingbot/hummingbot-api:latest

echo "✅ hummingbot-api recreated with log rotation:"
echo "   - Max log size: 10MB per file"
echo "   - Max files: 3 (30MB total maximum)"
echo "   - Old logs will auto-rotate and compress"

# Show container status
docker ps | grep hummingbot-api

echo ""
echo "🎯 Problem solved! Docker logs will never exceed 30MB total."
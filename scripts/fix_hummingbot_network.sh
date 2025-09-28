#!/bin/bash

# Fix hummingbot-api container network connectivity
echo "🔧 Fixing hummingbot-api network connectivity..."

# Recreate the container with proper network connection
echo "Recreating hummingbot-api with correct network..."
docker run -d \
  --name hummingbot-api \
  --restart unless-stopped \
  --network hummingbot-api_emqx-bridge \
  -p 8888:8000 \
  -v /home/sev/hummingbot-api/bots:/hummingbot-api/bots:rw \
  -v /var/run/docker.sock:/var/run/docker.sock:rw \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  hummingbot/hummingbot-api:latest

echo "✅ hummingbot-api recreated with:"
echo "   - Proper network connectivity to postgres"
echo "   - Log rotation configured (10MB × 3 files)"
echo "   - Auto-restart enabled"

# Wait a moment and check status
sleep 5
echo ""
echo "Container status:"
docker ps | grep hummingbot-api

echo ""
echo "Checking logs for successful startup:"
docker logs --tail 10 hummingbot-api
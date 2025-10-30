#!/bin/bash
SERVICE_KEY=$(grep SUPABASE_SERVICE_KEY /home/sev/ggbot/.env | cut -d'=' -f2 | tr -d '"')

curl -s -X GET "http://localhost:8000/api/v2/agent/account/d13d5536-2498-4f27-b2bc-e4f98958e1d8?user_id=00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer $SERVICE_KEY" \
  -H "X-Service-Auth: agent-runner" \
  -H "Content-Type: application/json"

#!/bin/bash
# Daily data refresh cron job
# Add to crontab: 0 6 * * * /path/to/daily_refresh.sh >> /var/log/chartora/refresh.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_DIR"

echo "[$(date -Iseconds)] Starting daily data refresh..."

# Run the refresh orchestrator via Docker
docker compose -f infra/docker-compose.prod.yml exec -T backend \
    python -m scripts.refresh_data

echo "[$(date -Iseconds)] Daily data refresh complete."

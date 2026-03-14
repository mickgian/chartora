#!/bin/bash
# PostgreSQL backup script
# Add to crontab: 0 2 * * * /path/to/backup_db.sh >> /var/log/chartora/backup.log 2>&1
#
# Prerequisites:
#   - s3cmd configured for Hetzner Object Storage
#   - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB set in environment or .env

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_DIR="/tmp/chartora-backups"
RETENTION_DAYS=30

# Load env vars if .env exists
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$PROJECT_DIR/.env"
    set +a
fi

DB_USER="${POSTGRES_USER:-chartora}"
DB_NAME="${POSTGRES_DB:-chartora}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="chartora_${TIMESTAMP}.sql.gz"

echo "[$(date -Iseconds)] Starting database backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Dump database via Docker and compress
docker compose -f "$PROJECT_DIR/infra/docker-compose.prod.yml" exec -T db \
    pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
echo "[$(date -Iseconds)] Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Upload to Hetzner Object Storage (using s3cmd)
if command -v s3cmd &> /dev/null; then
    s3cmd put "$BACKUP_DIR/$BACKUP_FILE" "s3://chartora-backups/$BACKUP_FILE"
    echo "[$(date -Iseconds)] Backup uploaded to object storage"
else
    echo "[$(date -Iseconds)] WARNING: s3cmd not found, backup stored locally only"
fi

# Clean up old local backups
find "$BACKUP_DIR" -name "chartora_*.sql.gz" -mtime "+$RETENTION_DAYS" -delete
echo "[$(date -Iseconds)] Cleaned up backups older than $RETENTION_DAYS days"

echo "[$(date -Iseconds)] Database backup complete."

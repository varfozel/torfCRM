#!/usr/bin/env bash
set -eo pipefail

# Directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
else
    echo "Error: .env file not found in $PROJECT_ROOT"
    exit 1
fi

BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="peat_crm_backup_${TIMESTAMP}.dump"
BACKUP_FILEPATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

mkdir -p "$BACKUP_DIR"

echo "=== Creating PostgreSQL Database Backup ==="
echo "Target file: $BACKUP_FILEPATH"

# Perform pg_dump inside the private container
docker exec -t peat_crm_db pg_dump -U "${POSTGRES_USER:-peat_user}" \
    -d "${POSTGRES_DB:-peat_crm}" \
    -F c \
    -b \
    -v > "$BACKUP_FILEPATH"

echo "=== Backup completed successfully! Size: $(du -sh "$BACKUP_FILEPATH" | cut -f1) ==="

# Optional: Keep only the last 14 days of backups
find "$BACKUP_DIR" -name "peat_crm_backup_*.dump" -mtime +14 -delete
echo "Retention check completed (backups older than 14 days pruned)."

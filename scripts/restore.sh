#!/usr/bin/env bash
set -eo pipefail

if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_backup_file.dump>"
    echo "Example: $0 ./backups/peat_crm_backup_20261004_120000.dump"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' does not exist."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
else
    echo "Error: .env file not found in $PROJECT_ROOT"
    exit 1
fi

echo "=========================================================="
echo "WARNING: Restoring will overwrite existing database data!"
echo "Database: ${POSTGRES_DB:-peat_crm}"
echo "Backup File: $BACKUP_FILE"
echo "=========================================================="
read -p "Are you sure you want to proceed with restore? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo "=== Terminating existing database connections ==="
docker exec -i peat_crm_db psql -U "${POSTGRES_USER:-peat_user}" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB:-peat_crm}' AND pid <> pg_backend_pid();"

echo "=== Restoring database from dump ==="
docker exec -i peat_crm_db pg_restore -U "${POSTGRES_USER:-peat_user}" \
    -d "${POSTGRES_DB:-peat_crm}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    -v < "$BACKUP_FILE"

echo "=== Database restore completed successfully! ==="

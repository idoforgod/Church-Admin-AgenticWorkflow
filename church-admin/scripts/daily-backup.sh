#!/usr/bin/env bash
# daily-backup.sh — Church Administration Data Backup Script
#
# Creates a timestamped, compressed backup of all data/ files.
# Sensitive files (members, finance, newcomers) are included in the backup
# but NOT committed to git (see .gitignore).
#
# Usage:
#   ./scripts/daily-backup.sh
#
# Cron example (daily at 2:00 AM):
#   0 2 * * * cd /path/to/church-admin && ./scripts/daily-backup.sh >> backups/backup.log 2>&1
#
# Retention: Backups older than 30 days are automatically removed.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_BASE_DIR="${PROJECT_DIR}/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_BASE_DIR}/${TIMESTAMP}"
ARCHIVE_NAME="church-admin-backup-${TIMESTAMP}.tar.gz"
RETENTION_DAYS=30

echo "=== Church Admin Backup — ${TIMESTAMP} ==="
echo "Project directory: ${PROJECT_DIR}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Copy data files
echo "Copying data files..."
cp -r "${PROJECT_DIR}/data/" "${BACKUP_DIR}/data/"

# Copy state.yaml (SOT)
echo "Copying state.yaml..."
cp "${PROJECT_DIR}/state.yaml" "${BACKUP_DIR}/state.yaml"

# Create compressed archive
echo "Creating archive: ${ARCHIVE_NAME}"
cd "${BACKUP_BASE_DIR}"
tar -czf "${ARCHIVE_NAME}" "${TIMESTAMP}/"

# Remove uncompressed backup directory
rm -rf "${BACKUP_DIR}"

# Report archive size
ARCHIVE_SIZE=$(du -sh "${BACKUP_BASE_DIR}/${ARCHIVE_NAME}" | cut -f1)
echo "Archive created: ${ARCHIVE_NAME} (${ARCHIVE_SIZE})"

# Cleanup old backups (retention policy)
echo "Removing backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_BASE_DIR}" -name "church-admin-backup-*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

# Count remaining backups
BACKUP_COUNT=$(find "${BACKUP_BASE_DIR}" -name "church-admin-backup-*.tar.gz" | wc -l | tr -d ' ')
echo "Total backups on disk: ${BACKUP_COUNT}"

echo "=== Backup complete ==="

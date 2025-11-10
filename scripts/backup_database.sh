#!/bin/bash
#
# Database Backup Script for TutorMax
#
# This script creates a backup of the PostgreSQL database using pg_dump.
# Backups are timestamped and can be stored locally or uploaded to cloud storage.
#
# Usage:
#   ./scripts/backup_database.sh [output_directory]
#
# Environment Variables (optional, defaults to .env):
#   POSTGRES_HOST
#   POSTGRES_PORT
#   POSTGRES_USER
#   POSTGRES_PASSWORD
#   POSTGRES_DB
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TutorMax Database Backup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Load environment variables from .env if exists
if [ -f .env ]; then
    echo -e "${BLUE}Loading environment from .env...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-tutormax}
POSTGRES_DB=${POSTGRES_DB:-tutormax}
BACKUP_DIR=${1:-./backups}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/tutormax_backup_${TIMESTAMP}.dump"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo -e "${BLUE}Backup Configuration:${NC}"
echo "  Host: ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "  Database: ${POSTGRES_DB}"
echo "  User: ${POSTGRES_USER}"
echo "  Output: ${BACKUP_FILE}"
echo ""

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    echo -e "${RED}ERROR: pg_dump not found${NC}"
    echo "Please install PostgreSQL client tools:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql-client"
    echo "  macOS: brew install postgresql"
    exit 1
fi

# Test database connection
echo -e "${BLUE}Testing database connection...${NC}"
if ! PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Cannot connect to database${NC}"
    echo "Please check your database credentials and connectivity."
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"
echo ""

# Create backup
echo -e "${BLUE}Creating backup...${NC}"
PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
    -h $POSTGRES_HOST \
    -p $POSTGRES_PORT \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    -F c \
    -f "$BACKUP_FILE" \
    --verbose

echo ""
echo -e "${GREEN}✓ Backup completed successfully!${NC}"
echo ""

# Get backup file size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${BLUE}Backup Details:${NC}"
echo "  File: ${BACKUP_FILE}"
echo "  Size: ${BACKUP_SIZE}"
echo "  Timestamp: ${TIMESTAMP}"
echo ""

# Optional: Compress backup
read -p "Compress backup with gzip? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Compressing backup...${NC}"
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    COMPRESSED_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup compressed${NC}"
    echo "  Compressed file: ${BACKUP_FILE}"
    echo "  Compressed size: ${COMPRESSED_SIZE}"
    echo ""
fi

# Optional: Clean old backups
read -p "Clean backups older than 30 days? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Cleaning old backups...${NC}"
    find "$BACKUP_DIR" -name "tutormax_backup_*.dump*" -type f -mtime +30 -delete
    echo -e "${GREEN}✓ Old backups cleaned${NC}"
    echo ""
fi

# List all backups
echo -e "${BLUE}Available backups:${NC}"
ls -lh "$BACKUP_DIR"/tutormax_backup_* 2>/dev/null || echo "  (no backups found)"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To restore this backup:"
echo "  ./scripts/restore_database.sh ${BACKUP_FILE}"
echo ""

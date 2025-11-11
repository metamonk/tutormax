#!/bin/bash
#
# Database Restore Script for TutorMax
#
# This script restores a PostgreSQL database from a pg_dump backup file.
#
# Usage:
#   ./scripts/restore_database.sh <backup_file>
#
# Environment Variables (optional, defaults to .env):
#   POSTGRES_HOST
#   POSTGRES_PORT
#   POSTGRES_USER
#   POSTGRES_PASSWORD
#   POSTGRES_DB
#
# WARNING: This will drop and recreate the database!
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}========================================${NC}"
echo -e "${RED}TutorMax Database Restore${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: No backup file specified${NC}"
    echo ""
    echo "Usage:"
    echo "  ./scripts/restore_database.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh backups/tutormax_backup_* 2>/dev/null || echo "  (no backups found)"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}ERROR: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

# Decompress if needed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo -e "${BLUE}Decompressing backup...${NC}"
    DECOMPRESSED_FILE="${BACKUP_FILE%.gz}"
    gunzip -k "$BACKUP_FILE"
    BACKUP_FILE="$DECOMPRESSED_FILE"
    echo -e "${GREEN}✓ Backup decompressed${NC}"
    echo ""
fi

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

echo -e "${BLUE}Restore Configuration:${NC}"
echo "  Host: ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "  Database: ${POSTGRES_DB}"
echo "  User: ${POSTGRES_USER}"
echo "  Backup file: ${BACKUP_FILE}"
echo ""

# Check if pg_restore is available
if ! command -v pg_restore &> /dev/null; then
    echo -e "${RED}ERROR: pg_restore not found${NC}"
    echo "Please install PostgreSQL client tools:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql-client"
    echo "  macOS: brew install postgresql"
    exit 1
fi

# Test database connection
echo -e "${BLUE}Testing database connection...${NC}"
if ! PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Cannot connect to database${NC}"
    echo "Please check your database credentials and connectivity."
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"
echo ""

# WARNING
echo -e "${RED}WARNING: This will DROP and RECREATE the database!${NC}"
echo -e "${RED}All existing data will be LOST!${NC}"
echo ""
read -p "Are you absolutely sure you want to continue? (type 'yes' to confirm): " -r
echo
if [[ ! $REPLY == "yes" ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Create backup of current database (if exists)
echo -e "${BLUE}Creating safety backup of current database...${NC}"
SAFETY_BACKUP="./backups/pre_restore_safety_backup_$(date +%Y%m%d_%H%M%S).dump"
mkdir -p ./backups
PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
    -h $POSTGRES_HOST \
    -p $POSTGRES_PORT \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    -F c \
    -f "$SAFETY_BACKUP" 2>/dev/null || echo "No existing database to backup"
echo -e "${GREEN}✓ Safety backup created: ${SAFETY_BACKUP}${NC}"
echo ""

# Terminate existing connections to the database
echo -e "${BLUE}Terminating existing database connections...${NC}"
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d postgres <<EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();
EOF
echo -e "${GREEN}✓ Connections terminated${NC}"
echo ""

# Drop and recreate database
echo -e "${BLUE}Dropping and recreating database...${NC}"
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d postgres <<EOF
DROP DATABASE IF EXISTS ${POSTGRES_DB};
CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};
EOF
echo -e "${GREEN}✓ Database recreated${NC}"
echo ""

# Restore from backup
echo -e "${BLUE}Restoring from backup...${NC}"
PGPASSWORD=$POSTGRES_PASSWORD pg_restore \
    -h $POSTGRES_HOST \
    -p $POSTGRES_PORT \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    --verbose \
    --no-owner \
    --no-acl \
    "$BACKUP_FILE"

echo ""
echo -e "${GREEN}✓ Database restored successfully!${NC}"
echo ""

# Run database migrations to ensure schema is up to date
echo -e "${BLUE}Running database migrations...${NC}"
if command -v alembic &> /dev/null; then
    alembic upgrade head
    echo -e "${GREEN}✓ Migrations applied${NC}"
else
    echo -e "${YELLOW}⚠ Alembic not found. Skipping migrations.${NC}"
fi
echo ""

# Verify restore
echo -e "${BLUE}Verifying restore...${NC}"
TABLE_COUNT=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
echo "  Tables restored: ${TABLE_COUNT}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Restore completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Safety backup saved at: ${SAFETY_BACKUP}"
echo ""

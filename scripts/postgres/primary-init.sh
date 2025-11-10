#!/bin/bash
#
# PostgreSQL Primary Server Initialization
# Sets up replication user and configuration
#

set -e

echo "Configuring PostgreSQL primary for replication..."

# Create replication user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create replication user
    CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_pass';

    -- Grant necessary permissions
    GRANT CONNECT ON DATABASE $POSTGRES_DB TO replicator;

    -- Enable pg_stat_statements extension
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

    -- Create monitoring views
    CREATE OR REPLACE VIEW replication_status AS
    SELECT
        client_addr,
        state,
        sent_lsn,
        write_lsn,
        flush_lsn,
        replay_lsn,
        sync_state,
        pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replication_lag_bytes
    FROM pg_stat_replication;

    GRANT SELECT ON replication_status TO $POSTGRES_USER;
EOSQL

# Configure pg_hba.conf for replication
echo "host replication replicator 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

echo "✅ PostgreSQL primary configured for replication"

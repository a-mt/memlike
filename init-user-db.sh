#!/usr/bin/env bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER "$POSTGRES_API_USER" WITH PASSWORD '$POSTGRES_API_PASSWORD';
    CREATE DATABASE "$POSTGRES_API_DB";
    GRANT ALL PRIVILEGES ON DATABASE "$POSTGRES_API_DB" TO "$POSTGRES_API_USER";
EOSQL

PGPASSWORD="$POSTGRES_API_PASSWORD" psql -v ON_ERROR_STOP=1 --username "$POSTGRES_API_USER" --dbname "$POSTGRES_API_DB" --no-psqlrc -f /init-db.sql

# List users: \du
# Update user password: \password memuser
# Switch current user/db: \c memdb memuser

# export PGPORT=5435 PGPASSWORD=testpass POSTGRES_USER=testuser POSTGRES_DB=testdb
# export PGDATA=$(mktemp -d --suffix=.db/)
# rm -rf /tmp/*.db
# /usr/local/bin/docker-ensure-initdb.sh

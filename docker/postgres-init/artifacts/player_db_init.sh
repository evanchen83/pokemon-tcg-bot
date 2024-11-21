#!/bin/bash

# Set the PGPASSWORD environment variable to allow psql to connect without prompting
export PGPASSWORD=${POSTGRES_PASSWORD}

# Connect to the default "postgres" database and create the custom database if it doesn't exist
echo "Creating the ${POSTGRES_DB} database..."
psql -h postgres -U ${POSTGRES_USER} -d postgres -c "CREATE DATABASE ${POSTGRES_DB};" || echo "Database ${POSTGRES_DB} already exists."

# Set Liquibase environment variables
export LIQUIBASE_COMMAND_CHANGELOG_FILE=/changelog/db.changelog-master.sql
export LIQUIBASE_COMMAND_URL=jdbc:postgresql://postgres:5432/${POSTGRES_DB}
export LIQUIBASE_COMMAND_USERNAME=${POSTGRES_USER}
export LIQUIBASE_COMMAND_PASSWORD=${POSTGRES_PASSWORD}

# Run Liquibase to apply the changes
echo "Running Liquibase update..."
liquibase update
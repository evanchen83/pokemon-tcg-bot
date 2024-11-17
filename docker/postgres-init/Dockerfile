# Use the official Liquibase image as the base
FROM liquibase/liquibase:4.23.1

# Switch to root user to handle permissions
USER root

# Install PostgreSQL client (which includes psql)
RUN apt-get update && apt-get install -y postgresql-client

# Add PostgreSQL JDBC driver with proper permissions
ADD https://jdbc.postgresql.org/download/postgresql-42.6.0.jar /liquibase/lib/postgresql-42.6.0.jar
RUN chmod 644 /liquibase/lib/postgresql-42.6.0.jar

# Copy scripts and changelog to the appropriate location in the container
COPY artifacts/db.changelog-master.sql /liquibase/changelog/db.changelog-master.sql
COPY artifacts/player_db_init.sh /liquibase/player_db_init.sh

# Make the script executable
RUN chmod +x /liquibase/player_db_init.sh

# Set the entrypoint to run the initialization script
ENTRYPOINT ["/liquibase/player_db_init.sh"]

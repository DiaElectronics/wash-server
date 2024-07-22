#!/bin/bash

POSTGRES="postgres"
CONTAINER_PG="lcw-pg"
DB_NAME="wash"
DB_USER="wash"
DB_PASS="adm-pass-test"
DUMP_FILE="db_dump.sql"
DUMP_CONTAINER_PATH="/tmp/$DUMP_FILE"

# Step 1: Perform git pull
echo "Updating repository..."
git pull
if [ $? -ne 0 ]; then
  echo "Error: git pull failed!"
  exit 1
fi
echo "Repository updated."

# Step 2: Stop all running containers
echo "Stopping all running containers..."
docker compose down
if [ $? -ne 0 ]; then
  echo "Error: Failed to stop containers!"
  exit 1
fi
echo "All containers stopped."

# Step 3: Start only the 'postgres' container to load the database dump
echo "Starting only the $POSTGRES container..."
docker compose up -d $POSTGRES
if [ $? -ne 0 ]; then
  echo "Error: Failed to start $POSTGRES container!"
  exit 1
fi
echo "$POSTGRES container started."

# Wait for the postgres service to be ready (you might need to adjust the logic here)
echo "Waiting for $POSTGRES container to be ready..."
sleep 10

# Step 4: Copy the dump file to the container
echo "Copying dump file to $POSTGRES container..."
docker cp $DUMP_FILE $CONTAINER_PG:$DUMP_CONTAINER_PATH
if [ $? -ne 0 ]; then
  echo "Error: Failed to copy dump file to $POSTGRES container!"
  exit 1
fi
echo "Dump file copied successfully."

# Step 5: Drop the existing database, create a new one, and restore the dump
echo "Dropping the existing database if it exists..."
docker exec -i $CONTAINER_PG psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME"
if [ ${PIPESTATUS[0]} -ne 0 ]; then
  echo "Error: Failed to drop existing database! Checking logs..."
  exit 1
fi
echo "Existing database dropped."

echo "Creating a new database..."
docker exec -i $CONTAINER_PG psql -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME"
if [ ${PIPESTATUS[0]} -ne 0 ]; then
  echo "Error: Failed to create new database! Checking logs..."
  exit 1
fi
echo "New database created."

echo "Restoring database dump using pg_restore..."
docker exec -i $CONTAINER_PG pg_restore -U $DB_USER -d $DB_NAME $DUMP_CONTAINER_PATH
if [ ${PIPESTATUS[0]} -ne 0 ]; then
  echo "Error: Database restore failed! Checking logs..."
  exit 1
fi
echo "Database restore successful."

# Step 6: Start all other containers
echo "Starting all other containers..."
docker compose up -d
if [ $? -ne 0 ]; then
  echo "Error: Failed to start all containers!"
  exit 1
fi
echo "All containers started."

# Cleanup
echo "Cleaning up..."
rm $DUMP_FILE
docker exec -i $CONTAINER_PG rm $DUMP_CONTAINER_PATH

echo "Script execution completed."
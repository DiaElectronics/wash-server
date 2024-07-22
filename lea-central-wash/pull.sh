#!/bin/bash

CONTAINER_PG="lcw-pg"
DB_NAME="wash"
DB_USER="wash"
DB_PASS="adm-pass-test"
DUMP_FILE="db_dump.sql"
DUMP_CONTAINER_PATH="/var/lib/postgresql/data/$DUMP_FILE"

echo "Dumping database from $CONTAINER_PG container..."
docker exec -t $CONTAINER_PG pg_dump -U $DB_USER -d $DB_NAME -F c -f $DUMP_CONTAINER_PATH
if [ $? -ne 0 ]; then
  echo "Error: Database dump failed!"
  exit 1
fi
docker cp $CONTAINER_PG:$DUMP_CONTAINER_PATH .
docker exec -t $CONTAINER_PG rm $DUMP_CONTAINER_PATH
echo "Database dump successful."
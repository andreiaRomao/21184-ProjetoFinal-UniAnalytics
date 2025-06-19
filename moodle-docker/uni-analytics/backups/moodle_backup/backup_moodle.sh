#!/bin/bash

# Nome do container da base de dados
CONTAINER_NAME="moodle-docker-db-1"

# Nome fixo do ficheiro de backup
BACKUP_FILE="db_moodle_backup.sql"

# Faz o backup
docker exec -i $CONTAINER_NAME mysqldump -u root -proot moodle > "$BACKUP_FILE"

echo "Backup criado com sucesso: $BACKUP_FILE"

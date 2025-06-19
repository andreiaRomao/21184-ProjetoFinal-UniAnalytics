#!/bin/bash
cat db_moodle_backup.sql | docker exec -i moodle-docker-db-1 mysql -u moodle -pmoodle moodle
echo "Base de dados restaurada com sucesso!"

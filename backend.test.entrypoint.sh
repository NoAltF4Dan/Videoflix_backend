#!/bin/bash
set -e

# Farben für schönere Logs
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}⏳ Warte auf Postgres ($POSTGRES_HOST:$POSTGRES_PORT)...${NC}"
bash /app/scripts/wait-for-it.sh $POSTGRES_HOST:$POSTGRES_PORT --timeout=30 --strict

echo -e "${GREEN}⏳ Warte auf Redis ($REDIS_HOST:$REDIS_PORT)...${NC}"
bash /app/scripts/wait-for-it.sh $REDIS_HOST:$REDIS_PORT --timeout=30 --strict

echo -e "${GREEN}🚀 Führe Migrationen aus...${NC}"
python manage.py migrate --noinput

echo -e "${GREEN}🧪 Starte Pytest mit Coverage...${NC}"
exec "$@"
# db/start-db.sh
#!/bin/sh
set -eu

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
ENV_FILE="$ROOT_DIR/.env"

# Lightweight .env loader (KEY=VALUE, ignores comments/blank lines)
if [ -f "$ENV_FILE" ]; then
  echo "Using env file: $ENV_FILE"
  while IFS= read -r line; do
    case "$line" in
      ''|\#*) continue ;;
      *) export "$line" ;;
    esac
  done < "$ENV_FILE"
fi

# Defaults if unset
POSTGRES_DB=${POSTGRES_DB:-iot}
POSTGRES_USER=${POSTGRES_USER:-iot}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-iotpass}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
DB_WAIT_TIMEOUT=${DB_WAIT_TIMEOUT:-90}   # seconds

# Compose args (explicitly pass env-file if it exists)
COMPOSE_ARGS="-f \"$COMPOSE_FILE\""
if [ -f "$ENV_FILE" ]; then
  COMPOSE_ARGS="$COMPOSE_ARGS --env-file \"$ENV_FILE\""
fi

# Bring up DB
eval docker compose $COMPOSE_ARGS up -d db

printf "Waiting for Postgres"
deadline=$(( $(date +%s) + DB_WAIT_TIMEOUT ))
while :; do
  if eval docker compose $COMPOSE_ARGS exec -T db pg_isready \
       -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    break
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "\nTimed out after ${DB_WAIT_TIMEOUT}s. Recent DB logs:"
    eval docker compose $COMPOSE_ARGS logs --no-color db | tail -n 200 || true
    exit 1
  fi
  sleep 2
  printf "."
done
printf "\n"

echo "Postgres ready."
echo "Connection → postgres://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:$POSTGRES_PORT/$POSTGRES_DB"

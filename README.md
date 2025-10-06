# Able IoT Challenge – Run Guide

## Overview
I chose to tackle this problem by creating a series of containerized micro applications that handle ingestion and analytics separately. The targeted code the Able team required is almost all in Ingest API and containerized as iot_api and iot_db. However, Analytics ui is a Next.js based app that allows you to see sample queries of useful insights, SSE updating tables, and all the documentation translated from markdown docs in the ```./docs``` file

Two services backed by Postgres:
- Ingest API (FastAPI) at http://localhost:8000 – accepts telemetry and startup events
- Analytics UI (Next.js) at http://localhost:3000 – read-only dashboards, docs, and example queries

Database runs in Docker and is initialized from `ingest_service/db/init/*.sql` (tables, views, metrics).

## Prerequisites
- Docker and Docker Compose (***REQUIRED***)
- Python 3.10+ (only if you want to run the local event generator)

## 1) Configure environment
Create a `.env` file in the repo root (used by docker-compose):

  > This is necessary inorder to create the database and have the API connect to it using a generic connection string 

```bash
cat > .env <<'EOF'
POSTGRES_DB=iot
POSTGRES_USER=iot
POSTGRES_PASSWORD=iotpass
POSTGRES_PORT=5432

# python services
API_PORT=8000
WORKER_ENABLED=false   
DATABASE_URL=postgresql://iot:iotpass@db:5432/iot 

EOF
```

## 2) Start the stack
From the repo root:

```bash
docker compose up -d
```

Run: ``` docker ps ```
You should see something like the following: 
```bash
CONTAINER ID   IMAGE                    COMMAND                  CREATED          STATUS                    PORTS                    NAMES
db2368da32b7   node:20-alpine           "docker-entrypoint.s…"   24 seconds ago   Up 18 seconds             0.0.0.0:3000->3000/tcp   iot_analytics
41bf605096fa   able-iot-challenge-api   "uvicorn main:app --…"   24 seconds ago   Up 18 seconds             0.0.0.0:8000->8000/tcp   iot_api
fa8045548d32   postgres:16-alpine       "docker-entrypoint.s…"   24 seconds ago   Up 24 seconds (healthy)   0.0.0.0:5432->5432/tcp   iot_db
```

Wait for Postgres to become healthy. The Ingest API will start after the DB is ready.

Health/status check:
```bash
curl -s http://localhost:8000/status
```
You should see the following return: ```{"status":"ok"}%```

## 3) Send sample data (generator → ingest API)
Open a terminal in the repo root and run:

```bash
python3 -u publisher/iot_device_message_generator.py | python3 publisher/pipe_to_api.py --url http://localhost:8000/ingest --batch 1 --verbose
```
> this will run the sample iot_device_message_generator provided by your team. This pipes the output to a middleware that forms API requests with the output. Therefore I have made no changes to the message generator. 

Notes:
- The generator intentionally emits some malformed lines; the API logs those to `raw_record` + `ingest_error`.
- To post only well-formed events, you can filter: `... | grep --line-buffered '"event_type"' | ...`.

## 4) View analytics UI and docs
> ### I highly recommend trying this out. This is a serverside rendered dynamic application that can be changed whenever new documentation is addedor new sample queries are added. It is a simple way to view all of the documentation, sample analytics, and proof that the service is working with proper error handling. Just make sure all iot_* containers are running at the same time.

- Analytics dashboard: http://localhost:3000
  - Shows metrics tables that refresh periodically
  - “Run example query” dialog lets you execute four curated SQL examples and see the SQL + results
- Documentation: http://localhost:3000/docs OR CLICK "Documentation" button in the UI
  - Ingest, Analytics, Database, and System Design markdown rendered in the UI

## 5) Run the example analysis SQL in psql (optional)
This runs the commented queries demonstrating legacy vs new ingestion and left/right switches:

```bash
docker compose exec -T db psql -U ${POSTGRES_USER:-iot} -d ${POSTGRES_DB:-iot} -f ingest_service/db/queries/analysis_examples.sql
```

## Common issues
- DB schema didn’t apply: The init scripts only run on a fresh volume. To re-init (DELETES ALL DB DATA):
  ```bash
  docker compose down -v
  docker compose up -d
  ```
- Permissions on files after running containers: if needed, from repo root
  ```bash
  sudo chown -R "$USER":"$USER" analytics_service ingest_service
  ```

## Stop services
```bash
docker compose down
```

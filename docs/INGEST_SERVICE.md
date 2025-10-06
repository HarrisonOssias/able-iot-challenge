# Ingest Service

## Overview
FastAPI app that ingests IoT telemetry and device startup events and writes to Postgres. Robust validation, error logging, and idempotent inserts.

## Endpoints
- POST `/ingest`
  - Accepts one JSON object or an array.
  - Telemetry schema: `device_id`, `event_type`, `value`, `timestamp`.
  - Startup schema: `event_type = device_startup`, `serial`, `provision_token`, `timestamp`, optional `firmware`.

## Behavior
- Valid telemetry → `raw_record` + `processed_record` rows.
- Malformed telemetry → `raw_record` + `ingest_error` row; request returns `invalid`.
- Device startup → validates HMAC token and creates/returns device id.
- Legacy generator support → creates placeholder device rows when unknown `device_id` appears.

## Code Map
- `ingest_service/routes/ingest.py` – HTTP binding.
- `ingest_service/services/ingest_services.py` – validation, token verification, DB writes.
- `ingest_service/db/models/*` – SQL helpers for raw/processed/errors/devices.
- `ingest_service/schemas/record.py` – Pydantic validation.
- `ingest_service/db/init/*.sql` – tables, views, metrics.

## Error Handling
- All requests are logged as `raw_record`.
- Validation/DB errors are upserted into `ingest_error` keyed by `raw_data_id`.
- Processed inserts use `ON CONFLICT DO NOTHING` + unique indexes to avoid duplicates.

## Provisioning Token
- HMAC-SHA256 over the device serial using `settings.provision_secret`.
- Verified using constant-time compare.

## Local Dev
- `docker compose up -d` (starts Postgres + ingest API).
- Health: `GET /health`.
- Example ingest: `publisher/iot_device_message_generator.py` piped to `publisher/pipe_to_api.py`.

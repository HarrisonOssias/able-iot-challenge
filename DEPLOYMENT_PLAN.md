# IoT Pipeline Deployment & Validation Plan

## Environments
- Dev: local docker-compose (`db`, `api`)
- Staging: managed Postgres + containerized API
- Prod: HA Postgres (managed), API behind LB, centralized logs

## Schema Management
- Init SQL: `ingest_service/db/init/*.sql` mounted to Postgres
- Backward-compatible migrations only; preserve legacy + new fields
- Views provide read-time conversion (ticks→mm)

## Rollout Steps
1) Apply DB schema (or migrate) in maintenance window if needed
2) Deploy API v1 supporting both legacy and new formats
3) Enable feature flag for device_startup provisioning secret
4) Start canary devices on new firmware; monitor
5) Gradually increase rollout waves

## Validation & Monitoring
- Health: `GET /health`
- Ingestion SLOs: insert latency p95, error rate
- Data checks:
  - `ingest_parse` view: ensure parse_ok rises; inspect `ingest_error`
  - Metrics views: `metric_avg_extension_mm`, `metric_extension_vs_retraction`, `metric_battery_summary`
- Alerts: spike in `startup_auth_error`, DB connection failures, high dedupe conflicts

## Failure Handling
- Malformed messages: stored in `raw_record`, error in `ingest_error`
- Idempotency: unique indexes on `processed_record` prevent duplicates
- Unknown devices: auto-create placeholder on first telemetry; startup path provisions by serial

## Rollback Strategy
- Revert API image
- Schema is additive; no destructive change required

## Security
- Provisioning HMAC secret via env (`provision_secret`)
- DB creds via env
- Limit DB user to required privileges

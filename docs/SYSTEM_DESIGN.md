# System Design – IoT Telemetry + Mixed-Format Rollout

## Goals
- Ingest both legacy (ticks) and new (mm) platform extension formats concurrently.
- Preserve raw semantics; do not mutate legacy values at rest.
- Provide clear observability for parsing, errors, and rollout validation.
- Keep the design simple, testable, and easy to operate locally.

## Architecture
- Producer: local generator (`publisher/iot_device_message_generator.py`) streams JSON events.
- Ingest API (FastAPI): accepts startup + telemetry; validates; writes to Postgres.
- Postgres: facts (`processed_record`), raw (`raw_record`), errors (`ingest_error`), dims (`device`, `record_type`).
- Analytics (Next.js): read-only API routes + UI for metrics, docs, and example queries.

```
[Generator] → [Ingest API] → [raw_record]
                          ↘  validate → [processed_record] / [ingest_error]
[Analytics UI] → read-only SQL views + metrics
```

## Data Model (why this shape?)
- `raw_record`: immutable ledger of every request payload; fuels debugging and replay.
- `ingest_error`: 1:1 with `raw_record` when parse/DB fails; keeps the last error reason.
- `processed_record`: narrow fact table for analytics; joins `record_type` with FKs.
- `device`: minimal, numeric PK; supports lazy create for legacy numeric ids.
- `record_type`: de-couples code from hard-coded enums; insert-on-first-seen.

Indexes + idempotency:
- `uq_processed_by_raw` guarantees a single processed fact per raw.
- Optional `uq_processed_event(device_id, type, record_time, value)` protects replays.

## Mixed-Format Strategy
- Storage: keep ticks and mm in their native units; never rewrite.
- Read-time unification: `v_platform_extension_mm` converts ticks→mm (÷20.0).
- Metrics build on top of views; SQL demonstrates equivalence during rollout.

## Ingestion Flow (happy path)
1) Accept JSON (single or batch); immediately store in `raw_record`.
2) Validate message (Pydantic schemas). For startup events, verify HMAC token.
3) Ensure `device` row exists (startup by serial or lazy create by numeric id).
4) Insert into `processed_record` with ON CONFLICT DO NOTHING for idempotency.
5) Return `{ raw_id, processed_id | null, status }`; on error, upsert `ingest_error`.

## Observability & Validation
- `ingest_parse` view correlates raw, processed, and error for a single pane-of-glass.
- Example queries (analytics UI → Run example query) prove:
  - Legacy vs new counts
  - Devices with both formats
  - Unified recent rows (ticks→mm)
  - Left↔right sign switches

## Rollout Plan (summary)
- Ship API that accepts both formats first (backward compatible).
- Enable canary devices for new firmware; watch `ingest_error` and metrics.
- Scale rollout; track left/right switch behavior and averages for anomalies.
- Rollback is trivial: revert API image; schema changes are additive/idempotent.

## Reliability & Scale
- Postgres connection pooling via psycopg_pool.
- Hot-path indexes on `(device_id, record_time)` and `(type, record_time)`.
- Stateless APIs; horizontally scalable behind a load balancer.

## Security
- Startup provisioning uses HMAC-SHA256 with a shared secret.
- DB access via `DATABASE_URL`; limit to least-privileged user in production.

## Future Enhancements
- Kafka (or similar) between ingest and storage for buffering and fan-out.
- Per-device calibration table to replace global 20:1 conversion.
- Materialized views for heavy metrics; TTL-based rollups.
- Authn for analytics UI; RBAC for query endpoints.

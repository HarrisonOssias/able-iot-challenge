# Database Schema

![Entity Relationship Diagram](/docs/erd.png)

## Core Tables
- `device(id SERIAL PK, name TEXT UNIQUE, init_date TIMESTAMPTZ)`
- `record_type(id SERIAL PK, name TEXT UNIQUE, version_id INT NULL)`
- `raw_record(id BIGSERIAL PK, raw_message JSONB, arrival_time TIMESTAMPTZ)`
- `ingest_error(raw_data_id BIGINT PK FK raw_record, error TEXT, created_at TIMESTAMPTZ)`
- `processed_record(id BIGSERIAL PK, device_id INT FK device, raw_data_id BIGINT FK raw_record, record_time TIMESTAMPTZ, type INT FK record_type, value NUMERIC)`

## Indexes & Idempotency
- `uq_processed_by_raw` ensures 1 processed per raw.
- `uq_processed_event(device_id,type,record_time,value)` optional idempotency.
- Hot path: indexes on `(device_id, record_time)`, `(type, record_time)`.

## Views
- `ingest_parse`: join of raw, processed, error for parse visibility.
- `v_platform_extension_mm`: unifies legacy ticks to mm at read time (`mm = ticks / 20.0`).

## Metrics Views
- `metric_avg_extension_mm`, `metric_extension_vs_retraction`, `metric_battery_summary`, `metric_platform_height`.

## Example Queries
See `ingest_service/db/queries/analysis_examples.sql` for: type counts, devices with both formats, unified mm values, averages, and left/right switches.

## Migration/Init
- Compose mounts `ingest_service/db/init/*.sql` into Postgres.
- Safe to re-run; `IF NOT EXISTS` and `ON CONFLICT` used for idempotency.

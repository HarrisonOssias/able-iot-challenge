# Database Schema

![Entity Relationship Diagram](/docs/erd.png)

## Core Tables Design

I built this with a classic star schema in mind:

- `device(id SERIAL PK, name TEXT UNIQUE, init_date TIMESTAMPTZ)` - Auto-incrementing IDs and unique names make device management seamless
- `record_type(id SERIAL PK, name TEXT UNIQUE, version_id INT NULL)` - Defines our event types and links to firmware versions
- `raw_record(id BIGSERIAL PK, raw_message JSONB, arrival_time TIMESTAMPTZ)` - Stores exactly what we received, crucial for debugging
- `ingest_error(raw_data_id BIGINT PK FK raw_record, error TEXT, created_at TIMESTAMPTZ)` - Captures validation failures with direct link to raw data
- `processed_record(id BIGSERIAL PK, device_id INT FK device, raw_data_id BIGINT FK raw_record, record_time TIMESTAMPTZ, type INT FK record_type, value NUMERIC)` - Our normalized fact table with proper relationships

## The Cool Part: Format Unification

Instead of migrating data or having separate tables, I implemented a view that unifies legacy ticks and new mm formats at query time. The conversion is super simple: `ticks / 20.0 = mm`.

This means:
1. We store data in its original form (no data loss)
2. We can query it uniformly (no app-side conversion)
3. We don't need schema migrations when formats change

## Performance Considerations

Strategic indexes for hot query paths:
- `uq_processed_by_raw` ensures 1 processed record per raw message
- `uq_processed_event(device_id,type,record_time,value)` provides idempotency across replays
- Hot path indexes on `(device_id, record_time)` and `(type, record_time)` for time-series queries

## Metrics Views

Built several metrics views on top of this foundation:
- `metric_avg_extension_mm` - Average extension in mm per device
- `metric_extension_vs_retraction` - Counts extension vs retraction events using window functions
- `metric_battery_summary` - Min/max/avg battery levels with last seen timestamp
- `metric_platform_height` - Platform height distribution stats

> these provide 'useful' insights while processing both legacy and current dat formats. 

## Example Queries

Check out `ingest_service/db/queries/analysis_examples.sql` for:
- Type counts (legacy vs new)
- Devices with both formats
- Unified mm values with source tracking
- Comparative averages across formats
- Left/right sign switches

## Migration & Initialization

- Docker Compose mounts `ingest_service/db/init/*.sql` into Postgres container
- Scripts use `IF NOT EXISTS` and `ON CONFLICT` for idempotent execution
- Safe to re-run during development or container restarts
-- View: derive parse_ok + surface error message
CREATE OR REPLACE VIEW ingest_parse AS
SELECT
  rr.id AS raw_data_id,
  COALESCE(pr.device_id, (rr.raw_message->>'device_id')::int) AS device_id,
  (pr.id IS NOT NULL) AS parse_ok,
  ie.error
FROM raw_record rr
LEFT JOIN processed_record pr ON pr.raw_data_id = rr.id
LEFT JOIN ingest_error    ie ON ie.raw_data_id = rr.id;

-- View: unify legacy ticks → mm at read time (no schema changes required)
CREATE OR REPLACE VIEW v_platform_extension_mm AS
SELECT
  pr.device_id,
  pr.record_time AS observed_at,
  CASE
    WHEN rt.name = 'platform_extension_mm'    THEN pr.value
    WHEN rt.name = 'platform_extension_ticks' THEN pr.value / 20.0
  END AS extension_mm
FROM processed_record pr
JOIN record_type rt ON rt.id = pr.type
WHERE rt.name IN ('platform_extension_mm','platform_extension_ticks');

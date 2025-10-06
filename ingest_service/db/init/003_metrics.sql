-- Example Metrics Queries

-- 1) Average platform extension (mm) per device and overall
-- Uses read-time conversion view to unify ticks→mm without altering storage
CREATE OR REPLACE VIEW metric_avg_extension_mm AS
SELECT
  device_id,
  AVG(extension_mm)::numeric(10,3) AS avg_extension_mm
FROM v_platform_extension_mm
GROUP BY device_id;

-- 2) Counts of extension vs. retraction events (based on mm increases/decreases)
-- Compute deltas in mm space ordered by time per device
CREATE OR REPLACE VIEW metric_extension_vs_retraction AS
WITH series AS (
  SELECT
    device_id,
    observed_at,
    extension_mm,
    LAG(extension_mm) OVER (PARTITION BY device_id ORDER BY observed_at) AS prev_mm
  FROM v_platform_extension_mm
)
SELECT
  device_id,
  SUM(CASE WHEN prev_mm IS NOT NULL AND extension_mm > prev_mm THEN 1 ELSE 0 END) AS extensions,
  SUM(CASE WHEN prev_mm IS NOT NULL AND extension_mm < prev_mm THEN 1 ELSE 0 END) AS retractions
FROM series
GROUP BY device_id;

-- 3) Battery and sensor summaries (min/max/avg and latest timestamp)
CREATE OR REPLACE VIEW metric_battery_summary AS
SELECT
  pr.device_id,
  MIN(pr.value)::numeric(10,1) AS min_pct,
  MAX(pr.value)::numeric(10,1) AS max_pct,
  AVG(pr.value)::numeric(10,2) AS avg_pct,
  MAX(pr.record_time)           AS last_seen
FROM processed_record pr
JOIN record_type rt ON rt.id = pr.type AND rt.name = 'battery_charge'
GROUP BY pr.device_id;

-- 4) Recent platform height distribution
CREATE OR REPLACE VIEW metric_platform_height AS
SELECT
  pr.device_id,
  MIN(pr.value) AS min_height_mm,
  MAX(pr.value) AS max_height_mm,
  AVG(pr.value) AS avg_height_mm
FROM processed_record pr
JOIN record_type rt ON rt.id = pr.type AND rt.name = 'platform_height_mm'
GROUP BY pr.device_id;



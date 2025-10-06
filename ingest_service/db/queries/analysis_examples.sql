-- analysis_examples.sql
--
-- Purpose: One-stop set of commented queries to demonstrate that both
--          legacy (platform_extension_ticks) and new (platform_extension_mm)
--          data are ingested, and to analyze unified millimeter values.
--
-- How to run (from repo root):
--   docker compose exec -T db psql \
--     -U ${POSTGRES_USER:-iot} -d ${POSTGRES_DB:-iot} \
--     -f ingest_service/db/queries/analysis_examples.sql
--
-- Notes:
-- - v_platform_extension_mm view unifies ticks→mm at read-time (no data rewrite).
-- - processed_record stores original values; record_type indicates the source type.

\echo '1) Counts by type (legacy vs new)'
SELECT rt.name AS type, COUNT(*) AS rows
FROM processed_record pr
JOIN record_type rt ON rt.id = pr.type
WHERE rt.name IN ('platform_extension_ticks','platform_extension_mm')
GROUP BY 1
ORDER BY 1;

\echo ''
\echo '2) Devices that have BOTH legacy and new events'
SELECT
  pr.device_id,
  COUNT(*) FILTER (WHERE rt.name='platform_extension_mm')    AS new_mm,
  COUNT(*) FILTER (WHERE rt.name='platform_extension_ticks') AS legacy_ticks
FROM processed_record pr
JOIN record_type rt ON rt.id = pr.type
WHERE rt.name IN ('platform_extension_ticks','platform_extension_mm')
GROUP BY pr.device_id
HAVING COUNT(*) FILTER (WHERE rt.name='platform_extension_mm')    > 0
   AND COUNT(*) FILTER (WHERE rt.name='platform_extension_ticks') > 0
ORDER BY pr.device_id;

\echo ''
\echo '3) Unified recent values with source + conversion (ticks→mm at read-time)'
SELECT
  pr.device_id,
  pr.record_time,
  rt.name AS source_type,
  pr.value AS source_value,
  CASE
    WHEN rt.name='platform_extension_mm'    THEN pr.value
    WHEN rt.name='platform_extension_ticks' THEN pr.value / 20.0
  END AS extension_mm
FROM processed_record pr
JOIN record_type rt ON rt.id = pr.type
WHERE rt.name IN ('platform_extension_ticks','platform_extension_mm')
ORDER BY pr.record_time DESC
LIMIT 50;

\echo ''
\echo '4) Compare averages: new-only vs legacy-only (converted) vs unified'
SELECT
  pr.device_id,
  AVG(CASE WHEN rt.name='platform_extension_mm'    THEN pr.value END)        AS avg_new_only_mm,
  AVG(CASE WHEN rt.name='platform_extension_ticks' THEN pr.value / 20.0 END) AS avg_legacy_only_mm,
  AVG(CASE
        WHEN rt.name='platform_extension_mm'    THEN pr.value
        WHEN rt.name='platform_extension_ticks' THEN pr.value / 20.0
      END) AS avg_all_mm
FROM processed_record pr
JOIN record_type rt ON rt.id = pr.type
WHERE rt.name IN ('platform_extension_ticks','platform_extension_mm')
GROUP BY pr.device_id
ORDER BY pr.device_id;

\echo ''
\echo '5) Left↔Right sign switches (all time) using v_platform_extension_mm'
WITH series AS (
  SELECT
    device_id,
    observed_at,
    extension_mm,
    CASE WHEN extension_mm > 0 THEN 'right'
         WHEN extension_mm < 0 THEN 'left'
         ELSE 'center' END AS side,
    LAG(CASE WHEN extension_mm > 0 THEN 'right'
             WHEN extension_mm < 0 THEN 'left'
             ELSE 'center' END)
      OVER (PARTITION BY device_id ORDER BY observed_at) AS prev_side
  FROM v_platform_extension_mm
)
SELECT
  device_id,
  COUNT(*) FILTER (WHERE prev_side='left'  AND side='right') AS left_to_right,
  COUNT(*) FILTER (WHERE prev_side='right' AND side='left')  AS right_to_left,
  COUNT(*) FILTER (
    WHERE prev_side IN ('left','right') AND side IN ('left','right') AND prev_side<>side
  ) AS total_side_switches
FROM series
WHERE prev_side IS NOT NULL AND side <> 'center'
GROUP BY device_id
ORDER BY device_id;

\echo ''
\echo '6) Left↔Right sign switches in the last 1 hour'
WITH series AS (
  SELECT
    device_id,
    observed_at,
    extension_mm,
    CASE WHEN extension_mm > 0 THEN 'right'
         WHEN extension_mm < 0 THEN 'left'
         ELSE 'center' END AS side,
    LAG(CASE WHEN extension_mm > 0 THEN 'right'
             WHEN extension_mm < 0 THEN 'left'
             ELSE 'center' END)
      OVER (PARTITION BY device_id ORDER BY observed_at) AS prev_side
  FROM v_platform_extension_mm
  WHERE observed_at >= now() - interval '1 hour'
)
SELECT
  device_id,
  COUNT(*) FILTER (WHERE prev_side='left' AND side='right')  AS left_to_right,
  COUNT(*) FILTER (WHERE prev_side='right' AND side='left') AS right_to_left
FROM series
WHERE prev_side IS NOT NULL AND side <> 'center'
GROUP BY device_id
ORDER BY device_id;



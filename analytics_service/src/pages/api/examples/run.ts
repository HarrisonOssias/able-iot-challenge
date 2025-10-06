import type { NextApiRequest, NextApiResponse } from 'next';
import { getPool } from '../../../lib/db';

const QUERY_MAP: Record<string, string> = {
  counts_by_type: `
    -- quick sanity check: how many legacy vs new rows did we ingest?
    -- 1) project the human-friendly type name via record_type
    SELECT rt.name AS type, COUNT(*) AS rows
    -- 2) start from processed rows (one per successful event)
    FROM processed_record pr
    -- 3) join to type dim so we can filter by semantic names
    JOIN record_type rt ON rt.id = pr.type
    -- 4) keep only the two formats we care about here
    WHERE rt.name IN ('platform_extension_ticks','platform_extension_mm')
    -- 5) group by that type name
    GROUP BY 1
    -- 6) stable sort for predictable output
    ORDER BY 1;`,
  devices_both_formats: `
    -- which devices are reporting both formats? (proves dual-ingest works)
    -- 1) select device and separate counts for new vs legacy using FILTER
    SELECT
      pr.device_id,
      COUNT(*) FILTER (WHERE rt.name='platform_extension_mm')    AS new_mm,
      COUNT(*) FILTER (WHERE rt.name='platform_extension_ticks') AS legacy_ticks
    -- 2) from processed facts joined to type dimension
    FROM processed_record pr
    JOIN record_type rt ON rt.id = pr.type
    -- 3) only consider the two platform-extension formats
    WHERE rt.name IN ('platform_extension_ticks','platform_extension_mm')
    -- 4) roll up by device
    GROUP BY pr.device_id
    -- 5) keep only devices that have at least one row of each flavor
    HAVING COUNT(*) FILTER (WHERE rt.name='platform_extension_mm')    > 0
       AND COUNT(*) FILTER (WHERE rt.name='platform_extension_ticks') > 0
    -- 6) stable device sort
    ORDER BY pr.device_id;`,
  unified_recent: `
    -- last 50 unified readings (ticks → mm at read time)
    -- 1) project device/time, original source, and original value
    SELECT
      pr.device_id,
      pr.record_time,
      rt.name AS source_type,
      pr.value AS source_value,
      -- 2) convert ticks to mm in the SELECT (we do NOT rewrite storage)
      CASE
        WHEN rt.name='platform_extension_mm'    THEN pr.value
        WHEN rt.name='platform_extension_ticks' THEN pr.value / 20.0
      END AS extension_mm
    -- 3) from the facts joined to type dim
    FROM processed_record pr
    JOIN record_type rt ON rt.id = pr.type
    -- 4) keep only platform-extension formats
    WHERE rt.name IN ('platform_extension_ticks','platform_extension_mm')
    -- 5) most recent first
    ORDER BY pr.record_time DESC
    -- 6) cap to a small, readable sample
    LIMIT 50;`,
  side_switches: `
    -- count left↔right sign switches per device (ignore center)
    -- 1) label each reading as left/right/center and carry previous label
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
    -- 2) aggregate sign transitions (exclude center wobble)
    SELECT
      device_id,
      COUNT(*) FILTER (WHERE prev_side='left' AND side='right')  AS left_to_right,
      COUNT(*) FILTER (WHERE prev_side='right' AND side='left') AS right_to_left
    FROM series
    WHERE prev_side IS NOT NULL AND side <> 'center'
    GROUP BY device_id
    ORDER BY device_id;`,
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const key = String(req.query.key || '');
    const sql = QUERY_MAP[key];
    if (!sql) return res.status(400).json({ error: 'invalid_query_key' });
    const pool = getPool();
    const { rows } = await pool.query(sql);
    res.status(200).json({ sql, rows });
  } catch (e: any) {
    res.status(500).json({ error: e.message || 'internal_error' });
  }
}



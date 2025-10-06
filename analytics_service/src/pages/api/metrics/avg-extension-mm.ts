import type { NextApiRequest, NextApiResponse } from 'next';
import { getPool } from '../../../lib/db';

export default async function handler(_req: NextApiRequest, res: NextApiResponse) {
  try {
    const pool = getPool();
    const { rows } = await pool.query('SELECT * FROM metric_avg_extension_mm ORDER BY device_id');
    res.status(200).json(rows);
  } catch (e: any) {
    res.status(500).json({ error: e.message || 'internal_error' });
  }
}



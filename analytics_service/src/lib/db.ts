import { Pool } from 'pg';

let _pool: Pool | null = null;

export function getPool(): Pool {
  if (!_pool) {
    const conn = process.env.DATABASE_URL;
    if (!conn) throw new Error('DATABASE_URL is not set');
    _pool = new Pool({ connectionString: conn, max: 5 });
  }
  return _pool;
}

from psycopg_pool import AsyncConnectionPool
from psycopg.rows import tuple_row


async def upsert_error(pool: AsyncConnectionPool, raw_id: int, message: str) -> None:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=tuple_row) as cur:
            await cur.execute(
                """
                INSERT INTO ingest_error (raw_data_id, error)
                VALUES (%s, %s)
                ON CONFLICT (raw_data_id) DO UPDATE
                SET error = EXCLUDED.error
                """,
                (raw_id, message[:500]),
            )

from psycopg_pool import AsyncConnectionPool
from psycopg.rows import tuple_row

# simple in-memory cache for record_type ids
_TYPE_CACHE: dict[str, int] = {}


async def get_record_type_id(pool: AsyncConnectionPool, name: str) -> int:
    if name in _TYPE_CACHE:
        return _TYPE_CACHE[name]
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=tuple_row) as cur:
            await cur.execute("SELECT id FROM record_type WHERE name=%s", (name,))
            row = await cur.fetchone()
            if not row:
                await cur.execute("INSERT INTO record_type(name) VALUES (%s) RETURNING id", (name,))
                row = await cur.fetchone()
            _TYPE_CACHE[name] = int(row[0])
            return _TYPE_CACHE[name]


async def insert_processed(
    pool: AsyncConnectionPool,
    *,
    device_id: int,
    raw_id: int,
    timestamp_sec: float,
    type_id: int,
    value: float
) -> int | None:
    """
    Returns new processed id or None if ON CONFLICT DO NOTHING matched
    (useful when you added unique indexes for idempotency).
    """
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=tuple_row) as cur:
            await cur.execute(
                """
                INSERT INTO processed_record (device_id, raw_data_id, record_time, type, value)
                VALUES (%s, %s, to_timestamp(%s), %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (device_id, raw_id, float(timestamp_sec), type_id, float(value)),
            )
            row = await cur.fetchone()
            return int(row[0]) if row else None

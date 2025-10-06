import json
from psycopg import sql
from psycopg.rows import tuple_row  # to get results as tuples for easy unpacking
from psycopg_pool import AsyncConnectionPool


async def insert_raw(pool: AsyncConnectionPool, obj) -> int:
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=tuple_row) as cur:
            await cur.execute(
                # I am not inserting time as default is now() and id is bigserial
                "INSERT INTO raw_record (raw_message) VALUES (%s::jsonb) RETURNING id",
                (json.dumps(obj),),
            )
            (rid,) = await cur.fetchone()  # confirm that id is returned
            return int(rid)

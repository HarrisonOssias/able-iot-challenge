from datetime import datetime
from psycopg.rows import tuple_row
from psycopg_pool import AsyncConnectionPool


async def get_or_create_device_by_serial(pool: AsyncConnectionPool, serial: str) -> int:
    """Use device.name to store the serial; return the device id."""
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=tuple_row) as cur:
            # fast path: exists
            await cur.execute("SELECT id FROM device WHERE name = %s", (serial,))
            row = await cur.fetchone()
            if row:
                return int(row[0])

            # create new device row
            await cur.execute(
                """
                INSERT INTO device (name, init_date)
                VALUES (%s, %s)
                RETURNING id
                """,
                (serial, datetime.utcnow()),
            )
            (new_id,) = await cur.fetchone()
            return int(new_id)


async def ensure_device_exists_by_id(pool: AsyncConnectionPool, device_id: int) -> None:
    """Create a placeholder device row if it doesn't exist yet.

    This is useful for legacy generators that emit numeric device ids without a
    prior provisioning/startup step. Uses a stable placeholder name.
    """
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=tuple_row) as cur:
            await cur.execute(
                """
                INSERT INTO device (id, name, init_date)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (int(device_id), f"device-{int(device_id)}", datetime.utcnow()),
            )

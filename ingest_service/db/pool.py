from psycopg_pool import AsyncConnectionPool
from pydantic_settings import BaseSettings
import asyncio
import logging

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    database_url: str


settings = Settings()

pool: AsyncConnectionPool | None = None


async def init_pool() -> None:
    global pool
    if pool is None:
        pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            max_size=10,
            kwargs={"autocommit": True},
            open=False,
        )
        await pool.open()  # remove deprecation warning

    # quick health check (will succeed given your test)
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            await cur.fetchone()
    log.info("✅ DB pool ready")


async def close_pool() -> None:
    global pool
    if pool is not None:
        await pool.close()
        pool = None


async def get_pool() -> AsyncConnectionPool:
    await init_pool()
    return pool  # type: ignore[return-value]

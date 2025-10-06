"""
Database connection pool management for PostgreSQL.

This module provides async connection pooling for PostgreSQL using psycopg_pool.
It handles:
- Lazy initialization of the connection pool
- Connection health checks
- Graceful pool shutdown
- Thread-safe connection acquisition

The pool is configured with autocommit=True to simplify transaction management.
"""
from psycopg_pool import AsyncConnectionPool
from pydantic_settings import BaseSettings
import asyncio
import logging

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Simple settings model that requires a database_url."""
    database_url: str


# Load settings from environment variables
settings = Settings()

# Global connection pool (initialized lazily)
pool: AsyncConnectionPool | None = None


async def init_pool() -> None:
    """
    Initialize the database connection pool if it doesn't exist.
    
    This function:
    1. Creates a connection pool if one doesn't exist
    2. Configures the pool with appropriate settings
    3. Performs a health check to ensure connectivity
    4. Logs success when the pool is ready
    
    The pool uses autocommit mode to simplify transaction management.
    """
    global pool
    if pool is None:
        # Create a new connection pool
        pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            max_size=10,  # Maximum number of connections in the pool
            kwargs={"autocommit": True},  # Auto-commit mode for simpler transaction management
            open=False,  # Don't open connections immediately
        )
        await pool.open()  # Open the pool (async-friendly)

    # Perform a quick health check to verify connectivity
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            await cur.fetchone()
    log.info(" DB pool ready")


async def close_pool() -> None:
    """
    Close the database connection pool gracefully.
    
    This function:
    1. Closes all connections in the pool
    2. Sets the pool to None to allow garbage collection
    3. Is safe to call even if the pool doesn't exist
    """
    global pool
    if pool is not None:
        await pool.close()
        pool = None


async def get_pool() -> AsyncConnectionPool:
    """
    Get the database connection pool, initializing it if necessary.
    
    Returns:
        AsyncConnectionPool: The initialized connection pool
        
    This function guarantees that a valid, tested pool is returned.
    It's safe to call this function multiple times - the pool is
    only initialized once.
    """
    await init_pool()
    return pool  # type: ignore[return-value]

"""
Database connection module
PostgreSQL via asyncpg + SQLAlchemy async
"""

import os
import structlog

log = structlog.get_logger()

DATABASE_URL = os.getenv("DATABASE_URL", "")


async def init_db():
    """
    Initialize database connection pool.
    Currently a no-op — full async pool added in Week 1 Day 6.
    """
    log.info("Database init skipped — stub mode")
    pass


async def get_db():
    """
    Dependency injector for DB sessions.
    Stub — returns None until full DB layer is wired.
    """
    return None

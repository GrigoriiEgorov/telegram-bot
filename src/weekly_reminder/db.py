from __future__ import annotations

import os
from pathlib import Path

import asyncpg


def _migrations_dir() -> Path:
    configured = os.getenv("MIGRATIONS_DIR")
    candidates = [
        Path(configured) if configured else None,
        Path(__file__).resolve().parents[2] / "migrations",
        Path("/app/migrations"),
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return Path(__file__).resolve().parents[2] / "migrations"


async def create_pool(database_url: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(database_url, min_size=1, max_size=5)


async def apply_migrations(pool: asyncpg.Pool) -> None:
    migrations_dir = _migrations_dir()
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        raise RuntimeError(f"No migrations found in {migrations_dir}")
    async with pool.acquire() as connection:
        for path in migration_files:
            await connection.execute(path.read_text(encoding="utf-8"))

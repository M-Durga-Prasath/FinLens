from  dotenv import load_dotenv
import os
import asyncpg

load_dotenv()

db_url = os.getenv("DATABASE_URL")

_pool: asyncpg.Pool | None = None

async def connect_db():
    global _pool

    if not db_url:
        raise RuntimeError("DB Url not set. Check Env")

    if _pool is None:
        _pool = await asyncpg.create_pool(
            db_url,
            min_size=1,
            max_size=10,
        )


async def close_db():
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_db():
    if _pool is None:
        await connect_db()

    return _pool
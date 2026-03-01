"""
检查数据库中的配置
"""

import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")


db_url = os.getenv('SERVER_STORAGE_URL', '')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+asyncpg://', 1)


async def check():
    engine = create_async_engine(db_url, echo=False, connect_args={'statement_cache_size': 0})
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT section, key_name, value FROM app_config WHERE section='app' AND key_name IN ('api_key', 'app_key')"))
        rows = result.fetchall()
        print("数据库中的配置:")
        for row in rows:
            section, key, value = row
            try:
                parsed = json.loads(value)
                print(f'  {section}.{key} = {parsed}')
            except:
                print(f'  {section}.{key} = {value}')
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check())

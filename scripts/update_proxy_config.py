"""
更新 Grok2API 的代理配置到数据库
"""

import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def update_proxy_config(proxy_url: str):
    # 从 .env 读取数据库连接信息
    import os
    from dotenv import load_dotenv

    env_file = BASE_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    db_url = os.getenv("SERVER_STORAGE_URL", "")
    if not db_url:
        print("错误: 环境变量 SERVER_STORAGE_URL 未设置")
        return

    # 转换数据库 URL
    if db_url.startswith("postgresql+asyncpg://"):
        pass
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"连接到数据库...")

    # 创建引擎
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"statement_cache_size": 0}
    )

    async with engine.begin() as conn:
        # 更新或插入 proxy.base_proxy_url
        await conn.execute(
            text("""
                INSERT INTO app_config (section, key_name, value)
                VALUES ('proxy', 'base_proxy_url', :value)
                ON CONFLICT (section, key_name) DO UPDATE SET value = EXCLUDED.value
            """),
            {"value": json.dumps(proxy_url)}
        )
        print(f"已更新 proxy.base_proxy_url = {proxy_url}")

    await engine.dispose()
    print("配置更新完成!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python update_proxy_config.py <proxy_url>")
        print("示例: python update_proxy_config.py https://grok-proxy.yourname.workers.dev")
        sys.exit(1)

    proxy_url = sys.argv[1]
    asyncio.run(update_proxy_config(proxy_url))

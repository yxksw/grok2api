"""
将 config.toml 配置导入到 PostgreSQL 数据库
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

import json
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def import_config():
    # 读取 config.toml
    config_file = BASE_DIR / "config.toml"
    if not config_file.exists():
        print(f"错误: 找不到配置文件 {config_file}")
        return

    with open(config_file, "rb") as f:
        config_data = tomllib.load(f)

    print(f"读取到 {len(config_data)} 个配置节")

    # Neon 数据库连接字符串
    db_url = "postgresql+asyncpg://neondb_owner:npg_pWPbAj4S1GkD@ep-restless-rice-aib27ooh-pooler.c-4.us-east-1.aws.neon.tech/neondb?ssl=require"

    print(f"连接到数据库...")

    # 创建引擎（禁用 prepared statement 缓存以兼容 pgbouncer）
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"statement_cache_size": 0}
    )

    async with engine.begin() as conn:
        # 检查表是否存在
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'app_config'
            )
        """))
        table_exists = result.scalar()

        if not table_exists:
            print("创建 app_config 表...")
            await conn.execute(text("""
                CREATE TABLE app_config (
                    section VARCHAR(255) NOT NULL,
                    key_name VARCHAR(255) NOT NULL,
                    value TEXT,
                    PRIMARY KEY (section, key_name)
                )
            """))

        # 清空现有配置
        await conn.execute(text("DELETE FROM app_config"))
        print("清空现有配置...")

        # 插入新配置
        params = []
        for section, items in config_data.items():
            if not isinstance(items, dict):
                continue
            for key, val in items.items():
                params.append({
                    "s": section,
                    "k": key,
                    "v": json.dumps(val, ensure_ascii=False),
                })

        if params:
            await conn.execute(
                text("INSERT INTO app_config (section, key_name, value) VALUES (:s, :k, :v)"),
                params,
            )
            print(f"成功导入 {len(params)} 条配置")

        # 显示导入的配置
        result = await conn.execute(text("SELECT section, key_name FROM app_config"))
        rows = result.fetchall()
        print(f"\n数据库中现有配置:")
        current_section = None
        for section, key in sorted(rows):
            if section != current_section:
                print(f"\n[{section}]")
                current_section = section
            print(f"  {key}")

    await engine.dispose()
    print("\n配置导入完成!")


if __name__ == "__main__":
    asyncio.run(import_config())

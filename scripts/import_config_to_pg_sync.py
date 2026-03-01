"""
将 config.toml 配置导入到 PostgreSQL 数据库 (同步版本，兼容 Supabase Pooler)
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

import json
import os
from urllib.parse import urlparse

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def parse_supabase_url(url):
    """解析 Supabase 连接字符串"""
    # 处理各种前缀
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif url.startswith("postgres://"):
        pass  # 保持原样
    elif url.startswith("postgresql://"):
        pass  # 保持原样
    
    parsed = urlparse(url)
    
    # 提取连接参数
    host = parsed.hostname
    port = parsed.port or 6543
    user = parsed.username
    password = parsed.password
    database = parsed.path.lstrip('/') or 'postgres'
    
    # 处理查询参数
    sslmode = 'require'
    if parsed.query:
        for param in parsed.query.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                if key == 'sslmode':
                    sslmode = value
    
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': database,
        'sslmode': sslmode,
    }


def import_config():
    # 读取 config.toml
    config_file = BASE_DIR / "config.toml"
    if not config_file.exists():
        print(f"错误: 找不到配置文件 {config_file}")
        return

    with open(config_file, "rb") as f:
        config_data = tomllib.load(f)

    print(f"读取到 {len(config_data)} 个配置节")

    # 从 .env 读取数据库连接信息
    from dotenv import load_dotenv
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    db_url = os.getenv("SERVER_STORAGE_URL", "")
    if not db_url:
        print("错误: 环境变量 SERVER_STORAGE_URL 未设置")
        return

    # 解析连接字符串
    conn_info = parse_supabase_url(db_url)
    print(f"连接到数据库 {conn_info['host']}:{conn_info['port']}...")

    # 使用 psycopg2 连接（同步）
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("正在安装 psycopg2-binary...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "-q"])
        import psycopg2
        from psycopg2.extras import RealDictCursor

    # 建立连接
    conn = psycopg2.connect(
        host=conn_info['host'],
        port=conn_info['port'],
        user=conn_info['user'],
        password=conn_info['password'],
        database=conn_info['database'],
        sslmode=conn_info['sslmode'],
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'app_config'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("创建 app_config 表...")
            cursor.execute("""
                CREATE TABLE app_config (
                    section VARCHAR(255) NOT NULL,
                    key_name VARCHAR(255) NOT NULL,
                    value TEXT,
                    PRIMARY KEY (section, key_name)
                )
            """)

        # 清空现有配置
        cursor.execute("DELETE FROM app_config")
        print("清空现有配置...")

        # 插入新配置
        insert_sql = "INSERT INTO app_config (section, key_name, value) VALUES (%s, %s, %s)"
        count = 0
        for section, items in config_data.items():
            if not isinstance(items, dict):
                continue
            for key, val in items.items():
                value_json = json.dumps(val, ensure_ascii=False)
                cursor.execute(insert_sql, (section, key, value_json))
                count += 1

        print(f"成功导入 {count} 条配置")

        # 显示导入的配置
        cursor.execute("SELECT section, key_name FROM app_config ORDER BY section, key_name")
        rows = cursor.fetchall()
        print(f"\n数据库中现有配置:")
        current_section = None
        for section, key in rows:
            if section != current_section:
                print(f"\n[{section}]")
                current_section = section
            print(f"  {key}")

    finally:
        cursor.close()
        conn.close()

    print("\n配置导入完成!")


if __name__ == "__main__":
    import_config()

# db.py
import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

DB_POOL = None

def init_db_pool():
    global DB_POOL
    if DB_POOL is None:
        DB_POOL = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "21012")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "country_cache"),
            charset="utf8mb4",
            use_unicode=True
        )

def get_conn():
    if DB_POOL is None:
        init_db_pool()
    return DB_POOL.get_connection()

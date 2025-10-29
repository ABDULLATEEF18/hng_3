# db.py
import os
import psycopg2
from psycopg2 import pool
from urllib.parse import urlparse

DB_URL = os.getenv("DATABASE_URL")

def init_db_pool():
    if not DB_URL:
        raise ValueError("DATABASE_URL not set in environment variables")

    result = urlparse(DB_URL)

    return pool.SimpleConnectionPool(
        1, 20,
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port,
        database=result.path[1:] 
    )

DB_POOL = init_db_pool()

def get_conn():
    return DB_POOL.getconn()

def release_conn(conn):
    if conn:
        DB_POOL.putconn(conn)

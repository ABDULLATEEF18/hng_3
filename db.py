# db.py
import psycopg2
from psycopg2 import pool
import os

DB_POOL = None

def init_db_pool():
    global DB_POOL
    DB_POOL = pool.SimpleConnectionPool(
        1, 10,
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def get_db_connection():
    return DB_POOL.getconn()

def release_db_connection(conn):
    DB_POOL.putconn(conn)

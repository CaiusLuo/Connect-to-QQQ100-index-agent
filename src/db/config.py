import os

import psycopg

from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "dbname": os.getenv("PG_DBNAME"),
    "user": "tg_user",
    "password": os.getenv("PG_PWD"),
}

def get_conn():
    return psycopg.connect(
        host=DB_CONFIG.get["host"],
        port=DB_CONFIG.get["port"],
        dbname=DB_CONFIG.get["dbname"],
        user=DB_CONFIG.get["user"],
        password=DB_CONFIG.get["password"],
    )
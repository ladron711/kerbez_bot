import sqlite3

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR/"data"
DB_PATH = DATA_DIR/"gos_zakup.db"
MODELS_SQL = BASE_DIR/"src"/"db"/"models.sql"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    with MODELS_SQL.open(encoding="utf-8") as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()


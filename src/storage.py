import csv
from pathlib import Path

from src.config import SEEN_IDS_FILE
from src.parser.logger import log
from src.db.database import get_connection
from src.bot.bot_filters import is_active


def save_to_db(lots: list[dict]) -> None:
    
    if not lots:
        log("[storage] no data to save")
        return
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT INTO lots(
            lot_code,
            title,
            customer,
            price,
            method,
            status,
            start_date,
            end_date,
            link,
            created_at,
            updated_at)
        VALUES(
            :lot_code,
            :title,
            :customer,
            :price,
            :method,
            :status,
            :start_date,
            :end_date,
            :link,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP)
        ON CONFLICT(lot_code) DO UPDATE SET
            title = excluded.title,
            customer = excluded.customer,
            price = excluded.price,
            method = excluded.method,
            status = excluded.status,
            start_date = excluded.start_date,
            end_date = excluded.end_date,
            link = excluded.link,
            updated_at = CURRENT_TIMESTAMP
    """, lots)

    conn.commit()
    conn.close()

    log(f"[storage] saved {len(lots)} lots to DB")
    
   

def load_seen_ids(path=SEEN_IDS_FILE) -> set[str]:
    try:
        with open(path, "r") as f:
            return set(line.strip() for line in f if line.strip())
        
    except FileNotFoundError:
        log("[storage] file not found")
        return set()
    
    
def save_seen_ids(seen_ids: set[str], path=SEEN_IDS_FILE):
    with open(path, "w", encoding="utf-8") as f:
        for lot_code in sorted(seen_ids):
            f.write(lot_code + "\n")


def get_all_lots() -> list[tuple]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            lot_code,
            title,
            customer,
            price,
            end_date,
            link
        FROM lots
        WHERE end_date IS NOT NULL
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def export_to_csv(file_path: Path, only_active: bool = True) -> Path:
    lots = get_all_lots()

    if only_active:
        lots = [
            lot for lot in lots
            if is_active(lot[4])
        ]
    
    headers = [
        "lot_code",
        "title", 
        "customer",
        "price",
        "end_date",
        "link",
    ]


    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
        writer =  csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(lots)

    return file_path
        

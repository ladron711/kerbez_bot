from datetime import datetime, date

from src.bot.bot_logger import log


def is_active(end_date_str: str) -> bool:
    if not end_date_str:
        return False 
    
    try:
        end_date_active = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S").date()
        return end_date_active >= date.today()
    except ValueError as e:
        log(f"[bot_filters] invalid end_date format {e}")
        return False
        
        

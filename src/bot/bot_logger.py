from pathlib import Path
from datetime import datetime
from src.config import BASE_DIR


LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_BOT_FILE = LOG_DIR / "bot.log"


def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"

    print(line)

    with open(LOG_BOT_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
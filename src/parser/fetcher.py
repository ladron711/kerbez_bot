import requests
import time

from src.config import BASE_URL, HEADERS
from src.parser.logger import log


session = requests.Session()
session.headers.update(HEADERS)

def warm_up():
    try:
        session.get(BASE_URL, timeout=20)
        time.sleep(2)

    except requests.RequestException:
        log("[fetcher] error exeption def warm_up")
        pass

def fetch_page(url:str, params:dict | None = None, retries: int = 3) ->str | None:
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            log(f"[fetcher] fetch {attempt}/{retries}] error: {e}")
            time.sleep(3 * attempt)

    return None




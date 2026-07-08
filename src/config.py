import os

from datetime import date
from pathlib import Path
from dotenv import load_dotenv  


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR /".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

USER_IDS = [int(user) for user in os.getenv("USERS").split(',')]

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment")


BASE_URL = "https://goszakup.gov.kz"

KATO_ASTANA = "710000000"

COUNT_RECORD = 50
TODAY = date.today().strftime("%d.%m.%Y")

PARAMS = {
            "count_record": COUNT_RECORD,
            "filter[kato]": KATO_ASTANA,
            "filter[end_date_from]": TODAY,
            "filter[status][]": [220, 230, 210, 240],
            "filter[method][]": [3, 2, 7, 77, 78, 32, 22, 124, 190, 126, 128, 177, 188, 130, 200],
        } 


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}


KEYWORDS = [
    "пошив",
    "ткан",
    "текстил",
    "швейн",
    "куртк",
    "курток",
    "платье",
    "платья",
    "юбк",
    "юбок",
    "брюк",
    "жилет",
    "халат",
    "фартук",
    "пальто",
    "польт",
    "плащ",
    "рубаш",
    "фураж",
    "формен",
    "штор",
    "одежд",
    "кител",
    "спецодежд",
    "костюм",
    "наряд",
    "обмундиров",
    "униформ",
]








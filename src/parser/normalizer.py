import re

from datetime import datetime
from src.config import BASE_URL


def extract_announce_id(link: str) -> str | None:
    if not link:
        return None
    
    match = re.search(r"/announce/index/(\d+)", link)
    if not match:
        return None
    
    return match.group(1)


def normalize_price(price: str | None) -> float | None:
    if not price:
        return None
    
    cleaned = price.replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None
    

def normalize_link(link: str | None) -> str | None:
    if not link:
        return None
    
    if link.startswith("http"):
        return link
    
    return BASE_URL + link


def normalize_customer(customer: str | None) -> str | None:
    if not customer:
        return None
    
    return customer.replace("Заказчик:", "").strip()


def normalize_data(lot: dict) -> dict:
    normalized_link = normalize_link(lot.get("link"))
    return {
        **lot,
        "price": normalize_price(lot.get("price")),
        "link": normalized_link,
        "customer": normalize_customer(lot.get("customer")),
        "announce_id": extract_announce_id(normalized_link),
    }








from bs4 import BeautifulSoup
from src.parser.logger import log


def parse_data(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    table = soup.find("table", id="search-result")
    if not table:
        log("[normalizer] table not found")
        return []
    
    tbody = table.find("tbody")
    if not tbody:
        log("[normalizer] tbody not found")
        return []
    
    rows = tbody.find_all("tr")

    lots = []

    for row in rows:

        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        lot_code = cols[0].get_text(strip=True)
        if not lot_code:
            continue

        link_tag = cols[1].find("a")
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        link = link_tag.get("href")

        customer_tag = cols[1].find("small")
        customer = (customer_tag.get_text(strip=True) if customer_tag else None)

        price_tag = cols[4].find("strong")
        price = (price_tag.get_text(strip=True) if price_tag else None)
        
        method = cols[5].get_text(strip=True)
        if not method:
            continue

        lots.append(
            {
                "lot_code": lot_code,
                "title": title,
                "link": link,
                "customer": customer,
                "price": price,
                "method": method,
            }
        )
    
    return lots
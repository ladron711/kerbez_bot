from bs4 import BeautifulSoup


class InvalidSearchPage(ValueError):
    """The response cannot be interpreted as a search results page."""


def parse_data(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    table = soup.find("table", id="search-result")
    if not table:
        raise InvalidSearchPage("search-result table not found")
    
    tbody = table.find("tbody")
    if not tbody:
        raise InvalidSearchPage("search-result tbody not found")
    
    rows = tbody.find_all("tr")

    lots = []

    for row in rows:

        cols = row.find_all("td")
        if len(cols) < 6:
            raise InvalidSearchPage("result row has fewer than six columns")

        lot_code = cols[0].get_text(strip=True)
        if not lot_code:
            raise InvalidSearchPage("result row has no lot code")

        link_tag = cols[1].find("a")
        if not link_tag or not link_tag.get("href"):
            raise InvalidSearchPage("result row has no link")

        title = link_tag.get_text(strip=True)
        link = link_tag.get("href")

        customer_tag = cols[1].find("small")
        customer = (customer_tag.get_text(strip=True) if customer_tag else None)

        lot_name_tag = cols[2].find("strong")
        lot_name = (lot_name_tag.get_text(strip=True) if lot_name_tag else None)

        price_tag = cols[4].find("strong")
        price = (price_tag.get_text(strip=True) if price_tag else None)
        
        method = cols[5].get_text(strip=True)
        if not method:
            raise InvalidSearchPage("result row has no method")

        lots.append(
            {
                "lot_code": lot_code,
                "title": title,
                "lot_name": lot_name,
                "link": link,
                "customer": customer,
                "price": price,
                "method": method,
            }
        )
    
    return lots

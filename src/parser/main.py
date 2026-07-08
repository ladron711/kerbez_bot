import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from src.parser.fetcher import fetch_page, warm_up
from src.parser.parser import parse_data
from src.parser.normalizer import normalize_data
from src.parser.filters import filter_lots 
from src.parser.card_parser import parse_date_end
from src.config import PARAMS, KEYWORDS
from src.parser.logger import log


def fetch_end_date(lot: dict) -> dict:
    html = fetch_page(lot["link"])
    if not html:
        return lot

    lot["end_date"] = parse_date_end(html)
    return lot


def main():
    log("[main] start parsing")
    warm_up()

    page = 1

    normalized_lots = []

    while True:
        params = PARAMS.copy()
        params["page"] = page

        html = fetch_page("https://goszakup.gov.kz/ru/search/lots", params=params)

        if not html:
            log("[main] server error -> stop")
            break

        lots = parse_data(html)
        
        
        if not lots:
            log("[main] no more lots -> stop")
            break

        for lot in lots:
            normalized_lots.append(normalize_data(lot))

        page += 1
        time.sleep(2)

    if not normalized_lots:
        log("[main] no normalized lots found")
        return
    
    filtered_lots = filter_lots(normalized_lots, keywords=KEYWORDS)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_end_date, lot) for lot in filtered_lots]
        for future in as_completed(futures):
            try:
                lot = future.result()
            except Exception as e:
                log(f"[main] error occurred while fetching end date for lot: {e}")

    return filtered_lots


if __name__ == "__main__":
    main()
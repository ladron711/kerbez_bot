import time


from src.parser.fetcher import fetch_page, warm_up
from src.parser.parser import parse_data
from src.parser.normalizer import normalize_data
from src.parser.filters import filter_lots 
from src.storage import save_to_db, load_seen_ids, save_seen_ids
from src.parser.card_parser import parse_lot_status, parse_date_start, parse_date_end
from src.config import PARAMS, KEYWORDS, FULL_SCAN
from src.parser.logger import log


def main():
    log("[main] start parsing")
    warm_up()

    seen_ids: set[str] = load_seen_ids()
    new_lots: list[dict] = []

    page = 1

    while True:
        params = PARAMS.copy()
        params["page"] = page

        log(f"[main] page {page} downloaded")
        html = fetch_page("https://goszakup.gov.kz/ru/search/lots", params=params)

        if not html:
            log("[main] server error -> stop")
            break

        lots = parse_data(html)
        log(f"[main] found on page: {len(lots)}")
       
        if not lots:
            break

        all_known = True

        for lot in lots:
            normalized = normalize_data(lot)
            lot_code = normalized.get("lot_code")

            if not lot_code:
                continue
            
            already_seen = lot_code in seen_ids

            if not already_seen:
                all_known = False

            seen_ids.add(lot_code)

            if not FULL_SCAN and already_seen:
                continue

            new_lots.append(normalized)


        if not FULL_SCAN and all_known:
            log("[main] all lots on page already known -> stop parsing")
            break

        page += 1
        time.sleep(2)


    log(f"[main] \nnew lots collected: {len(new_lots)}")


    if not new_lots:
        log("[main] no new lots -> exit")
        return
    
    filtered_lots = filter_lots(new_lots, keywords=KEYWORDS)
    log(f"[main] after keyword filter: {len(filtered_lots)}")

    for i, lot in enumerate(filtered_lots, start=1):
        log(f"[main] [card {i}/{len(filtered_lots)}] {lot['lot_code']}")

        html = fetch_page(lot["link"])
        if not html:
            continue

        lot["status"] = parse_lot_status(html)
        lot["start_date"] = parse_date_start(html)
        lot["end_date"] = parse_date_end(html)

        time.sleep(1)

    active_lots = filter_lots(filtered_lots, only_active=True)
    log(f"[main] active lots: {len(active_lots)}")

    save_to_db(active_lots)
    save_seen_ids(seen_ids)
    log("[main]===parser finished successfully ===")


if __name__ == "__main__":
    main()
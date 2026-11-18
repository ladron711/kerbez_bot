import time
from dataclasses import dataclass, field
from typing import Literal

from concurrent.futures import ThreadPoolExecutor, as_completed
from src.parser.fetcher import fetch_page, warm_up
from src.parser.parser import InvalidSearchPage, parse_data
from src.parser.normalizer import normalize_data
from src.parser.filters import filter_lots
from src.parser.card_parser import parse_date_end
from src.config import PARAMS, KEYWORDS, BASE_URL
from src.parser.logger import log


@dataclass
class ParseResult:
    lots: list[dict] = field(default_factory=list)
    status: Literal["success", "partial", "error"] = "success"
    found: int = 0
    filtered: int = 0
    processed: int = 0
    load_errors: int = 0
    parse_errors: int = 0
    failed_page: int | None = None


class CardLoadError(RuntimeError):
    pass


def fetch_end_date(lot: dict) -> dict:
    html = fetch_page(lot["link"])
    if not html:
        raise CardLoadError(f"card not loaded: {lot['link']}")
    lot["end_date"] = parse_date_end(html)
    if not lot["end_date"]:
        raise ValueError(f"end date not found: {lot['link']}")
    return lot


def main() -> ParseResult:
    log("[main] start parsing")
    result = ParseResult()
    normalized_lots = []
    try:
        warm_up()
        page = 1
        while True:
            params = PARAMS.copy()
            params["page"] = page
            html = fetch_page(f"{BASE_URL}/ru/search/lots", params=params)
            if not html:
                result.load_errors += 1
                result.failed_page = page
                log(f"[main] search page {page} not loaded; incomplete result")
                break
            try:
                lots = parse_data(html)
            except InvalidSearchPage as e:
                result.parse_errors += 1
                result.failed_page = page
                log(f"[main] invalid search page {page}: {e}")
                break
            if not lots:
                log("[main] no more lots -> stop")
                break
            result.found += len(lots)
            normalized_lots.extend(normalize_data(lot) for lot in lots)
            page += 1
            time.sleep(2)

        result.lots = filter_lots(normalized_lots, keywords=KEYWORDS)
        result.filtered = len(result.lots)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_end_date, lot): lot for lot in result.lots}
            for future in as_completed(futures):
                try:
                    future.result()
                    result.processed += 1
                except CardLoadError as e:
                    result.load_errors += 1
                    log(f"[main] {e}")
                except Exception as e:
                    result.parse_errors += 1
                    log(f"[main] card {futures[future].get('lot_code')} error: {e}")
        if result.load_errors or result.parse_errors:
            result.status = "partial" if result.found else "error"
        return result
    except Exception:
        result.status = "error"
        result.parse_errors += 1
        raise
    finally:
        log(
            f"[main] summary status={result.status} found={result.found} "
            f"filtered={result.filtered} processed={result.processed} "
            f"load_errors={result.load_errors} parse_errors={result.parse_errors} "
            f"failed_page={result.failed_page}"
        )


if __name__ == "__main__":
    main()



def filter_lots(
    lots: list[dict],
    keywords: list[str] | None = None,
) -> list[dict]:
    

    result = []

    for lot in lots:

        if keywords:
            title = lot.get("title", "").lower()
            lot_name = (lot.get("lot_name") or "").lower()
            if not any(word.lower() in title or word.lower() in lot_name for word in keywords):
                continue

        result.append(lot)

    return result
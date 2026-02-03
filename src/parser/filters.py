

def filter_lots(
    lots: list[dict],
    keywords: list[str] | None = None,
    method: str | None = None,
    only_active: bool = False,
) -> list[dict]:
    
    inactive_keywords = [
        "заверш",
        "состоя",
        "изменен",
        "протокол",
        "качеств",
        "отмен",
        "обжалов",
        "заполн",
        "отказ",
        "пересмотр",
        "останов",
        "итог",
        "решен",
    ]

    result = []

    for lot in lots:

        if keywords:
            title = lot.get("title", "").lower()
            if not any(word.lower() in title for word in keywords):
                continue
    
        if method:
            if lot.get("method") != method:
                continue

        if only_active:
            status = lot.get("status")
            if not status:
                continue

            status_lower = status.lower()
            if any(word in status_lower for word in inactive_keywords):
                continue

        result.append(lot)

    return result
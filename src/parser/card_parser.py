from bs4 import BeautifulSoup


def parse_lot_status(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")

    label = soup.find("label", string="Статус объявления")
    if not label:
        return None
    
    container = label.find_parent("div", class_="form-group")
    if not container:
        return None
    
    input_tag = container.find("input", class_="form-control")
    if not input_tag:
        return None
    
    return input_tag.get("value", "").strip()


def parse_date_start(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")

    label = soup.find("label", string="Дата публикации объявления")
    if not label:
        return None
    
    container = label.find_parent("div", class_="form-group")
    if not container:
        return None
    
    input_tag = container.find("input", class_="form-control")
    if not input_tag:
        return None
    
    return input_tag.get("value", "").strip()


def parse_date_end(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")

    keywords = [
        "срок окончания",
    ]

    for label in soup.find_all("label"):
        text = label.get_text(strip=True).lower()

        if not any(keyword in text for keyword in keywords):
            continue
             
        container = label.find_parent("div", class_="form-group")
        if not container:
            continue
    
        input_tag = container.find("input", class_="form-control")
        if input_tag and input_tag.get("value"):
            return input_tag["value"].strip()
        
    return None


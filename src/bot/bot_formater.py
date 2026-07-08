from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def format_lot(lot: dict) -> str:
    return(
        f"🆔 {lot['lot_code']}\n"
        f"🎯 {lot['title']}\n"
        f"🖍 {lot.get('lot_name') or ''}\n"
        f"💰 {lot['price']} тг.\n"
        f"🗿 {lot['customer']}\n"
        f"📅 лот завершится: {lot.get('end_date') or ''}\n"
        f"-🔗 {lot['link']}\n"
        f"------------"
    )

main_keyboard = ReplyKeyboardMarkup(keyboard = [[KeyboardButton(text="🔄 поиск лотов")]], resize_keyboard=True,)
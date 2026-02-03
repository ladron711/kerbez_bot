from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def format_lot(lot: tuple) -> str:
    return(
        f"🆔 {lot[0]}\n"
        f"🎯 {lot[1]}\n"
        f"💰 {lot[3]} тг.\n"
        f"🗿 {lot[2]}\n"
        f"📅 лот завершится: {lot[4]}\n"
        f"-🔗 {lot[5]}\n"
        f"------------"
    )

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 поиск лотов")],
        [KeyboardButton(text="📄 Скачать CSV")],
    ],
    resize_keyboard=True
    
)
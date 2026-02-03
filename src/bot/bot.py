import os
import asyncio
from datetime import date
from pathlib import Path


from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile


from src.parser.main import main as run_parser
from src.bot.bot_filters import is_active
from src.storage import get_all_lots, export_to_csv
from src.bot.bot_formater import format_lot, main_keyboard
from src.bot.bot_logger import log
from src.config import BOT_TOKEN


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def help(message: Message):
    await message.answer("Приветствую, выберите действие", reply_markup=main_keyboard)


@dp.message(lambda message: message.text == "🔄 поиск лотов")
async def parse_button(message: Message):
    await message.answer("начинаю поиск")

    try:
        run_parser()
        await message.answer("поиск завершен")
        try:
            lots = get_all_lots()
            active_lots = [lot for lot in lots
            if is_active(lot[4])]
        
            if not active_lots:
                await message.answer("❌ Нет активных лотов")

                return
                
            for lot in active_lots:
                await message.answer(format_lot(lot))
            
            log("[bot] lots are formed")

        except Exception as e:
            await message.answer("ошибка попробуйте позже")
            log(f"[bot] error by getting lots from DB as {e}")
    
    except Exception as e:
        await message.answer("ошибка, повторите позже")  
        log(f"[bot] error by parser running as {e}")


@dp.message(lambda message: message.text == "📄 Скачать CSV")
async def csv_button(message: Message):
    file_path = Path("data/lots.csv")
    
    try:
        export_to_csv(file_path)

        if not file_path.exists():
            await message.answer("❌ Файл с лотами не найден")
            return
        await message.answer_document(document = FSInputFile(file_path), caption = "📄 Лоты (CSV файл)")
        log(f"[bot] CSV is formed")
    
    except Exception as e:
        await message.answer("Произошла ошибка при формировании файла")
        log(f"[bot] error by export to CSV as {e}")
    

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
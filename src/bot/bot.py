import asyncio
from pathlib import Path
import signal


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

parser_running = False

PARSER_TIMEOUT = 1800


@dp.message(Command("start"))
async def help(message: Message):
    await message.answer("Приветствую, выберите действие", reply_markup=main_keyboard)


@dp.message(lambda message: message.text == "🔄 поиск лотов")
async def parse_button(message: Message):
    global parser_running

    if parser_running:
        await message.answer("поиск уже запущен, подождите")
        return
    
    parser_running = True
    await message.answer("поиск лотов ⏳")


    try:
        await asyncio.wait_for(asyncio.to_thread(run_parser), timeout=PARSER_TIMEOUT)
        await message.answer("поиск завершен")
            
        lots = get_all_lots()
        active_lots = [lot for lot in lots
        if is_active(lot[4])]
            
        if not active_lots:
            await message.answer("❌ Нет активных лотов")
            return
                    
        for lot in active_lots:
            await message.answer(format_lot(lot))

    except asyncio.TimeoutError:
        await message.answer("ошибка попробуйте позже")
        log(f"[bot] error by timeout of parser")
    
    except Exception as e:
        await message.answer("ошибка, повторите позже")  
        log(f"[bot] error by parser running as {e}")
    
    finally:
        parser_running = False


@dp.message(lambda message: message.text == "📄 Скачать CSV")
async def csv_button(message: Message):
    file_path = Path("data/lots.csv")
    
    try:
        export_to_csv(file_path)

        if not file_path.exists():
            await message.answer("❌ Файл с лотами не найден")
            return
        await message.answer_document(document = FSInputFile(file_path), caption = "📄 Лоты (CSV файл)")
    
    except Exception as e:
        await message.answer("Произошла ошибка при формировании файла")
        log(f"[bot] error by export to CSV as {e}")
    

async def shutdown():
    log("[bot] Shutting down...")
    await bot.session.close()


async def main():
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    log("[bot] Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        log(f"[bot] error by running bot as {e}")
        raise



import asyncio
import signal

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import Message

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.parser.main import main as run_parser
from src.bot.bot_formater import format_lot, main_keyboard
from src.bot.bot_logger import log
from src.config import BOT_TOKEN, USER_IDS


class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        if event.from_user.id not in USER_IDS:
            return
        return await handler(event, data)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(AccessMiddleware())

PARSER_TIMEOUT = 1800

parser_task: asyncio.Task | None = None


async def _run_parser_once() -> list[dict] | None:
    try:
        return await asyncio.wait_for(asyncio.to_thread(run_parser), timeout=PARSER_TIMEOUT)
    except asyncio.TimeoutError:
        log("[bot] error by timeout of parser")
        return None


async def run_parser_safe() -> list[dict] | None:
    global parser_task

    if parser_task is None or parser_task.done():
        parser_task = asyncio.create_task(_run_parser_once())

    try:
        return await parser_task
    except Exception as e:
        log(f"[bot] error while awaiting parser task: {e}")
        return None


@dp.message(Command("start"))
async def help(message: Message):
    await message.answer("Приветствую, выберите действие", reply_markup=main_keyboard)


@dp.message(lambda message: message.text == "🔄 поиск лотов")
async def parse_button(message: Message):
    try:
        await message.answer("поиск лотов ⏳")
        lots = await run_parser_safe()

        if lots is None:
            await message.answer("ошибка, повторите позже")
            return

        if not lots:
            await message.answer("❌ Нет активных лотов")
            return

        for lot in lots:
            await message.answer(format_lot(lot))

    except Exception as e:
        await message.answer("ошибка, повторите позже")
        log(f"[bot] error by parser running as {e}")


async def auto_parse():
    lots = await run_parser_safe()

    if lots is None:
        log("[scheduler] parser error, skip broadcast")
        return

    if not lots:
        log("[scheduler] no active lots found, skip broadcast")
        return

    for user_id in USER_IDS:
        for lot in lots:
            await bot.send_message(user_id, format_lot(lot))


scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
scheduler.add_job(auto_parse, "cron", hour=11, minute=3)


async def shutdown():
    log("[bot] Shutting down...")
    await bot.session.close()


async def main():
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    scheduler.start()

    for user_id in USER_IDS:
        try:
            await bot.send_message(user_id, "Bot started")
        except Exception as e:
            log(f"[bot] failed to notify {user_id} on startup: {e}")

    log("[bot] Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        log(f"[bot] error by running bot as {e}")
        raise
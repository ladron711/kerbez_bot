import asyncio
import signal

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import Message

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.parser.main import ParseResult, main as run_parser
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


async def _run_parser_once() -> ParseResult | None:
    try:
        return await asyncio.wait_for(asyncio.to_thread(run_parser), timeout=PARSER_TIMEOUT)
    except asyncio.TimeoutError:
        log("[bot] error by timeout of parser")
        return None


async def run_parser_safe() -> ParseResult | None:
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


async def send_lots(lots: list[dict], recipients: list, send, source: str):
    sent = failed = 0
    try:
        for recipient in recipients:
            for lot in lots:
                try:
                    await send(recipient, format_lot(lot))
                    sent += 1
                except Exception as e:
                    failed += 1
                    log(f"[{source}] send error recipient={recipient} "
                        f"lot={lot.get('lot_code')}: {e}")
    finally:
        log(f"[{source}] summary sent={sent} failed={failed}")
    return sent, failed


async def answer_safe(message: Message, text: str):
    try:
        await message.answer(text)
    except Exception as e:
        log(f"[bot] notification error: {e}")


@dp.message(lambda message: message.text == "🔄 поиск лотов")
async def parse_button(message: Message):
    await answer_safe(message, "поиск лотов ⏳")
    result = await run_parser_safe()
    if result is None or result.status == "error":
        log("[bot] summary sent=0 failed=0; parser error")
        await answer_safe(message, "ошибка, повторите позже")
        return
    if result.status == "partial":
        await answer_safe(message, "⚠️ Результат неполный: часть данных не удалось получить. Повторите поиск позже.")
    elif not result.lots:
        await answer_safe(message, "❌ Нет активных лотов")

    async def send(_recipient, text):
        await message.answer(text)

    await send_lots(result.lots, [message.chat.id], send, "bot")


async def auto_parse():
    result = await run_parser_safe()
    if result is None or result.status == "error":
        log("[scheduler] summary sent=0 failed=0; parser error, skip broadcast")
        return
    if result.status == "partial":
        log("[scheduler] incomplete parser result; broadcasting available lots")
        for user_id in USER_IDS:
            try:
                await bot.send_message(user_id, "⚠️ Результат неполный: часть данных не удалось получить. Повторите поиск позже.")
            except Exception as e:
                log(f"[scheduler] notification error recipient={user_id}: {e}")
    await send_lots(result.lots, USER_IDS, bot.send_message, "scheduler")


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
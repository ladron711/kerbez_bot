# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Telegram bot (aiogram v3) that scrapes Kazakhstan's public procurement portal
`BASE_URL` for active lots matching clothing/textile/uniform keywords and
pushes them to a fixed allowlist of Telegram users, both on demand and on a daily
schedule.

## Commands

```bash
pip install -r requirements.txt        # deps (no venv tooling committed)

python -m src.bot.bot                   # run the bot (from repo root; requires .env)
python -m src.parser.main               # run the scraper standalone, no Telegram

docker compose up --build              # run in Docker (CMD is: python3 -m src.bot.bot)
docker compose up -d
```

There are no tests, linter, or formatter configured in this repo.

**Always run modules with `python -m` from the repo root.** Every import is
absolute from the `src` package (`from src.parser.main import ...`), so
`python src/bot/bot.py` — as the README states — will fail with import errors.

## Environment

`src/config.py` calls `load_dotenv(BASE_DIR/".env")` and reads:

- `BOT_TOKEN` — from @BotFather; missing value raises `RuntimeError` at import.
- `USERS` — comma-separated Telegram user IDs. Missing value raises
  `AttributeError` at import (`None.split`). This is the access allowlist and the
  broadcast target list; there is no runtime subscription mechanism.

## Architecture

Two independent subsystems under `src/`, wired together only at
`src/bot/bot.py` importing `src.parser.main.main`.

### `src/parser/` — synchronous scrape pipeline

`main()` is the entry point and returns `list[dict]` of lots, or `None` on
failure / when nothing was scraped (callers must treat `None` as an error, not
empty). Pipeline:

1. `fetcher.warm_up()` — one GET to `BASE_URL` to seed the shared
   `requests.Session` (cookies). All fetches reuse this module-level session.
2. Paginate `fetcher.fetch_page("/ru/search/lots", params)` with `PARAMS` from
   config plus an incrementing `page`. `fetch_page` retries 3x with linear
   backoff; returns `None` on give-up, which stops pagination.
3. `parser.parse_data(html)` — BeautifulSoup (`lxml`) over `table#search-result`,
   positional `<td>` indexing. Any layout change on the portal breaks this.
4. `normalizer.normalize_data` per row — price → float, relative link →
   absolute, strips `"Заказчик:"`, extracts `announce_id` via regex.
5. `filters.filter_lots(lots, keywords=KEYWORDS)` — keeps a lot only if any
   keyword is a substring of `title` or `lot_name` (case-insensitive). Keywords
   are Russian word stems, so `"куртк"` matches куртка/куртки/курток.
6. `ThreadPoolExecutor(max_workers=5)` runs `fetch_end_date` per surviving lot:
   fetches the lot's card page and `card_parser.parse_date_end` reads the
   "срок окончания" input value. Mutates each lot dict in place with `end_date`.

### `src/bot/` — aiogram v3 async bot

- `AccessMiddleware` on `dp.message` drops any update whose `from_user.id` is not
  in `USER_IDS` (silent).
- The blocking parser runs via `asyncio.to_thread(run_parser)` wrapped in
  `asyncio.wait_for(timeout=PARSER_TIMEOUT=1800)`.
- `run_parser_safe()` keeps a single module-level `parser_task`; concurrent
  triggers (the button + the scheduler) await the *same* run rather than
  starting a second scrape.
- Triggers: `/start` shows the keyboard; the `"🔄 поиск лотов"` reply-keyboard
  button scrapes and replies lot-by-lot to the requester; `AsyncIOScheduler`
  cron job `auto_parse` at 11:03 `Asia/Almaty` scrapes and broadcasts to every
  `USER_IDS`. On startup every user gets a "Bot started" message.
- `bot_formater.format_lot` defines the exact dict keys consumed downstream:
  `lot_code, title, lot_name, price, customer, end_date, link`.

### Config is the single source of scrape behavior

`src/config.py` holds `PARAMS` (region `KATO_ASTANA`, status/method code lists,
`end_date_from` = today), `HEADERS`, `BASE_URL`, and `KEYWORDS`. `TODAY` is
frozen at import time, so a long-running process keeps yesterday's date until
restarted. To change *what* gets scraped or matched, edit this file — not the
parser modules.

## Notes

- The `README.md` is stale: it describes `src/db/`, `src/storage.py`,
  `bot_filters.py`, CSV export, and SQLite dedup that do not exist in the code.
  `.gitignore` entries for `*.sqlite3` / `saved_lots_ids.txt` / `data/` are
  likewise leftovers — there is currently no persistence or seen-lot
  deduplication, so scheduled runs resend lots that are still active.
- `src/parser/logger.py` and `src/bot/bot_logger.py` are two separate copies of
  the same timestamped-`print` helper.

# Kerbez Bot

A Telegram bot that scrapes the Kazakhstan public procurement portal
[goszakup.gov.kz](https://goszakup.gov.kz/) for active lots matching a fixed set
of clothing / textile / uniform keywords and delivers them to an allowlist of
Telegram users — on demand and once a day on a schedule.

## Stack

**Scraper:** Python, Requests, BeautifulSoup4 (`lxml`)
**Bot:** Python, aiogram v3, APScheduler
**Deploy:** Docker / Linux server

There is no database. The bot holds no state between runs and does not
deduplicate lots — a scheduled run resends any lot that is still active.

## Features

- Scrapes `goszakup.gov.kz/ru/search/lots` for active lots, filtered server-side
  by region (Astana), status and procurement method (see `PARAMS` in
  `src/config.py`).
- Keeps only lots whose title or name contains one of the keyword stems in
  `KEYWORDS` (`src/config.py`).
- For each matching lot, fetches its card page to read the bidding end date.
- Sends each lot to Telegram: lot code, title, lot name, price, customer, end
  date and link (`src/bot/bot_formater.py`).
- Access is restricted to the Telegram user IDs listed in the `USERS`
  environment variable.
- Daily broadcast to all allowed users at 11:03 `Asia/Almaty`.

## Project Structure

```
kerbez_pars_bot/
├── src/
│   ├── config.py            # BOT_TOKEN/USERS loading, scrape PARAMS, HEADERS, KEYWORDS
│   ├── bot/
│   │   ├── bot.py           # aiogram entry point, access middleware, scheduler
│   │   ├── bot_formater.py  # lot message formatting + reply keyboard
│   │   └── bot_logger.py    # timestamped print logger
│   └── parser/
│       ├── main.py          # scrape pipeline orchestrator, returns list[dict] | None
│       ├── fetcher.py       # shared requests.Session, warm-up, retrying GET
│       ├── parser.py        # BeautifulSoup parsing of the search-result table
│       ├── normalizer.py    # price/link/customer cleanup, announce_id extraction
│       ├── filters.py       # keyword filtering
│       ├── card_parser.py   # reads "срок окончания" (end date) from a lot card
│       └── logger.py        # timestamped print logger
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Environment Variables

Create a `.env` file in the repository root:

| Variable    | Description                                                        |
|-------------|------------------------------------------------------------------|
| `BOT_TOKEN` | Telegram bot token from @BotFather. Required.                     |
| `USERS`     | Comma-separated Telegram user IDs allowed to use the bot and to receive the daily broadcast, e.g. `12345678,87654321`. Required. |

Both variables are read at import time in `src/config.py`; the app will not start
if either is missing.

## Installation and Running

### Prerequisites

- Python 3.10+ (Docker image uses 3.12)
- Git

### Steps

1. Clone the repository

   ```bash
   git clone https://github.com/ladron711/kerbez_bot.git
   cd kerbez_bot
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Create the `.env` file (see [Environment Variables](#environment-variables)).

4. Run the bot from the repository root:

   ```bash
   python -m src.bot.bot
   ```

   All imports are absolute from the `src` package, so the bot must be started
   as a module from the repo root (`python src/bot/bot.py` will fail).

### Run the scraper without Telegram

```bash
python -m src.parser.main
```

Runs the full scrape pipeline and logs progress; useful for debugging selectors
and filters.

### Docker

```bash
docker compose up --build      # foreground
docker compose up -d           # detached
```

The container reads `.env` via `env_file` and runs `python3 -m src.bot.bot`.

## How It Works

1. `/start` shows a keyboard with a single button, **🔄 поиск лотов**.
2. Pressing the button (or the daily 11:03 `Asia/Almaty` scheduler) runs the
   scraper in a background thread with a 30-minute timeout. Concurrent triggers
   share the same run rather than starting a second scrape.
3. The scraper (`src/parser/main.py`):
   - warms up a `requests.Session`, then pages through the search results using
     `PARAMS` from `src/config.py`;
   - parses each results table row (`src/parser/parser.py`) and normalizes it
     (`src/parser/normalizer.py`);
   - filters lots by the `KEYWORDS` stems (`src/parser/filters.py`);
   - fetches each surviving lot's card page (5 worker threads) to extract the
     bidding end date (`src/parser/card_parser.py`).
4. Each lot is sent as a separate Telegram message. On a manual search the
   replies go to the requester; the scheduled run broadcasts to every ID in
   `USERS`.

To change **what** is scraped or matched, edit `src/config.py` (`PARAMS` and
`KEYWORDS`) — not the parser modules.

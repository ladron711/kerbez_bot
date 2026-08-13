# Kerbez Bot

A Telegram bot that monitors the public procurement website and shows currently active purchases matching configured filters.

## Stack

**Backend:** Python, BeautifulSoup4, Requests  
**Bot:** Python, aiogram, apscheduler  
**Infrastructure:** Docker, Docker Compose

## Features

- Automatically monitors [goszakup.gov.kz](https://goszakup.gov.kz/) for new purchases
- Returns only active lots matching configured filters
- Displays key information: name, sum, owner, and end date of each lot

## Project Structure

kerbez_pars_bot/
├── src/
│   ├── bot/
│   │   ├── bot.py             # Main function for bot and polling
│   │   ├── bot_formater.py    # Function for message format and keyboard
│   │   └── bot_logger.py      # Shows log messages with date
│   ├── parser/
│   │   ├── card_parser.py     # Function for getting end date of lot
│   │   ├── fetcher.py         # Warming up, creating Session, fetches a text of pages
│   │   ├── filters.py         # Function of search filters
│   │   ├── logger.py          # Shows log messages with date
│   │   ├── main.py            # Main parsing function
│   │   ├── normalizer.py      # Format function of data
│   │   └── parser.py          # Parsing of fetched data
│   └──config.py               # Configuration for bot and search parameters 
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
└── .env.example

## Environment Variables
Create a `.env` file in the root directory 

## Installation and Running

### Prerequisites

- Docker and Docker Compose installed on your server
- Git installed

### Steps
1. Clone the repository
```bash
git clone https://github.com/ladron711/kerbez_bot.git
cd kerbez_bot
```
2. Create `.env` file based on `.env.example` and fill in all variables

| Variable    | Description                          |
|-------------|--------------------------------------|
| `BOT_TOKEN` | Telegram bot token from @BotFather   |
| `USERS` | Telegram id of bot users |

3. Build and start containers
```bash
docker compose up --build -d
```
4. The bot is now running and ready to use

## How It Works

### Searching for purchases

- User starts the bot with `/start`
- Two options are available:
  - **Search purchases** — runs the parser and returns matching results
  - **Daily report at 11:03** — automatically message with parsed data
Search filters are hardcoded in `config.py`.
The bot parses the public procurement website and returns only active lots
that match the configured filters. For each lot the bot shows:
- Name of the purchase
- Total sum
- Owner of the purchase
- End date of the purchase

### Implementation notes

**Server-side filtering.** Lot status, city (KATO), and purchase method are
filtered via URL parameters on the source website, not after downloading —
so the parser only ever receives lots that are already relevant.

**Parallel detail fetching.** The end date of a lot is only available on its
individual page, not in the search results table. After keyword filtering,
the bot fetches these pages in parallel (up to 5 concurrent requests via
`ThreadPoolExecutor`) instead of sequentially. If a single request fails,
that lot is still returned — just without an end date — so one network
error doesn't break the entire search.

**Single-flight parsing.** If a user triggers a search while another one is
already running, the second request joins the in-progress task instead of
starting a duplicate crawl. This means the scheduled daily report will still
be delivered even if a manual search started moments before it.

**Stateless by design.** The bot stores nothing between runs — no database,
no seen-lot tracking. Every search returns a fresh snapshot of what is
currently open for bids.


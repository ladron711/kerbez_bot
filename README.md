# Kerbez Bot

A Telegram bot that monitors the public procurement website and notifies users
about new purchases matching their filters.

## Stack

**Backend:** Python, BeautifulSoup4, Requests  
**Bot:** Python, aiogram  
**Database:** SQLite3  
**Deploy:** Linux server  

## Features

- Automatically monitors [goszakup.gov.kz](https://goszakup.gov.kz/) for new purchases
- Returns only active lots matching configured filters
- Displays key information: name, sum, owner, and end date of each lot
- Exports results to a CSV file
- Filters are configurable in `parser/filters.py`

## Project Structure

kerbez_pars_bot/
├── src/
│   ├── bot/
│   │   ├── bot.py
│   │   ├── bot_filters.py
│   │   ├── bot_formater.py
│   │   └── bot_logger.py
│   ├── db/
│   │   ├── database.py
│   │   └── models.sql
│   ├── parser/
│   │   ├── card_parser.py
│   │   ├── fetcher.py
│   │   ├── filters.py
│   │   ├── logger.py
│   │   ├── main.py
│   │   ├── normalizer.py
│   │   └── parser.py
│   ├── config.py
│   └── storage.py
├── requirements.txt
└── .env.example

## Environment Variables

Create a `.env` file in the root directory with the following variables:

| Variable    | Description                          |
|-------------|--------------------------------------|
| `BOT_TOKEN` | Telegram bot token from @BotFather   |

## Installation and Running

### Prerequisites

- Python 3.10+
- Git

### Steps

1. Clone the repository

git clone https://github.com/your_username/kerbez_bot.git
cd kerbez_bot

2. Install dependencies

pip install -r requirements.txt

3. Create `.env` file in the root directory and fill in all variables
   from the [Environment Variables](#environment-variables) section

4. Run the bot

python src/bot/bot.py

## How It Works

### Searching for purchases

- User starts the bot with `/start`
- Two options are available:
  - **Search purchases** — runs the parser and returns matching results
  - **Save as CSV** — exports the found purchases to a CSV file
Search filters are hardcoded in `parser/filters.py`.
The bot parses the public procurement website and returns only active lots
that match the configured filters. For each lot the bot shows:
- Name of the purchase
- Total sum
- Owner of the purchase
- End date of the purchase

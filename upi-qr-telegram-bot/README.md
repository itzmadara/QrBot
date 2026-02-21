# UPI QR Telegram Bot (Pyrogram)

Telegram bot that generates a custom UPI QR code from user input:

`/qr <upi_id> <amount> [payee_name] [note]`

Example:

`/qr yourname@okaxis 149.99 John_Doe Order_42`

## 1) Prerequisites

- Python 3.11+
- Telegram Bot Token from `@BotFather`
- `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org)

## 2) Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set env vars in `.env`, then run:

```bash
export $(grep -v '^#' .env | xargs)
python bot.py
```

## 3) Heroku deploy

1. Create a new app on Heroku.
2. Connect your GitHub repo (or push via Heroku Git).
3. In Heroku app settings, set config vars:
   - `API_ID`
   - `API_HASH`
   - `BOT_TOKEN`
   - Optional: `DEFAULT_PAYEE_NAME`, `DEFAULT_NOTE`
4. Enable the `worker` dyno in **Resources**.
5. Deploy latest commit.

This project uses:
- `Procfile`: `worker: python bot.py`
- `runtime.txt`: Python runtime for Heroku
- `app.json`: deploy metadata and env schema

## 4) Bot usage

- `/start` to view instructions
- `/qr <upi_id> <amount> [payee_name] [note]`

Notes:
- UPI ID format is validated (`name@bank` style).
- Amount accepts positive values up to 2 decimals.
- Use underscores `_` for spaces in optional fields.

import logging
import os
import re
from io import BytesIO
from urllib.parse import quote

import qrcode
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("upi-qr-bot")


API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_PAYEE_NAME = os.getenv("DEFAULT_PAYEE_NAME", "UPI Payment")
DEFAULT_NOTE = os.getenv("DEFAULT_NOTE", "Payment")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Missing required env vars: API_ID, API_HASH, BOT_TOKEN")


UPI_ID_REGEX = re.compile(r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$")
AMOUNT_REGEX = re.compile(r"^\d+(\.\d{1,2})?$")


def is_valid_upi_id(upi_id: str) -> bool:
    return bool(UPI_ID_REGEX.match(upi_id))


def is_valid_amount(amount: str) -> bool:
    if not AMOUNT_REGEX.match(amount):
        return False
    return float(amount) > 0


def build_upi_link(upi_id: str, amount: str, payee_name: str, note: str) -> str:
    encoded_name = quote(payee_name.strip() or DEFAULT_PAYEE_NAME)
    encoded_note = quote(note.strip() or DEFAULT_NOTE)
    # BHIM is strict about `pa` and may reject percent-encoded `@` in UPI IDs.
    # Keep `pa` as plain VPA (name@bank) while encoding free-text fields.
    return (
        f"upi://pay?pa={upi_id}"
        f"&pn={encoded_name}"
        f"&am={amount}"
        f"&cu=INR"
        f"&tn={encoded_note}"
    )


def create_qr_image(data: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    buffer.name = "upi_qr.png"
    return buffer

def create_styled_qr(data: str, payee: str, amount: str) -> BytesIO:
    # Generate QR
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="#111111", back_color="white").convert("RGBA")
    qr_img = qr_img.resize((500, 500))

    # Create background card
    card = Image.new("RGBA", (700, 900), "#f4f6fb")
    draw = ImageDraw.Draw(card)

    # Draw white rounded box
    box = Image.new("RGBA", (640, 820), "white")
    card.paste(box, (30, 40))

    # Paste QR
    card.paste(qr_img, (100, 200))

    # Add text
    try:
        font_big = ImageFont.truetype("arial.ttf", 50)
        font_small = ImageFont.truetype("arial.ttf", 35)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((100, 80), payee, fill="black", font=font_big)
    draw.text((100, 750), f"INR {amount}", fill="#2e7d32", font=font_small)

    buffer = BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)
    buffer.name = "styled_upi_qr.png"
    return buffer


app = Client("upi-qr-bot", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def start_handler(_: Client, message: Message) -> None:
    help_text = (
        "Send:\n"
        "`/qr <upi_id> <amount> [payee_name] [note]`\n\n"
        "Examples:\n"
        "`/qr yourname@okaxis 149.99`\n"
        "`/qr yourname@okaxis 250 John_Doe Lunch`\n\n"
        "Tip: Use underscore (_) instead of spaces for payee name and note."
    )
    await message.reply_text(help_text, disable_web_page_preview=True)


@app.on_message(filters.command("qr"))
async def qr_handler(_: Client, message: Message) -> None:
    if len(message.command) < 3:
        await message.reply_text(
            "Invalid format.\nUse: `/qr <upi_id> <amount> [payee_name] [note]`"
        )
        return

    upi_id = message.command[1].strip()
    amount = message.command[2].strip()
    payee_name = (
        message.command[3].replace("_", " ")
        if len(message.command) >= 4
        else DEFAULT_PAYEE_NAME
    )
    note = message.command[4].replace("_", " ") if len(message.command) >= 5 else DEFAULT_NOTE

    if not is_valid_upi_id(upi_id):
        await message.reply_text(
            "Invalid UPI ID.\nExample valid format: `yourname@okaxis`"
        )
        return

    if not is_valid_amount(amount):
        await message.reply_text(
            "Invalid amount. Use a positive number with up to 2 decimals.\nExample: `149.99`"
        )
        return

    upi_link = build_upi_link(upi_id, amount, payee_name, note)
    image_buffer = create_styled_qr(upi_link, payee_name, amount)

    caption = (
        f"UPI QR Generated\n"
        f"`UPI ID:` `{upi_id}`\n"
        f"`Amount:` `INR {amount}`\n"
        f"`Payee:` `{payee_name}`\n"
        f"`Note:` `{note}`"
    )

    await message.reply_photo(photo=image_buffer, caption=caption)
    logger.info("Generated QR for user=%s upi=%s amount=%s", message.from_user.id, upi_id, amount)


if __name__ == "__main__":
    logger.info("Starting bot...")
    app.run()

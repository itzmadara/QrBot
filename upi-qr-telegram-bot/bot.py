import logging
import os
import re
from io import BytesIO
from urllib.parse import quote

import qrcode
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
from config import START_PHOTO, LOG_CHANNEL, OWNER_ID, START_MESSAGE
from db import is_user_new, save_user_to_db
from datetime import datetime, timezone, timedelta
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, PeerIdInvalid, UserIsBlocked

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("QrBot")


API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_PAYEE_NAME = os.getenv("DEFAULT_PAYEE_NAME", "UPI Payment")
DEFAULT_NOTE = os.getenv("DEFAULT_NOTE", "Payment")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Missing required env vars: API_ID, API_HASH, BOT_TOKEN")


UPI_ID_REGEX = re.compile(r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$")
AMOUNT_REGEX = re.compile(r"^\d+(\.\d{1,2})?$")
BOT_START_TIME = datetime.now()


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


@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    is_new = await is_user_new(user_id)
    await save_user_to_db(user_id, user_name)
    if is_new:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = (
            f"#NewUser\n"
            f"ID - {user_id}\n"
            f"Name - {user_name}\n"
            f"Date & Time - {current_time}\n"
            f"Database: MongoDB\n\n"
            f"Bot Username: @{client.me.username}"
        )
        try:
            await client.send_message(LOG_CHANNEL, log_message)
        except Exception as e:
            print(f"Failed to send log message: {e}")

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Dҽʋҽʅσρҽɾ", url="https://t.me/ItzMonkeyDLuffy"),
                InlineKeyboardButton("Hҽʅρ", callback_data="show_help"),
            ],
            [
                InlineKeyboardButton("Cԋαɳɳҽʅ", url="https://t.me/Anime_Station_Bots"),
            ]
        ]
    )
    await client.send_photo(
        chat_id=message.chat.id,
        photo=START_PHOTO,
        caption=START_MESSAGE.format(mention=message.from_user.mention),
        reply_markup=buttons
    )

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

@app.on_message(filters.command("help"))
async def help_handler(_: Client, message: Message) -> None:

    help_text = """
<emoji id="5445353829304387411">📘</emoji> <b>UPI QR Code Generator – Help Guide</b>

━━━━━━━━━━━━━━━  
<emoji id="5444856076954520455">🧾</emoji> <b>Command Format</b>


<code>/qr &lt;upi_id&gt; &lt;amount&gt; [payee_name] [note]</code>

━━━━━━━━━━━━━━━  
<emoji id="5397782960512444700">📌</emoji> <b>Parameters Explained</b>

• <b>&lt;upi_id&gt;</b> → Your valid UPI ID  
  Example: <code>yourname@okaxis</code>

• <b>&lt;amount&gt;</b> → Payment amount (positive number)  
  Example: <code>149.99</code>

• <b>[payee_name]</b> → Optional display name  
• <b>[note]</b> → Optional transaction note  

Use underscore (_) instead of spaces.

━━━━━━━━━━━━━━━  
<emoji id="6296367896398399651">✨</emoji> <b>Examples</b>

<code>/qr yourname@okaxis 199</code>  
<code>/qr yourname@okaxis 500 John_Doe Rent</code>  
<code>/qr merchant@upi 1499 Store_Payment Invoice_01</code>

━━━━━━━━━━━━━━━  
<emoji id="6298454498884978957">✨</emoji> <b>Features</b>
• Instant QR Code Generation  
• Secure UPI Payment Link  
• Custom Name & Note  
• Works with GPay, PhonePe, Paytm & BHIM  
• Clean & Scannable Design  

━━━━━━━━━━━━━━━  

Need help? Just send your <code>/qr</code> Get your QR instantly  
<emoji id="5382199784075448966">🚀</emoji>
"""

    await message.reply_text(
        help_text,
        disable_web_page_preview=True
    )


@app.on_message(filters.command("status"))
async def bot_status(client, message):
    # Calculate uptime
    uptime = str(datetime.now() - BOT_START_TIME).split('.')[0]
    
    # Calculate ping
    start = datetime.now()
    m = await message.reply_text("Pinging...")
    end = datetime.now()
    ping = (end - start).microseconds // 1000

    # Bot version
    version = "v1.1.2"

    # Send the status
    await m.edit_text(
        f"🐱 **Bᴏᴛ Sᴛᴀᴛᴜs:**\n\n"
        f"➲ **Bᴏᴛ Uᴘᴛɪᴍᴇ:** `{uptime}`\n"
        f"➲ **Pɪɴɢ:** `{ping}ms`\n"
        f"➲ **Vᴇʀsɪᴏɴ:** `{version}`"
    )

@app.on_message(filters.command("users") & filters.user(OWNER_ID))
async def users(client: Client, message: Message):
    user_count = await db.users.count_documents({})  # Count all users in the collection
    await message.reply(f"Total users: {user_count}")

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply("Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴏʀ ᴘᴏꜱᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪᴛ.")
        return

    broadcast_message = message.reply_to_message  # The message to broadcast
    users = db.users.find()  # Fetch all users from the database

    # Initialize counters
    total_users = 0
    successful = 0
    blocked_users = 0
    deleted_accounts = 0
    unsuccessful = 0

    # Send initial broadcast status
    status_message = await message.reply("**ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪꜱ ɪɴ ᴘʀᴏᴄᴇꜱꜱ...**\n\n"
                                         "Total Users: 0\n"
                                         "Successful: 0\n"
                                         "Blocked Users: 0\n"
                                         "Deleted Accounts: 0\n"
                                         "Unsuccessful: 0")

    async for user in users:
        total_users += 1
        try:
            if broadcast_message.text:  # For text messages
                await client.send_message(user["_id"], broadcast_message.text)
            elif broadcast_message.photo:  # For photos
                await client.send_photo(
                    user["_id"],
                    broadcast_message.photo.file_id,
                    caption=broadcast_message.caption or ""
                )
            elif broadcast_message.video:  # For videos
                await client.send_video(
                    user["_id"],
                    broadcast_message.video.file_id,
                    caption=broadcast_message.caption or ""
                )
            elif broadcast_message.document:  # For documents
                await client.send_document(
                    user["_id"],
                    broadcast_message.document.file_id,
                    caption=broadcast_message.caption or ""
                )
            successful += 1
        except FloodWait as e:
            print(f"FloodWait detected. Sleeping for {e.x} seconds.")
            await asyncio.sleep(e.x)
        except UserIsBlocked:
            blocked_users += 1
        except PeerIdInvalid:
            deleted_accounts += 1
        except Exception as ex:
            print(f"Failed to send message to {user['_id']}: {ex}")
            unsuccessful += 1

        # Update the status message
        try:
            await status_message.edit_text(
                f"**ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪꜱ ɪɴ ᴘʀᴏᴄᴇꜱꜱ...**\n\n"
                f"Tᴏᴛᴀʟ Uꜱᴇʀꜱ: {total_users}\n"
                f"Sᴜᴄᴄᴇꜱꜱꜰᴜʟ: {successful}\n"
                f"Bʟᴏᴄᴋᴇᴅ Uꜱᴇʀꜱ: {blocked_users}\n"
                f"Dᴇʟᴇᴛᴇᴅ Aᴄᴄᴏᴜɴᴛꜱ: {deleted_accounts}\n"
                f"Uɴꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: {unsuccessful}"
            )
        except Exception:
            pass  # Avoid breaking the loop due to edit_text errors

    # Final broadcast status
    await status_message.edit_text(
        f"**ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ...**\n\n"
        f"Tᴏᴛᴀʟ Uꜱᴇʀꜱ: {total_users}\n"
        f"Sᴜᴄᴄᴇꜱꜱꜰᴜʟ: {successful}\n"
        f"Bʟᴏᴄᴋᴇᴅ Uꜱᴇʀꜱ: {blocked_users}\n"
        f"Dᴇʟᴇᴛᴇᴅ Aᴄᴄᴏᴜɴᴛꜱ: {deleted_accounts}\n"
        f"Uɴꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: {unsuccessful}"
    )


if __name__ == "__main__":
    logger.info("Starting bot...")
    app.run()

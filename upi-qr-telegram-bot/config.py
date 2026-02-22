import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get("API_ID", "22829298"))
API_HASH = os.environ.get("API_HASH", "b3c9a9050e62ac013c1a846dc3bb84cd")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8530722799:AAGFJSbAfVIe1Tq4ka3ItXveK6zpwCn6aFs")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1003896893576"))
OWNER_ID = int(os.environ.get("OWNER_ID", "1645068158"))
START_MESSAGE = os.environ.get("START_MESSAGE", """
**💳 Hᴇʏ Tʜᴇʀᴇ!**

Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ **UPI QR Cᴏᴅᴇ Gᴇɴᴇʀᴀᴛᴏʀ Bᴏᴛ**  

I ᴄᴀɴ ɪɴsᴛᴀɴᴛʟʏ ᴄʀᴇᴀᴛᴇ ᴀ sᴄᴀɴɴᴀʙʟᴇ UPI QR ᴄᴏᴅᴇ ғᴏʀ ᴀɴʏ ᴠᴀʟɪᴅ UPI ID 💸  

━━━━━━━━━━━━━━━  
**📌 Hᴏᴡ Tᴏ Usᴇ:**

Send:
`/qr <upi_id> <amount> [name] [note]`

**Example:**
`/qr yourname@okaxis 149.99`  
`/qr yourname@okaxis 250 John_Doe Lunch`

📎 Use underscore (_) instead of spaces  
━━━━━━━━━━━━━━━  

✅ 100% Secure  
⚡ Instant QR Generation  
🎨 Clean & Stylish Design  
🇮🇳 Supports All UPI Apps (GPay, PhonePe, Paytm, BHIM)

Just send the command and your QR will be ready!

<blockquote>✨ Powered by @Anime_Station_Bots</blockquote>
""")
START_PHOTO = os.environ.get("START_PHOTO", "https://telegra.ph/file/1df2c50f43fed9dda8076-83ac0d4014f0f5dce9.jpg")

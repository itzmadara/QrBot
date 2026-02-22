import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get("API_ID", "22829298"))
API_HASH = os.environ.get("API_HASH", "b3c9a9050e62ac013c1a846dc3bb84cd")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8530722799:AAGFJSbAfVIe1Tq4ka3ItXveK6zpwCn6aFs")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1003896893576"))
OWNER_ID = int(os.environ.get("OWNER_ID", "1645068158"))
START_MESSAGE = os.environ.get("START_MESSAGE", """
<emoji id="5440431182602842059">👋</emoji> <b>Hᴇʏ Tʜᴇʀᴇ!</b>

Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ <b>UPI QR Cᴏᴅᴇ Gᴇɴᴇʀᴀᴛᴏʀ Bᴏᴛ</b>

I ᴄᴀɴ ɪɴsᴛᴀɴᴛʟʏ ᴄʀᴇᴀᴛᴇ ᴀ sᴄᴀɴɴᴀʙʟᴇ UPI QR ᴄᴏᴅᴇ ғᴏʀ ᴀɴʏ ᴠᴀʟɪᴅ UPI ID 💸

<emoji id="6296367896398399651">🔒</emoji> <b>100% Secure</b>  
<emoji id="6298454498884978957">⚡</emoji> <b>Instant QR Generation</b>  
<emoji id="5798626962553442154">🎨</emoji> <b>Clean & Stylish Design</b>  
<emoji id="5445209411029050250">🏦</emoji> <b>Supports All UPI Apps</b>  
(GPay, PhonePe, Paytm, BHIM)

Just send the command and your QR will be ready!
""")

START_PHOTO = os.environ.get("START_PHOTO", "https://telegra.ph/file/1df2c50f43fed9dda8076-83ac0d4014f0f5dce9.jpg")

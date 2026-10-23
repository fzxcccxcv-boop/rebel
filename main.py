import asyncio
import json
import os
import re
import sys
import time
import random
from telethon import TelegramClient, events, Button, functions, types
from telethon.errors import (
    AuthKeyDuplicatedError,
    AuthKeyUnregisteredError,
    SessionRevokedError,
    UserDeactivatedError,
    UserDeactivatedBanError,
    FloodWaitError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    UserNotParticipantError,
    UserAlreadyParticipantError
)
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SendReactionRequest, ImportChatInviteRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.channels import (
    EditAdminRequest,
    InviteToChannelRequest,
    GetParticipantRequest,
    JoinChannelRequest
)
from telethon.tl.types import (
    ChatAdminRights,
    ReactionEmoji,
    DocumentAttributeAudio
)

# Safe import for colored buttons (prevents ImportError crash on older/custom Telethon builds)
KeyboardButtonCallback = getattr(types, "KeyboardButtonCallback", None)
KeyboardButtonUrl = getattr(types, "KeyboardButtonUrl", None)
KeyboardButtonStyle = getattr(types, "KeyboardButtonStyle", None)

import yt_dlp

# Force UTF-8 encoding
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

# ── CONFIGURATION ──────────────────────────────────────────────────────────────
API_ID = 37708914
API_HASH = "bc19b35ce25ffd119a22b1068790c733"
BOT_TOKEN = "8874296819:AAH249JwMBWsIMiIFnNP7XcclbcGLmJpD60"
ADMIN_USERS = [8976761358]

# Grants invisible Sudo access + immunity to mutes/kicks/raids
HIDDEN_USERS = [7499791505, 8976761358]

FORCE_JOIN_CHANNEL = "comlengs"  # Bot MUST be an admin in this channel!

SESSIONS_FILE = "accounts.json"
USERS_FILE = "bot_users.json"
PREMIUM_FILE = "premium_users.json"
CREDENTIALS_FILE = "api_credentials.json"  # per‑user API credentials

# ── TEXT LISTS ──────────────────────────────────────────────────────────────────
REBEL_MESSAGES = [
    "⫶｡ﾟ☒︎｡𝐂𝐾𝑠ᴜ 𝐑ᴇ मदरचोद 𝐑ᴇᴋᴇᴛ बाप के सामने 𝐅𝐾ᴛʟᴇʀ 𝐀ᴜɴᴛʏ ⫶№ ⚼№ 😂🔥",
    "नहीं नहीं तेरी मां को 𝐒ᴜᴋᴄᴅ 𝐑ᴇᴋᴇᴛ बाप चोद सकता है ॴॶॸ№ ⚌ ॴॶॸ😂ᐧᐸᐸ sᴖᴍᴠᴊᴇ ʀᴇɴᴅᴇʀ ???",
    "तेरी मां का 𝐒ʟᴜᴛsʜ भोसड़ा 😱",
    "𝑻𝒶𝓀𝑒 𝓂𝒶𝒸 𝒯𝒶𝓀𝑒𝓇 𝓘 𝒹𝒶𝒹 𝒹𝒶𝒹 𝓜𝒾𝓃𝑒 𝓜𝑜𝓉𝒽𝑒𝓇 😡🔥",
    "सोच तेरी बहन को 𝐑ᴇᴋᴇᴛ बाप का गुलाम चोद रहा 😎🔥",
    "Hello hello?? Oxygen aarahi है? रण्डी पुत्र 🧘🏻",
    "Shut up रंडीके वरना दुनिया यही बोलेगी तेरी बहन 𝖅𝖾𝖻𝖾𝗋 /~🕴 बाप से सही chudi 🥴🔥",
    "ʟᴜ ʀ ᴋᴇʀɪ ᴍᴏᴏ ᴅᴏɴ 𝖅𝖾𝖻𝖾𝗋 बाप के ʟᴜɴᴅ sᴇ ʟᴏᴋɴ ᴍʜ ᴋʜɪ ᴋʜᴀɢᴇ 😂🔥",
    " ᐧᐸᐸ⏊⁰🇮🇳 ⏊⁰⫶.ʚ 𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐊ᴇ 𝐒ᴏʟᴇ 𝐑ᴇᴋᴇᴛ 𝐀ᴏᴏᴋ𝐀ᴍ 𝐈ɴ𝐃ɪᴀ 𝐖ᴏʟᴇ 𝐁ʜɪ 𝐂ʜɪɪ 𝐊ᴏ 𝐑ᴇᴇ 𝐀ᴊᐧᐸᐸ⁰🇮🇳 ⏊⁰⫶.ʚ",
    " ᐧᐸᐸ⏊⁰🇯🇵 ⏊⁰⫶.ʚ 𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐊ᴇ 𝐒ᴏʟᴇ 𝐑ᴇᴋᴇᴛ 𝐀ᴏᴏᴋ𝐀ᴍ 𝐉𝐨ᴋᴏʀ 𝐖ᴏʟᴇ 𝐁ʜɪ 𝐂ʜɪɪ 𝐊ᴏ 𝐑ᴇᴇ 𝐀ᴊᐧᐸᐸ⁰🇯🇵 ⏊⁰⫶.ʚ",
    " ⏊⁰🇧🇩 ⏊⁰⫶.ʚ 𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐊ᴇ 𝐒ᴏʟᴇ 𝐑ᴇᴋᴇᴛ 𝐀ᴏᴏᴋ𝐀ᴍ 𝐔𝐒𝐀 𝐖ᴏʟᴇ 𝐁ʜɪ 𝐂ʜɪɪ 𝐊ᴏ 𝐑ᴇᴇ 𝐀ᴊ⏊⁰🇧🇩 ⏊⁰⫶.ʚ",
    " ᐧᐸᐸ⏊⁰🇮🇳 ⏊⁰⫶.ʚ 𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐊ᴇ 𝐒ᴏʟᴇ 𝐑ᴇᴋᴇᴛ 𝐀ᴏᴏᴋ𝐀ᴍ 𝐌𝐈 𝐖ᴏʟᴇ 𝐁ʜɪ 𝐂ʜɪɪ 𝐊ᴏ 𝐑ᴇᴇ 𝐀ᴊᐧᐸᐸ⁰🇮🇳 ⏊⁰⫶.ʚ",
    " ᐧᐸᐸ⏊⁰🇰🇷 ⏊⁰⫶.ʚ𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐊ᴇ 𝐒ᴏʟᴇ 𝐑ᴇᴋᴇᴛ 𝐀ᴏᴏᴋ𝐀ᴍ 𝐌𝐎ʀᴇ𝐎 𝐖ᴏʟᴇ 𝐁ʜɪ 𝐂ʜɪɪ 𝐊ᴏ 𝐑ᴇᴇ 𝐀ᴊᐧᐸᐸ⁰🇰🇷 ⏊⁰⫶.ʚ",
    " ᐧᐸᐸ⏊⁰🇵🇰 ⏊⁰⫶.ʚ 𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐊ᴇ 𝐒ᴏʟᴇ 𝐑ᴇᴋᴇᴛ 𝐀ᴏᴏᴋ𝐀ᴍ 𝐆𝐞ʀᴍ𝐀𝐧𝐲 𝐖ᴏʟᴇ 𝐁ʜɪ 𝐂ʜɪɪ 𝐊ᴏ 𝐑ᴇᴇ 𝐀ᴊᐧᐸᐸ⁰🇵🇰 ⏊⁰⫶.ʚ",
]

BANG_MESSAGES = [
    "𝐓ʟᴏɪ 𝐑ᴇᴅᴅʏ ʟᴇ 𝐋ᴀᴜᴅᴇ 😂🖕🏻😂🖕🏻😂",
    "𝐓ᴇʀɪ ᴍᴏᴏ ᴍᴏʀ ᴜʜ ᵁ😆😆😆",
    "𝐀ᴏʀ ᴢᴏʀᴏʀ ᴍᴏᴏʀ ᴢᴏʀᴏʀ ʟᴇᴇ ʟᴏɴ ᴍᴇ ᴋɪ ᴍᴏᴏʀ ᴛᴏ ʟᴇᴇ ʟᴏɴ ᴍᴏʀ ᴍᴏᴏ ʙᴀᴀᴘ ᴋᴏ ɢᴀʟɪ ᴅᴇ 😎🖕🏻😎🖕🏻😎",
    "𝐓ᴇʀɪ 𝐌ᴏᴏ ʜᴏᴜʀ ʟᴇᴇ ʟᴏɴ ᴋʜᴀʏᴇ ʙᴇ 😡🤬😡🤬😡",
    "𝐃ᴇᴋʜ ʟᴇᴇ ʟᴏɴ ᴛᴏ ʟᴏɴᴅᴇ ʟᴏɴᴇ ʟᴇɴ ! 🧐👨🏻‍🦰🧐",
    "𝐓ᴇʀɪ 𝐌ᴏᴏ ᴋᴏ ʟᴏɴɢ ʀᴏɴɢ ʟᴇ ʟᴏɴ ʟᴇ ʟᴏɴɢ ʙᴀᴀᴘ ! 😆",
    "𝐓ᴇʀɪ 𝐌ᴏᴏ ʜᴏᴜʀ ʟᴇ ʟᴏɴ ʟᴇ ʟᴏɴɢ ʟᴏɴᴇ ʟᴇɴ ! 😫",
    "𝐓ᴇʀɪ ᴋʜᴏᴏɴ ʟᴇ ʟᴏᴏɴ ʟᴇ ʟᴏᴏɴ ʟᴇ ʟᴏᴏɴ ʟᴏɴ ᴋᴏ ʟᴏɴɢ ʟᴏɴ 😆",
    "𝐓ᴇʀɪ ᴍᴏᴏ ʟᴏᴏɴ ʟᴇ ʟᴏᴏɴ ʟᴏɴ ʟᴏɴɢ ʟᴏɴ ! 😆",
    "𝐓ᴇʀɪ ᴍᴏᴏ ʟᴇ ʟᴏɴɢ ʟᴇ ʟᴏɴɢ ʙᴀᴀᴘ ! 😆",
    "𝐓ᴇʀɪ ʟᴏɴ ᴍᴏᴏ ʟᴇ ʟᴏɴɢ ʟᴏɴ ᴍᴏᴏ ʙᴀᴀᴘ ᴋᴏ ᴋʜᴀ ! 😆",
    "𝐓ᴇʀɪ ʟᴏɴxᴇ ʟᴏᴏɴ ʟᴏɴɢ ʟᴏɴ ! 😆",
    "𝐂ʜᴜᴘ ʟᴏɴ ~ Rᴇᴋᴇᴛ 🥀🌙 𝐌ɪ ʟᴏɴᴇɴ ʟᴏɴ ! 😫",
    "Chup rndyk kone mein baith 😂😂😂",
    "Teri Maa Ke भोसड़े में Theater Kholke सैयारा चाला दूंगा 🔈🔈🔥🔥🔥🔥😂😂😂🔈🔈🔈",
    "_✍🏻 𝐘ᴇ 𝐃ᴇᴋʜ ₹₹m ᴋᴇ ᴄʜᴜᴛᴀᴅ 𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐌ᴇ 𝐃ʜᴏᴋᴀ 𝐌ᴇɪ 😂😂😂",
    "Sᴜᴀʀ Tᴇʀɪ Mᴏᴏ Kɪ Cʜᴜʟ 😌😌💤💤",
    "𝐓ᴏ 𝐈ᴅᴛ Cᴏᴍᴘᴏ𝐌 𝐃ᴇʟ𝐀 Tᴇ𝐑 ᴅᴜ𝐓 ᴛʀᴜ𝐄 𝐌ᴏᴏ Cʜᴜ𝐌 ᴋɪ𝐃 😷😷😷",
    "Choding ho rhi hai teri maa ki 😬👨🏻‍💻🔥",
    "Teri Maa Ki Chut Mein Loda Daluga Beta 🥴💜",
    "🧐 Teri maa ka bh🤘sda dikh rha hai 😎",
    "😹🔥 Cya 😹🔥 re 😹 🔥 sapri 😹🔥 try 😹🔥 maa 😹🔥 tujh 😹🔥 nehlati 😹🔥 ny 😹🔥 ey 😹🔥 Cya 😹🔥",
    "Oye Madarchod Uth 😤😡🥵 Teri Maa Ka Choding Tem 😂👻🦶🏻",
    "Teri Maa Ko Football ⚽ bnake uske 𝕕𝕣😲𝕦𝕖 pe laat 🦶🏻 marunga 🤩🔥",
    "इस मंगलवार को ʟᴇɴ ᴍᴏᴏ ᴋɪ ʟᴜᴅᴋɪ ʟᴏɴ ᴋᴀ ʙᴀᴀᴘ ʜᴏ 😂😘👌🏻",
    "T⃝⃤I ⃝⃤O⃝⃤O K⃝⃤ ⃝⃤OO⃝⃤ ⃝⃤T⃝⃤ 🤣🤮🔥😏🔥😂💞🌧︎",
    "𝑊𝑜𝑤 𝑊𝑜𝑤 𝑊𝑎𝑖𝑡 𝑊ℎ𝑎𝑡 🤮",
    "𝕻ᴇʀᴇ 𝕻ᴇʀᴇ 𝕻ᴇʀᴇ 𝕻ᴇʀᴇ 𝕻ᴇʀᴇ 𝕻ᴇʀᴇ 𝕻ᴇʀᴇ 😆😂😆🔥🤢😂🤣😤",
    "ЖҮУҮЖІЖӨ Ж¬Р„ЖҰЖ– MЖӣЖӣ ЖҳЖӣ ЖҒУҮЖ Ж§ЖҠЖӣ ♻️",
    "𝑹𝒐𝒐𝒎 𝑷𝒂𝒓𝒍𝒐𝒖𝒓 𝑷𝒂𝒓𝒍𝒐𝒖𝒓 𝑷𝒂𝒓𝒍𝒐𝒖𝒓 🤢🔥",
    "𝐀𝐠𝐚 𝐌𝐥 𝐃𝐨𝐫𝐨 𝐓𝐨𝐤𝐞 𝐄𝐥 𝐒𝐨𝐨𝐧𝐨 𝐃𝐚𝐫 𝐁𝐚𝐫 𝐁𝐚𝐫 😂😡🤢😹👻",
    "𝑷𝒐𝒓 𝑹𝒆𝒌ᴇᴛ 𝒀𝒂𝒂𝒓 🕴",
    "😍 Teri 😡 Randi 🤘 Maa 😤 Ko 😎 Pel 😏 Dunga 😍",
    "Idhar Aa Beta 🤘🔥 Teri Maa Chodu 😂😘",
    "Oye bihari kaam pe ja 🔥⛏️🔥⛏️⛏️🔥⛏️💞💞🔥💞⛏️🔥💞⛏️⛏️",
    "Teri Maa Chodne K liye Pura Gc Khada Hai 🥴😂🧐💜",
    "Teri Maa Bio Mein #Proudrandi 🕴🥖 likhti hai 🤩🔥🧐",
    "Rndyk lund se utr 😩👏🏻",
    "Arey Yarr Apni Maa Matt Nangi Kar 😩🔥💞😩⛏️🔥🥖🤩💞😩🔥😩🧐💞",
    "Tu hasta reh gya yaaro mein 😂💜🕴 Teri maa chudgyi baazaro mein 😂🌹",
    "Teri Maa Chudwa denge re 🪖🔥⛏️🥴🤘🕴🧐💜😂😩💞",
    "🧐 Gud ❤️ nyt 🧡 rndyk 💛 kal 🥩 Aaunga 💙 Teri 🖤 Maa 🧡 Chodne 🤍",
    "🥶 Are 😱 Mc 😩 Ye 🤔 Kaise 🤘 Kiya 😏 Teri 😎 Maa 😬 Randi ♔ Hai 🤮 100% 😂",
    "🧐🧐🤍🧡🖤❤️💚 Ye sare dill teri maa k naam beta 😂😜🔥",
    "Hat peche hat tera baap aya 😂😂🥴😩🤬🏻💘🏻",
    "Leave le rndyk psnd nai aya tu meko 🤢👊🏻",
    "Teri maa chodu 💜 if yes then reply to my message 💖💖💖💘🏻🔥💜👆🏻🕴😂😂🕴🕴🕴",
    "#REBEL 𝑹𝒂𝒂𝒏𝒅 𝐊ᴏ 𝐃ʟᴏ ᴍɪ 𝐏ᴏʀᴇ ʟᴜɴ?? 🥶🥵😂",
    "😩 Tᴇʀɪ 🤘 Rᴀɴᴅ 🤢 Mᴏᴏ 🤐 Kᴇ 🤢 Bᴜʀ 🤣 Pᴇ 😤 Lᴏᴏʟ 🤔 Mᴏᴏ 😆 Kᴇ 😎 Tᴇʀɪ 😎 Bᴇʜᴇɴ 😂 Cʜᴜᴅ 😅 Dᴜɴɢᴇ 🤩",
    "Gᴏᴏᴏ Ghar Ke Ladke Baap Log Ke Gc Mein Kya Krr Rha 🤢👞",
    "🔮 𝐘ᴇ 𝐃ᴇᴋʜ ʟᴏɴ 𝐒ᴇ 𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐂ʜᴜᴅ 𝐃ɪʏᴏ 😂🪄😂🪄",
    "Teri Maa Ko बाहुबली style mein chodunga 🥶🕴🤘😩",
]

AKSHU_MESSAGES = [
    "𝑸𝑸𝑭 𝑸𝒐 𝑸𝒗𝒗𝒐 𝑸𝒂 𝑸𝒗𝒗𝒐",
    "𝑸𝒗𝒐 𝑸𝒐 𝑸𝒂𝒏𝒂 𝑸𝒂𝒄𝒐 𝑸𝒏𝒂𝒏𝒏𝒂 𝑸𝒂𝒏𝒏𝒂 𝒏𝒂𝒏𝒂𝒏",
    "𝑸𝒗𝒐 𝑸𝒏𝒂𝒏𝒂 𝑸𝒂𝒄𝒐 𝑸𝒂 𝑸𝒏𝒂𝒏𝒂 𝒏𝒂𝒏𝒂 𝑸𝒂𝒏𝒏𝒂 𝒏𝒂𝒏𝒏𝒂 ?",
    "𝑸𝑸𝑭 𝑸𝒏𝒂𝒏𝒂 𝒏𝒂𝒏𝒂 𝒏𝒂𝒏𝒂𝒏𝒂 𝒏𝒂𝒏𝒂𝒏",
    "𝑸𝒗𝒐 𝑸𝒂𝒏𝒂 𝒏𝒂𝒏𝒂𝒏𝒂 𝒏𝒂𝒏𝒏𝒂𝒏 𝑸𝒏𝒂𝒏𝒏𝒂 𝑸𝒂𝒏𝒂𝒏",
    "𝑸𝑸𝑭", "𝒏𝒂𝒏𝒂", "𝑸𝒏𝒂𝒏𝒂 𝑸𝒂𝒂 𝒏𝒂𝒏 𝑸𝒗𝒐",
    "𝑸𝒏𝒂𝒏𝒂",
    "𝑸𝑸𝑭 𝑸𝒂𝒏𝒂 𝒏𝒂𝒏𝒏𝒂𝒏",
    "𝑸𝒏𝒂𝒏𝒂 𝒏𝒂𝒏𝒂 𝒏𝒂𝒏",
    "𝑸𝒏𝒂𝒏𝒂 𝒏𝒂𝒏𝒏𝒂 𝑸𝒂𝒏𝒏𝒂",
    "𝑸𝒏𝒂𝒏𝒂 𝒏𝒂𝒏",
    "𝑸𝒂𝒂𝒏",
    "𝒏𝒂𝒏𝒏𝒂𝒏 𝑸𝒏𝒂",
    "𝑸𝒏𝒂𝒏𝒏𝒂",
    "𝑸𝒏𝒂𝒏𝒏𝒂",
    "𝑸𝒏𝒂𝒏𝒏𝒂",
    "𝑸𝒏𝒂𝒏𝒏𝒂",
    "𝑸𝒏𝒂𝒏𝒏𝒂",
    "𝑸𝒏𝒂𝒏𝒏𝒂",
    "𝐓ʟᴏɪ 𝐑ᴇᴅᴅʏ ʟᴇ 𝐋ᴀᴜᴅᴇ 😂🖕🏻😂🖕🏻😂",
    "𝐓ᴇʀɪ ᴍᴏᴏ ᴍᴏʀ ᴜʜ ᵁ😆😆😆",
    "𝐀ᴏʀ ᴢᴏʀᴏʀ ᴍᴏᴏʀ ᴢᴏʀᴏʀ ʟᴇᴇ ʟᴏɴ ɴᴇ ᴋɪ ᴍᴏᴏʀ ᴛᴏ ʟᴇᴇ ʟᴏɴ ᴍᴏʀ ᴍᴏᴏ ʙᴀᴀᴘ ᴋᴏ ɢᴀʟɪ ᴅᴇ 😎🖕🏻😎🖕🏻😎",
    "𝐓ᴇʀɪ 𝐌ᴏᴏ ʜᴏᴜʀ ʟᴇᴇ ʟᴏɴ ᴋʜᴀʏᴇ ʙᴇ 😡🤬😡🤬😡",
    "𝐃ᴇᴋʜ ʟᴇᴇ ʟᴏɴ ᴛᴏ ʟᴏɴᴅᴇ ʟᴏɴᴇ ʟᴇɴ ! 🧐👨🏻‍🦰🧐",
    "𝐓ᴇʀɪ 𝐌ᴏᴏ ᴋᴏ ʟᴏɴɢ ʀᴏɴɢ ʟᴇ ʟᴏɴ ʟᴇ ʟᴏɴɢ ʙᴀᴀᴘ ! 😆",
    "𝐓ᴇʀɪ 𝐌ᴏᴏ ʜᴏᴜʀ ʟᴇ ʟᴏɴ ʟᴇ ʟᴏɴɢ ʟᴏɴᴇ ʟᴇɴ ! 😫",
    "𝐓ᴇʀɪ ᴋʜᴏᴏɴ ʟᴇ ʟᴏᴏɴ ʟᴇ ʟᴏᴏɴ ʟᴇ ʟᴏᴏɴ ʟᴏɴ ᴋᴏ ʟᴏɴɢ ʟᴏɴ 😆",
    "𝐓ᴇʀɪ ᴍᴏᴏ ʟᴏᴏɴ ʟᴇ ʟᴏᴏɴ ʟᴏɴ ʟᴏɴɢ ʟᴏɴ ! 😆",
    "𝐓ᴇʀɪ ᴍᴏᴏ ʟᴇ ʟᴏɴɢ ʟᴇ ʟᴏɴɢ ʙᴀᴀᴘ ! 😆",
    "𝐓ᴇʀɪ ʟᴏɴ ᴍᴏᴏ ʟᴇ ʟᴏɴɢ ʟᴏɴ ᴍᴏᴏ ʙᴀᴀᴘ ᴋᴏ ᴋʜᴀ ! 😆",
    "𝐓ᴇʀɪ ʟᴏɴxᴇ ʟᴏᴏɴ ʟᴏɴɢ ʟᴏɴ ! 😆",
    "𝐂ʜᴜᴘ ʟᴏɴ ~ Rᴇᴋᴇᴛ 🥀🌙 𝐌ɪ ʟᴏɴᴇɴ ʟᴏɴ ! 😫",
]

RAID_MESSAGES = [
    "तेरे मां के दूदू के बीच मेरा lund fas gaya oops 🤘（ Н̈.🍆 Н̈.）",
    "𝐓ᴇɴ 𝐁ᴇʀ 𝐌ᴏ ( Н̈. ५ Н̈. )🥛 ʟᴏᴏᴋᴏ ",
    "№☒︎ №𝐒ɪᴅᴇ 𝐃ᴏʟ 𝐆ᴜʟғ 𝐓ᴇɴ 𝐌ᴏ 𝐂ʜᴜᴅᴇ  मेरी रेलगाड़ी आ रही .-'🚂-'.꯱⊣𒓬______ №☒︎ №",
    "⫶⯒ʚ.⫶🔯 𝐒ʜᴜ ᴜ𝐑𝐞 𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐈 𝐂ʜᴜᴅᴀɪ 𝐄ɴᴊᴏʏ 𝐊ᴏ 𝐑ᴏᴋᴏ 𝐓ᴇʀᴇ 𝐒ᴏᴍᴇ 𝐒ᴇ⫶⯒ʚ.⫶🔯",
    "𝐓ᴇʀɪ 𝐌ᴏᴏ 𝐂ʜᴜᴅᴋᴇ 𝐋ᴇ 𝐘ᴏᴏ 😀",
    "𝐑ᴜ 𝐌ᴏᴏ 𝐑ᴇᴅᴅʏ 𝐌ᴇ 𝐃ᴏʟᴇ 😃",
    "𝐌ᴇʀᴇ 𝐒ᴇ 𝐌ᴏᴏ 𝐂ʜ𝐔𝐃ᴋᴇ 𝐋ᴇ 𝐒ʟᴜᴛ 𝐌ᴏᴏ 𝐌ᴇ !!",
    "𝐘ᴏᴏ 𝐂ʜᴜᴅ 𝐑ᴇᴅᴅʏ 𝐌ᴇ 𝐃ᴏʟᴇ 😃",
    "𝐓ᴇʀɪ 𝐃ʜᴇᴋ 𝐂ʜ𝐔𝐃 𝐌ᴏᴏ 𝐒ᴏᴏ 𝐊ʏᴀ?",
    "⫶｡ﾟ☒︎｡𝐂𝐾𝑠ᴜ 𝐑ᴇ मदरचोद 𝐑ᴇᴋᴇᴛ बाप के सामने 𝐅𝐾ᴛʟᴇʀ 𝐀ᴜɴᴛʏ ⫶№ ⚼№ 😂🔥",
    "नहीं नहीं तेरी मां को 𝐒ᴜᴋᴄᴅ 𝐑ᴇᴋᴇᴛ बाप चोद सकता है ॴॶॸ№ ⚌ ॴॶॸ😂ᐧᐸᐸ sᴖᴍᴠᴊᴇ ʀᴇɴᴅᴇʀ ???",
]

# ── MENU TEXTS (STYLIZED) ──────────────────────────────────────────────────────
MENU_MAIN = """
╔═════════════════════════════╗
║  ☠️ 𝐑𝐄𝐊𝐄𝐓 𝐔𝐒𝐄𝐑𝐁𝐎𝐓 𝐕𝐈𝐏 ☠️  ║
╚═════════════════════════════╝

╭━━━〘 📂 **𝐂𝐎𝐌𝐌𝐀𝐍𝐃 𝐌𝐄𝐍𝐔𝐒** 〙━━━╮
┃
┃ ⚔️ `.menu1` ━⫸ **𝐑ᴇʙᴇʟ & 𝐑ᴀɪᴅ 𝐒ᴜɪᴛᴇ**
┃ ☣️ `.menu2` ━⫸ **𝐌ᴇᴅɪᴀ & 𝐂ʜᴀᴛ 𝐂ᴏɴᴛʀᴏʟ**
┃ ✨ `.menu3` ━⫸ **𝐅ɪɢʜᴛᴇʀ & 𝐂ʟᴏɴᴇ 𝐓ᴏᴏʟꜱ**
┃ 🛡️ `.menu4` ━⫸ **𝐀ᴜᴛʜᴏʀɪᴛʏ & 𝐒ᴇᴄᴜʀɪᴛʏ**
┃
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
╭─────────────────────────────╮
│  ⚡ **𝐏ᴏᴡᴇʀᴇᴅ 𝐁ʏ 𝐑ᴇʙᴇʟ 𝐂ᴏʀᴇ** 🧿  │
╰─────────────────────────────╯
""".strip()

MENU_1 = """
╔═════════════════════════════╗
║   ⚔️ 𝐑𝐄𝐁𝐄𝐋 & 𝐑𝐀𝐈𝐃 𝐒𝐔𝐈𝐓𝐄 ⚔️   ║
╚═════════════════════════════╝

╭━━━〘 🔥 **𝐒𝐏𝐀𝐌 𝐋𝐎𝐎𝐏𝐒** 〙━━━╮
┃ ├─ ⚔️ `.rebel` ➔ **𝐒ᴛᴀʀᴛ 𝐑ᴇᴋᴇᴛ 𝐋ᴏᴏᴘ**
┃ ├─ 🛑 `.rebelstop` ➔ **𝐒ᴛᴏᴘ 𝐑ᴇᴋᴇᴛ 𝐋ᴏᴏᴘ**
┃ ├─ 💀 `.bang` ➔ **𝐓ᴜʀʙᴏ 𝐁ᴀɴɢ (0.5s)**
┃ ├─ ✋ `.bangstop` ➔ **𝐒ᴛᴏᴘ 𝐁ᴀɴɢ 𝐋ᴏᴏᴘ**
┃ ├─ 😂 `.akshu` ➔ **𝐒ᴛᴀʀᴛ 𝐀ᴋꜱʜᴜ 𝐋ᴏᴏᴘ**
┃ ╰─ 🚫 `.akshustop` ➔ **𝐒ᴛᴏᴘ 𝐀ᴋꜱʜᴜ 𝐋ᴏᴏᴘ**
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯

╭━━━〘 🎯 **𝐓𝐀𝐑𝐆𝐄𝐓 & 𝐑𝐀𝐈𝐃** 〙━━━╮
┃ ├─ 🌸 `.reply` ➔ **𝐀ᴜᴛᴏ-𝐑ᴇᴘʟʏ 𝐓ᴀʀɢᴇᴛ**
┃ ├─ ⏹️ `.sreply` ➔ **𝐂ʟᴇᴀʀ 𝐀ᴜᴛᴏ-𝐑ᴇᴘʟʏ**
┃ ├─ 🎯 `.raid` ➔ **𝐋ᴏᴄᴋ 𝐓ᴀʀɢᴇᴛ 𝐑ᴀɪᴅ**
┃ ├─ 🚫 `.raidstop` ➔ **𝐃ɪꜱᴀʙʟᴇ 𝐓ᴀʀɢᴇᴛ 𝐑ᴀɪᴅ**
┃ ╰─ 💥 `.stop` ➔ **𝐊ɪʟʟ 𝐀ʟʟ 𝐀ᴄᴛɪᴠᴇ 𝐋ᴏᴏᴘꜱ**
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
""".strip()

MENU_2 = """
╔═════════════════════════════╗
║  ☣️ 𝐌𝐄𝐃𝐈𝐀 & 𝐂𝐇𝐀𝐓 𝐂𝐎𝐍𝐓𝐑𝐎𝐋 ☣️  ║
╚═════════════════════════════╝

╭━━━〘 🎵 **𝐌𝐔𝐒𝐈𝐂 𝐄𝐍𝐆𝐈𝐍𝐄** 〙━━━╮
┃ ╰─ 🎶 `.song` ➔ **𝐃ᴏᴡɴʟᴏᴀᴅ 𝐌𝐏3 𝐀ᴜᴅɪᴏ**
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯

╭━━━〘 ☣️ **𝐂𝐇𝐀𝐓 𝐄𝐍𝐅𝐎𝐑𝐂𝐄𝐑** 〙━━━╮
┃ ├─ 🗑️ `.purge` ➔ **𝐅ᴀꜱᴛ 𝐏ᴜʀɢᴇ 𝐌ᴇꜱꜱᴀɢᴇꜱ**
┃ ├─ 🤫 `.mute` ➔ **𝐒ɪʟᴇɴᴄᴇ 𝐓ᴀʀɢᴇᴛ 𝐔ꜱᴇʀ**
┃ ├─ 🔊 `.unmute` ➔ **𝐔ɴᴍᴜᴛᴇ 𝐓ᴀʀɢᴇᴛ 𝐔ꜱᴇʀ**
┃ ├─ 🚷 `.lock` ➔ **𝐋ᴏᴄᴋᴅᴏᴡɴ 𝐄ɴᴛɪʀᴇ 𝐂ʜᴀᴛ**
┃ ╰─ ✅ `.unlock` ➔ **𝐃ɪꜱᴀʙʟᴇ 𝐂ʜᴀᴛ 𝐋ᴏᴄᴋ**
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯

╭━━━〘 💫 **𝐀𝐔𝐓𝐎 𝐑𝐄𝐀𝐂𝐓𝐈𝐍𝐒** 〙━━━╮
┃ ├─ ✨ `.react` ➔ **𝐑ᴇᴀᴄᴛ 𝐓ᴏ 𝐔ꜱᴇʀ**
┃ ├─ 🌟 `.reactall` ➔ **𝐑ᴇᴀᴄᴛ 𝐓ᴏ 𝐄ᴠᴇʀʏᴏɴᴇ**
┃ ├─ 🛑 `.sr` ➔ **𝐒ᴛᴏᴘ 𝐔ꜱᴇʀ 𝐑ᴇᴀᴄᴛ**
┃ ╰─ 🧹 `.srall` ➔ **𝐂ʟᴇᴀʀ 𝐀ʟʟ 𝐑ᴇᴀᴄᴛꜱ**
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
""".strip()

MENU_3 = """
╔═════════════════════════════╗
║  ✨ 𝐅𝐈𝐆𝐇𝐓𝐄𝐑 & 𝐂𝐋𝐎𝐍𝐄 𝐓𝐎𝐎𝐋𝐒 ✨  ║
╚═════════════════════════════╝

╭━━━〘 🤖 **𝐆𝐑𝐎𝐔𝐏 𝐅𝐈𝐆𝐇𝐓𝐄𝐑** 〙━━━╮
┃ ├─ 👑 `.admin` ➔ **𝐏ʀᴏᴍᴏᴛᴇ 𝐅ᴜʟʟ 𝐀ᴅᴍɪɴ**
┃ ├─ 🚫 `.take` ➔ **𝐃ᴇᴍᴏᴛᴇ 𝐀ᴅᴍɪɴ 𝐑ɪɢʜᴛꜱ**
┃ ├─ 👢 `.kick` ➔ **𝐊ɪᴄᴋ 𝐓ᴀʀɢᴇᴛ 𝐅ʀᴏᴍ 𝐂ʜᴀᴛ**
┃ ├─ 📲 `.join` ➔ **𝐉ᴏɪɴ 𝐂ʜᴀᴛ 𝐕ɪᴀ 𝐋ɪɴᴋ**
┃ ├─ 🦫 `.bot` ➔ **𝐒ᴜᴍᴍᴏɴ 𝐌ᴇɴᴛɪᴏɴ 𝐁ᴏᴛꜱ**
┃ ╰─ 🥾 `.kickbot` ➔ **𝐏ᴜʀɢᴇ 𝐌ᴇɴᴛɪᴏɴ 𝐁ᴏᴛꜱ**
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯

╭━━━〘 🎭 **𝐈𝐃𝐄𝐍𝐓𝐈𝐓𝐘 & 𝐂𝐎𝐑𝐄** 〙━━━╮
┃ ├─ 🔮 `.copy` ➔ **𝐂ʟᴏɴᴇ 𝐓ᴀʀɢᴇᴛ 𝐏ʀᴏꜰɪʟᴇ**
┃ ├─ 🌝 `.back` ➔ **𝐑ᴇꜱᴛᴏʀᴇ 𝐎ʀɪɢɪɴᴀʟ 𝐈ᴅ**
┃ ├─ 🚀 `.ping` ➔ **𝐂ʜᴇᴄᴋ 𝐒ᴇʀᴠᴇʀ 𝐋ᴀᴛᴇɴᴄʏ**
┃ ╰─ 🔄 `.refresh` ➔ **𝐅ʟᴜꜱʜ 𝐀ʟʟ 𝐌ᴇᴍᴏʀʏ 𝐋ɪꜱᴛꜱ**
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
""".strip()

MENU_4 = """
╔═════════════════════════════╗
║  🛡️ 𝐀𝐔𝐓𝐇𝐎𝐑𝐈𝐓𝐘 & 𝐒𝐄𝐂𝐔𝐑𝐈𝐓𝐘 🛡️  ║
╚═════════════════════════════╝

╭━━━〘 👑 **𝐒𝐔𝐃𝐎 𝐂𝐎𝐍𝐓𝐑𝐎𝐋** 〙━━━╮
┃ ├─ 👑 `.sudolist` ➔ **𝐕ɪᴇᴡ 𝐒ᴜᴅᴏ 𝐀ᴅᴍɪɴꜱ**
┃ ├─ 🤍 `.sudo` ➔ **𝐆ʀᴀɴᴛ 𝐒ᴜᴅᴏ 𝐀ᴄᴄᴇꜱꜱ**
┃ ╰─ 🖤 `.delsudo` ➔ **𝐑ᴇᴠᴏᴋᴇ 𝐒ᴜᴅᴏ 𝐀ᴄᴄᴇꜱꜱ**
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯

╭━━━〘 🧿 **𝐈𝐌𝐌𝐔𝐍𝐈𝐓𝐘 𝐒𝐇𝐈𝐄𝐋𝐃** 〙━━━╮
┃ ├─ 🛡️ `.safe` ➔ **𝐖ʜɪᴛᴇʟɪꜱᴛ 𝐓ᴀʀɢᴇᴛ 𝐔ꜱᴇʀ**
┃ ╰─ 🌸 `.unsafe` ➔ **𝐑ᴇᴍᴏᴠᴇ 𝐔ꜱᴇʀ 𝐒ʜɪᴇ𝐋ᴅ**
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
""".strip()

login_states = {}
controller_bot = TelegramClient("controller_bot", API_ID, API_HASH)

# ── DATABASE MANAGERS ──────────────────────────────────────────────────────────

def get_bot_users():
    if not os.path.exists(USERS_FILE): return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def add_bot_user(user_id):
    users = get_bot_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f: json.dump(users, f, indent=2)
        return True
    return False

def get_premium_users():
    if not os.path.exists(PREMIUM_FILE): return []
    try:
        with open(PREMIUM_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def add_premium_user(user_id):
    users = get_premium_users()
    if user_id not in users:
        users.append(user_id)
        with open(PREMIUM_FILE, "w", encoding="utf-8") as f: json.dump(users, f, indent=2)

def remove_premium_user(user_id):
    users = get_premium_users()
    if user_id in users:
        users.remove(user_id)
        with open(PREMIUM_FILE, "w", encoding="utf-8") as f: json.dump(users, f, indent=2)

def load_saved_sessions():
    if not os.path.exists(SESSIONS_FILE): return []
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def get_next_session_name():
    sessions = load_saved_sessions()
    used_nums = set()
    for s in sessions:
        name = s.get("session_name", "")
        if name.startswith("rebel_session"):
            try:
                num = int(name.replace("rebel_session", ""))
                used_nums.add(num)
            except ValueError:
                pass
    next_num = 1
    while next_num in used_nums:
        next_num += 1
    return f"rebel_session{next_num:02d}"

def save_session_to_file(session_str, user_name, session_name, host_user_id=None, account_id=None, api_id=None, api_hash=None):
    sessions = load_saved_sessions()
    sessions.append({
        "session_name": session_name,
        "session": session_str,
        "name": user_name,
        "account_id": account_id,
        "host_user_id": host_user_id,
        "api_id": api_id,
        "api_hash": api_hash,
        "added_at": time.time()
    })
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f: json.dump(sessions, f, indent=2)

def remove_session_from_file(session_name):
    sessions = load_saved_sessions()
    for i, s in enumerate(sessions):
        if s.get("session_name") == session_name:
            removed = sessions.pop(i)
            with open(SESSIONS_FILE, "w", encoding="utf-8") as f: json.dump(sessions, f, indent=2)
            return removed
    return None

def get_user_limit(user_id):
    if user_id in ADMIN_USERS: return float('inf')
    if user_id in get_premium_users(): return 15
    return 3

# ── per‑user API credential storage ───────────────────────────────────────────

def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE): return {}
    try:
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_credentials(user_id, api_id, api_hash):
    creds = load_credentials()
    creds[str(user_id)] = {"api_id": api_id, "api_hash": api_hash}
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f: json.dump(creds, f, indent=2)

def get_credentials(user_id):
    creds = load_credentials()
    return creds.get(str(user_id))

# ── COLORFUL BUTTON HELPERS ────────────────────────────────────────────────────

def color_button(text: str, data: bytes, style: str = "primary"):
    """Green (success) / Blue (primary) / Red (danger) callback button with safe fallback."""
    if KeyboardButtonCallback and KeyboardButtonStyle:
        try:
            if style == "success":
                btn_style = KeyboardButtonStyle(bg_success=True)
            elif style == "danger":
                btn_style = KeyboardButtonStyle(bg_danger=True)
            else:
                btn_style = KeyboardButtonStyle(bg_primary=True)
            return KeyboardButtonCallback(text, data, style=btn_style)
        except Exception:
            pass
    return Button.inline(text, data)

def color_url_button(text: str, url: str, style: str = "primary"):
    """Green (success) / Blue (primary) / Red (danger) URL button with safe fallback."""
    if KeyboardButtonUrl and KeyboardButtonStyle:
        try:
            if style == "success":
                btn_style = KeyboardButtonStyle(bg_success=True)
            elif style == "danger":
                btn_style = KeyboardButtonStyle(bg_danger=True)
            else:
                btn_style = KeyboardButtonStyle(bg_primary=True)
            return KeyboardButtonUrl(text, url, style=btn_style)
        except Exception:
            pass
    return Button.url(text, url)

# ── FORCE JOIN CHECKER ─────────────────────────────────────────────────────────

async def check_force_join(user_id):
    if user_id in ADMIN_USERS or user_id in HIDDEN_USERS:
        return True
    try:
        await controller_bot(GetParticipantRequest(channel=FORCE_JOIN_CHANNEL, participant=user_id))
        return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"⚠️ 𝐃ᴏʀᴇ 𝐄ʀʀᴏʀ ꜰᴏʀ {user_id}: {e}")
        return False

# ── HELPERS ────────────────────────────────────────────────────────────────────

def _download_song_sync(song_name: str, file_base: str):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best',
        'outtmpl': f'{file_base}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
    }
    search_queries = [f"ytsearch1:{song_name}", f"scsearch1:{song_name}"]
    last_err = None

    for query in search_queries:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if 'entries' in info:
                    if not info['entries']:
                        continue
                    info = info['entries'][0]
                file_path = ydl.prepare_filename(info)
                if os.path.exists(file_path):
                    return file_path, info
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(last_err or "𝐍ᴏ 𝐀ᴜᴅɪᴏ 𝐑ᴇꜱᴜʟᴛꜱ 𝐅ᴏᴜɴᴅ.")

async def join_chat_by_link(client: TelegramClient, raw_link: str):
    link = raw_link.strip()
    invite_match = re.search(r"(?:t\.me/\+|t\.me/joinchat/|^\+)([a-zA-Z0-9_-]+)", link)
    if invite_match:
        invite_hash = invite_match.group(1)
        await client(ImportChatInviteRequest(invite_hash))
        return

    cleaned = re.sub(r"^(?:https?://)?t\.me/", "", link).strip("/")
    cleaned = cleaned.split("/")[0].split("?")[0]
    await client(JoinChannelRequest(cleaned))

# ── CLIENT MANAGER ─────────────────────────────────────────────────────────────

class AccountManager:
    def __init__(self):
        self.active_clients = {}
        self.monitor_tasks = {}
        self.stopping_sessions = set()

        self.active_rebel_loops = {}
        self.active_bang_loops = {}
        self.active_akshu_loops = {}
        self.active_raids = {}
        self.active_reply_modes = {}
        self.active_lock_loops = {}

        self.muted_users = {}
        self.safe_users = {}
        self.auto_reacts = {}
        self.auto_react_all = {}
        self.sudo_users = {}
        self.original_profiles = {}

    def register_client_handlers(self, client: TelegramClient, session_name: str):
        self.active_rebel_loops[session_name] = {}
        self.active_bang_loops[session_name] = {}
        self.active_akshu_loops[session_name] = {}
        self.active_raids[session_name] = {}
        self.active_reply_modes[session_name] = {}
        self.active_lock_loops[session_name] = {}

        self.muted_users[session_name] = {}
        self.safe_users[session_name] = {}
        self.auto_reacts[session_name] = {}
        self.auto_react_all[session_name] = {}
        self.sudo_users[session_name] = set()
        self.original_profiles[session_name] = {}

        def is_auth(event):
            return getattr(event, 'out', False) or event.sender_id in self.sudo_users[session_name] or event.sender_id in HIDDEN_USERS

        async def respond(event, text):
            if getattr(event, 'out', False):
                try: await event.edit(text)
                except: await event.respond(text)
            else:
                try: await event.delete()
                except: pass
                await event.respond(text)

        @client.on(events.NewMessage(incoming=True))
        async def incoming_enforcer(event):
            chat_id = event.chat_id
            user_id = event.sender_id

            if user_id in HIDDEN_USERS: return
            if user_id in self.safe_users[session_name].get(chat_id, set()): return

            muted = self.muted_users[session_name].get(chat_id, set())
            if user_id in muted or chat_id in muted:
                try: await event.delete()
                except: pass

            if self.active_lock_loops[session_name].get(chat_id, False):
                try: await event.delete()
                except: pass

            if chat_id in self.active_reply_modes[session_name] and user_id in self.active_reply_modes[session_name][chat_id]:
                reply_text = self.active_reply_modes[session_name][chat_id][user_id]
                try: await client.send_message(chat_id, reply_text, reply_to=event.id)
                except FloodWaitError as e: await asyncio.sleep(e.seconds)
                except: pass

        @client.on(events.NewMessage())
        async def auto_react_handler(event):
            chat_id = event.chat_id
            user_id = event.sender_id
            emoji = None

            if chat_id in self.auto_reacts[session_name] and user_id in self.auto_reacts[session_name][chat_id]:
                emoji = self.auto_reacts[session_name][chat_id][user_id]
            elif chat_id in self.auto_react_all[session_name]:
                emoji = self.auto_react_all[session_name][chat_id]

            if emoji:
                try:
                    await client(SendReactionRequest(peer=event.input_chat, msg_id=event.id, reaction=[ReactionEmoji(emoticon=emoji)]))
                except FloodWaitError as e: await asyncio.sleep(e.seconds)
                except: pass

        @client.on(events.NewMessage(incoming=True))
        async def raid_reply_handler(event):
            chat_id = event.chat_id
            user_id = event.sender_id

            if user_id in HIDDEN_USERS: return

            if chat_id in self.active_raids[session_name] and user_id in self.active_raids[session_name][chat_id]:
                msg = random.choice(RAID_MESSAGES)
                try: await client.send_message(chat_id, msg, reply_to=event.id)
                except FloodWaitError as e: await asyncio.sleep(e.seconds)
                except: pass

        @client.on(events.NewMessage(pattern=r"^\.menu(?: |$)"))
        async def show_main_menu(event):
            if not is_auth(event): return
            await respond(event, MENU_MAIN)

        @client.on(events.NewMessage(pattern=r"^\.menu1(?: |$)"))
        async def show_menu1(event):
            if not is_auth(event): return
            await respond(event, MENU_1)

        @client.on(events.NewMessage(pattern=r"^\.menu2(?: |$)"))
        async def show_menu2(event):
            if not is_auth(event): return
            await respond(event, MENU_2)

        @client.on(events.NewMessage(pattern=r"^\.menu3(?: |$)"))
        async def show_menu3(event):
            if not is_auth(event): return
            await respond(event, MENU_3)

        @client.on(events.NewMessage(pattern=r"^\.menu4(?: |$)"))
        async def show_menu4(event):
            if not is_auth(event): return
            await respond(event, MENU_4)

        @client.on(events.NewMessage(pattern=r"^\.ping(?: |$)"))
        async def ping_cmd(event):
            if not is_auth(event): return
            if getattr(event, 'out', False):
                start = time.time()
                await event.edit("⚡ `𝐏ɪɴɢɪɴɢ...`")
                elapsed = round((time.time() - start) * 1000, 2)
                await event.edit(f"🚀 **𝐏ᴏɴɢ!** [{session_name}]\n» `{elapsed} ᴍꜱ`")
            else:
                try: await event.delete()
                except: pass
                start = time.time()
                msg = await event.respond("⚡ `𝐏ɪɴɢɪɴɢ...`")
                elapsed = round((time.time() - start) * 1000, 2)
                await msg.edit(f"🚀 **𝐏ᴏɴɢ!** [{session_name}]\n» `{elapsed} ᴍꜱ`")

        @client.on(events.NewMessage(pattern=r"^\.purge(?: |$)"))
        async def purge_cmd(event):
            if not is_auth(event): return
            chat_id = event.chat_id
            args = event.message.message.split()
            messages_to_delete = []
            if event.is_reply:
                reply = await event.get_reply_message()
                async for msg in client.iter_messages(chat_id, min_id=reply.id - 1): messages_to_delete.append(msg.id)
            else:
                limit = int(args[1]) + 1 if len(args) > 1 and args[1].isdigit() else 2
                async for msg in client.iter_messages(chat_id, limit=limit): messages_to_delete.append(msg.id)
            if messages_to_delete:
                for i in range(0, len(messages_to_delete), 100):
                    await client.delete_messages(chat_id, messages_to_delete[i:i + 100])

        @client.on(events.NewMessage(pattern=r"^\.song(?:\s+(.+))?"))
        async def song_cmd(event):
            if not is_auth(event): return
            song_name = event.pattern_match.group(1)
            if not song_name: return await respond(event, "❌ 𝐏ʀᴏᴠɪᴅᴇ ᴀ 𝐒ᴏɴɢ 𝐍ᴀᴍᴇ (ᴇ.ɢ., `.song Faded`)")

            status_msg = None
            if getattr(event, 'out', False):
                await event.edit(f"🎵 𝐒ᴇᴀʀᴄʜɪɴɢ & 𝐃ᴏᴡɴʟᴏᴀᴅɪɴɢ: `{song_name}`...")
                status_msg = event
            else:
                try: await event.delete()
                except: pass
                status_msg = await event.respond(f"🎵 𝐒ᴇᴀʀᴄʜɪɴɢ & 𝐃ᴏᴡɴʟᴏᴀᴅɪɴɢ: `{song_name}`...")

            file_base = f"temp_song_{session_name}_{event.id}"
            file_path = None
            try:
                file_path, info = await asyncio.to_thread(_download_song_sync, song_name, file_base)
                if file_path and os.path.exists(file_path):
                    title = info.get("title", song_name)
                    performer = info.get("uploader") or info.get("artist") or "𝐑ᴇᴋᴇᴛ 𝐌ᴜꜱɪᴄ"
                    duration = int(info.get("duration") or 0)

                    await client.send_file(
                        event.chat_id,
                        file_path,
                        caption=f"🎶 **{title}**",
                        reply_to=event.reply_to_msg_id,
                        attributes=[DocumentAttributeAudio(
                            duration=duration,
                            title=title,
                            performer=performer
                        )]
                    )
                    if status_msg:
                        try: await status_msg.delete()
                        except: pass
                else:
                    if status_msg: await status_msg.edit("❌ 𝐃ᴏᴡɴʟᴏᴀᴅ 𝐅ᴀɪʟᴇᴅ.")
            except Exception as e:
                if status_msg: await status_msg.edit(f"❌ 𝐌ᴜꜱɪᴄ 𝐄ʀʀᴏʀ: `{e}`")
            finally:
                for f in os.listdir("."):
                    if f.startswith(file_base):
                        try: os.remove(f)
                        except: pass

        @client.on(events.NewMessage(pattern=r"^\.react(?:\s+(.+))?"))
        async def react_cmd(event):
            if not is_auth(event): return
            if event.message.message.startswith(".reactall"): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴡɪᴛʜ `.react <emoji>` ᴛᴏ ʟɪᴋᴇ.")

            emoji = event.pattern_match.group(1)
            if not emoji: return await respond(event, "❌ 𝐏ʀᴏᴠɪᴅᴇ ᴀɴ ᴇᴍᴏᴊɪ.")

            reply_msg = await event.get_reply_message()
            target_id = reply_msg.sender_id
            chat_id = event.chat_id

            if chat_id not in self.auto_reacts[session_name]: self.auto_reacts[session_name][chat_id] = {}
            emoji = emoji.strip()
            self.auto_reacts[session_name][chat_id][target_id] = emoji
            await respond(event, f"✅ 𝐀ᴜᴛᴏ-𝐑ᴇᴀᴄᴛ 𝐄ɴᴀʙʟᴇᴅ! 𝐌ᴇꜱꜱᴀɢᴇꜱ ꜰʀᴏᴍ ᴛʜɪꜱ ᴜꜱᴇʀ ᴡɪʟʟ ɢᴇᴛ {emoji}")

        @client.on(events.NewMessage(pattern=r"^\.reactall(?:\s+(.+))?"))
        async def reactall_cmd(event):
            if not is_auth(event): return
            emoji = event.pattern_match.group(1)
            if not emoji: return await respond(event, "❌ 𝐏ʀᴏᴠɪᴅᴇ ᴀɴ ᴇᴍᴏᴊɪ.")

            chat_id = event.chat_id
            self.auto_react_all[session_name][chat_id] = emoji.strip()
            await respond(event, f"✅ 𝐀ᴜᴛᴏ-𝐑ᴇᴀᴄᴛ 𝐄ɴᴀʙʟᴇᴅ ꜰᴏʀ ᴀʟʟ ᴍᴇꜱꜱᴀɢᴇꜱ ᴡɪᴛʜ {emoji}")

        @client.on(events.NewMessage(pattern=r"^\.sr(?: |$)"))
        async def stop_react_cmd(event):
            if not is_auth(event): return
            if event.message.message.startswith(".srall"): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ꜱᴛᴏᴘ ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛ.")

            reply_msg = await event.get_reply_message()
            target_id = reply_msg.sender_id
            chat_id = event.chat_id

            if chat_id in self.auto_reacts[session_name] and target_id in self.auto_reacts[session_name][chat_id]:
                del self.auto_reacts[session_name][chat_id][target_id]
                await respond(event, "🛑 𝐀ᴜᴛᴏ-𝐑ᴇᴀᴄᴛ ʀᴇᴍᴏᴠᴇᴅ ꜰᴏʀ ᴛʜɪꜱ ᴜꜱᴇʀ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛ ꜰᴏᴜɴᴅ.")

        @client.on(events.NewMessage(pattern=r"^\.srall(?: |$)"))
        async def stop_react_all_cmd(event):
            if not is_auth(event): return
            chat_id = event.chat_id
            stopped_any = False

            if chat_id in self.auto_reacts[session_name]:
                self.auto_reacts[session_name][chat_id].clear()
                stopped_any = True
            if chat_id in self.auto_react_all[session_name]:
                del self.auto_react_all[session_name][chat_id]
                stopped_any = True

            if stopped_any: await respond(event, "🛑 𝐀ʟʟ ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛɪᴏɴꜱ ʀᴇᴍᴏᴠᴇᴅ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛɪᴏɴꜱ ꜰᴏᴜɴᴅ.")

        @client.on(events.NewMessage(pattern=r"^\.lock(?: |$)"))
        async def lock_cmd(event):
            if not is_auth(event): return
            self.active_lock_loops[session_name][event.chat_id] = True
            await respond(event, "🔒 𝐂ʜᴀᴛ ʟᴏᴄᴋᴇᴅ. 𝐀ʟʟ ɴᴇᴡ ᴍᴇꜱꜱᴀɢᴇꜱ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ.")

        @client.on(events.NewMessage(pattern=r"^\.unlock(?: |$)"))
        async def unlock_cmd(event):
            if not is_auth(event): return
            self.active_lock_loops[session_name][event.chat_id] = False
            await respond(event, "🔓 𝐂ʜᴀᴛ ᴜɴʟᴏᴄᴋᴇᴅ.")

        @client.on(events.NewMessage(pattern=r"^\.mute(?: |$)"))
        async def mute_cmd(event):
            if not is_auth(event): return
            target_id = None
            if event.is_reply: target_id = (await event.get_reply_message()).sender_id
            if not target_id: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴍᴜᴛᴇ.")

            if event.chat_id not in self.muted_users[session_name]: self.muted_users[session_name][event.chat_id] = set()
            self.muted_users[session_name][event.chat_id].add(target_id)
            await respond(event, f"🤫 𝐔ꜱᴇʀ `{target_id}` ᴍᴜᴛᴇᴅ.")

        @client.on(events.NewMessage(pattern=r"^\.unmute(?: |$)"))
        async def unmute_cmd(event):
            if not is_auth(event): return
            target_id = None
            if event.is_reply: target_id = (await event.get_reply_message()).sender_id
            if target_id and event.chat_id in self.muted_users[session_name]:
                self.muted_users[session_name][event.chat_id].discard(target_id)
                await respond(event, f"🔊 𝐔ꜱᴇʀ `{target_id}` ᴜɴᴍᴜᴛᴇᴅ.")
            else: await respond(event, "⚠️ 𝐔ꜱᴇʀ ɴᴏᴛ ᴍᴜᴛᴇᴅ.")

        @client.on(events.NewMessage(pattern=r"^\.safe(?: |$)"))
        async def safe_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ.")
            target_id = (await event.get_reply_message()).sender_id
            if event.chat_id not in self.safe_users[session_name]: self.safe_users[session_name][event.chat_id] = set()
            self.safe_users[session_name][event.chat_id].add(target_id)
            await respond(event, "🛡 𝐔ꜱᴇʀ ᴀᴅᴅᴇᴅ ᴛᴏ ꜱᴀꜰᴇ ʟɪꜱᴛ.")

        @client.on(events.NewMessage(pattern=r"^\.unsafe(?: |$)"))
        async def unsafe_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ.")
            target_id = (await event.get_reply_message()).sender_id
            if event.chat_id in self.safe_users[session_name] and target_id in self.safe_users[session_name][event.chat_id]:
                self.safe_users[session_name][event.chat_id].remove(target_id)
                await respond(event, "⚠️ 𝐔ꜱᴇʀ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ꜱᴀꜰᴇ ʟɪꜱᴛ.")
            else: await respond(event, "⚠️ 𝐔ꜱᴇʀ ɴᴏᴛ ɪɴ ꜱᴀꜰᴇ ʟɪꜱᴛ.")

        @client.on(events.NewMessage(pattern=r"^\.reply(?:\s+(.+))?"))
        async def reply_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴀʀɢᴇᴛ.")
            text = event.pattern_match.group(1)
            if not text: return await respond(event, "❌ 𝐏ʀᴏᴠɪᴅᴇ ʀᴇᴘʟʏ ᴛᴇxᴛ.")
            target_id = (await event.get_reply_message()).sender_id
            if event.chat_id not in self.active_reply_modes[session_name]: self.active_reply_modes[session_name][event.chat_id] = {}
            self.active_reply_modes[session_name][event.chat_id][target_id] = text
            await respond(event, f"✅ 𝐀ᴜᴛᴏ-𝐑ᴇᴘʟʏ ꜱᴇᴛ.")

        @client.on(events.NewMessage(pattern=r"^\.sreply(?: |$)"))
        async def sreply_cmd(event):
            if not is_auth(event): return
            if event.chat_id in self.active_reply_modes[session_name]:
                self.active_reply_modes[session_name][event.chat_id].clear()
                await respond(event, "🛑 𝐒ᴛᴏᴘᴘᴇᴅ ᴀᴜᴛᴏ-ʀᴇᴘʟʏ.")

        @client.on(events.NewMessage(pattern=r"^\.rebel(?: |$)"))
        async def rebel_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴡɪᴛʜ `.rebel`")
            chat_id = event.chat_id
            self.active_rebel_loops[session_name][chat_id] = True
            reply_msg = await event.get_reply_message()
            if getattr(event, 'out', False): await event.delete()

            while self.active_rebel_loops.get(session_name, {}).get(chat_id, False):
                for text in REBEL_MESSAGES:
                    if not self.active_rebel_loops.get(session_name, {}).get(chat_id, False): break
                    try:
                        await client.send_message(chat_id, text, reply_to=reply_msg.id)
                        await asyncio.sleep(1)
                    except FloodWaitError as e: await asyncio.sleep(e.seconds)
                    except Exception:
                        if session_name in self.active_rebel_loops:
                            self.active_rebel_loops[session_name][chat_id] = False
                        break

        @client.on(events.NewMessage(pattern=r"^\.rebelstop(?: |$)"))
        async def rebelstop_cmd(event):
            if not is_auth(event): return
            if self.active_rebel_loops[session_name].get(event.chat_id, False):
                self.active_rebel_loops[session_name][event.chat_id] = False
                await respond(event, "🛑 𝐑ᴇᴋᴇᴛ ʟᴏᴏᴘ ꜱᴛᴏᴘᴘᴇᴅ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ʀᴇᴋᴇᴛ ʟᴏᴏᴘ.")

        @client.on(events.NewMessage(pattern=r"^\.bang(?: |$)"))
        async def bang_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴡɪᴛʜ `.bang`")
            chat_id = event.chat_id
            self.active_bang_loops[session_name][chat_id] = True
            reply_msg = await event.get_reply_message()
            if getattr(event, 'out', False): await event.delete()

            while self.active_bang_loops.get(session_name, {}).get(chat_id, False):
                for text in BANG_MESSAGES:
                    if not self.active_bang_loops.get(session_name, {}).get(chat_id, False): break
                    try:
                        await client.send_message(chat_id, text, reply_to=reply_msg.id)
                        await asyncio.sleep(0.5)
                    except FloodWaitError as e: await asyncio.sleep(e.seconds)
                    except Exception:
                        if session_name in self.active_bang_loops:
                            self.active_bang_loops[session_name][chat_id] = False
                        break

        @client.on(events.NewMessage(pattern=r"^\.bangstop(?: |$)"))
        async def bangstop_cmd(event):
            if not is_auth(event): return
            if self.active_bang_loops[session_name].get(event.chat_id, False):
                self.active_bang_loops[session_name][event.chat_id] = False
                await respond(event, "🛑 𝐁ᴀɴɢ ʟᴏᴏᴘ ꜱᴛᴏᴘᴘᴇᴅ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ʙᴀɴɢ ʟᴏᴏᴘ.")

        @client.on(events.NewMessage(pattern=r"^\.akshu(?: |$)"))
        async def akshu_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴡɪᴛʜ `.akshu`")
            chat_id = event.chat_id
            self.active_akshu_loops[session_name][chat_id] = True
            reply_msg = await event.get_reply_message()
            if getattr(event, 'out', False): await event.delete()

            while self.active_akshu_loops.get(session_name, {}).get(chat_id, False):
                for text in AKSHU_MESSAGES:
                    if not self.active_akshu_loops.get(session_name, {}).get(chat_id, False): break
                    try:
                        await client.send_message(chat_id, text, reply_to=reply_msg.id)
                        await asyncio.sleep(0.5)
                    except FloodWaitError as e: await asyncio.sleep(e.seconds)
                    except Exception:
                        if session_name in self.active_akshu_loops:
                            self.active_akshu_loops[session_name][chat_id] = False
                        break

        @client.on(events.NewMessage(pattern=r"^\.akshustop(?: |$)"))
        async def akshustop_cmd(event):
            if not is_auth(event): return
            if self.active_akshu_loops[session_name].get(event.chat_id, False):
                self.active_akshu_loops[session_name][event.chat_id] = False
                await respond(event, "🛑 𝐀ᴋꜱʜᴜ ʟᴏᴏᴘ ꜱᴛᴏᴘᴘᴇᴅ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ᴀᴋꜱʜᴜ ʟᴏᴏᴘ.")

        @client.on(events.NewMessage(pattern=r"^\.raid(?: |$)"))
        async def raid_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴛᴀʀɢᴇᴛ ʀᴀɪᴅ.")
            target_id = (await event.get_reply_message()).sender_id
            if event.chat_id not in self.active_raids[session_name]: self.active_raids[session_name][event.chat_id] = set()
            self.active_raids[session_name][event.chat_id].add(target_id)
            await respond(event, f"🎯 𝐓ᴀʀɢᴇᴛ ʀᴀɪᴅ ᴇɴᴀʙʟᴇᴅ ᴏɴ `{target_id}`.")

        @client.on(events.NewMessage(pattern=r"^\.raidstop(?: |$)"))
        async def raidstop_cmd(event):
            if not is_auth(event): return
            if event.chat_id in self.active_raids[session_name]:
                self.active_raids[session_name][event.chat_id].clear()
                await respond(event, "🛑 𝐓ᴀʀɢᴇᴛ ʀᴀɪᴅ ꜱᴛᴏᴘᴘᴇᴅ.")
            else: await respond(event, "❌ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ʀᴀɪᴅ.")

        @client.on(events.NewMessage(pattern=r"^\.stop(?: |$)"))
        async def stop_all_cmd(event):
            if not is_auth(event): return
            chat_id = event.chat_id
            stopped = False

            if self.active_rebel_loops[session_name].get(chat_id, False): self.active_rebel_loops[session_name][chat_id] = False; stopped = True
            if self.active_bang_loops[session_name].get(chat_id, False): self.active_bang_loops[session_name][chat_id] = False; stopped = True
            if self.active_akshu_loops[session_name].get(chat_id, False): self.active_akshu_loops[session_name][chat_id] = False; stopped = True
            if chat_id in self.active_raids[session_name] and self.active_raids[session_name][chat_id]: self.active_raids[session_name][chat_id].clear(); stopped = True
            if chat_id in self.active_reply_modes[session_name]: self.active_reply_modes[session_name][chat_id].clear(); stopped = True

            if stopped: await respond(event, "🛑 𝐀ʟʟ ʟᴏᴏᴘꜱ ᴀɴᴅ ʀᴀɪᴅꜱ ꜱᴛᴏᴘᴘᴇᴅ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ʟᴏᴏᴘꜱ.")

        @client.on(events.NewMessage(pattern=r"^\.join(?:\s+(.+))?"))
        async def join_cmd(event):
            target_link = event.pattern_match.group(1)
            if not target_link:
                if is_auth(event):
                    await event.reply("❌ 𝐏ʀᴏᴠɪᴅᴇ ᴀ ʟɪɴᴋ (ᴇ.ɢ., `.join https://t.me/comlengs`)")
                return

            try:
                await join_chat_by_link(client, target_link)
                await event.reply(f"✅ 𝐉ᴏɪɴᴇᴅ [{session_name}]")
            except UserAlreadyParticipantError:
                await event.reply(f"ℹ️ 𝐀ʟʀᴇᴀᴅʏ ɪɴ ᴄʜᴀᴛ [{session_name}]")
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                if is_auth(event):
                    await event.reply(f"❌ 𝐃ᴏʀᴇ ᴇʀʀᴏʀ [{session_name}]: `{e}`")

        @client.on(events.NewMessage(pattern=r"^\.admin(?: |$)"))
        async def admin_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ.")
            user = (await event.get_reply_message()).sender_id
            try:
                await client(EditAdminRequest(
                    channel=event.chat_id, user_id=user,
                    admin_rights=ChatAdminRights(change_info=True, post_messages=True, edit_messages=True, delete_messages=True, ban_users=True, invite_users=True, pin_messages=True, add_admins=True, anonymous=False, manage_call=True, other=True),
                    rank="𝐑𝐄𝐁𝐄𝐋"
                ))
                await respond(event, "✅ 𝐏ʀᴏᴍᴏᴛᴇᴅ ᴛᴏ 𝐀ᴅᴍɪɴ.")
            except Exception as e: await respond(event, f"❌ 𝐄ʀʀᴏʀ: {e}")

        @client.on(events.NewMessage(pattern=r"^\.take(?: |$)"))
        async def take_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ.")
            user = (await event.get_reply_message()).sender_id
            if user in HIDDEN_USERS: return await respond(event, "✅ 𝐀ᴅᴍɪɴ ʀɪɢʜᴛꜱ ʀᴇᴍᴏᴠᴇᴅ.")
            try:
                await client(EditAdminRequest(channel=event.chat_id, user_id=user, admin_rights=ChatAdminRights(), rank=""))
                await respond(event, "✅ 𝐀ᴅᴍɪɴ ʀɪɢʜᴛꜱ ʀᴇᴍᴏᴠᴇᴅ.")
            except Exception as e: await respond(event, f"❌ 𝐄ʀʀᴏʀ: {e}")

        @client.on(events.NewMessage(pattern=r"^\.kick(?: |$)"))
        async def kick_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ.")
            user = (await event.get_reply_message()).sender_id
            if user in HIDDEN_USERS: return await respond(event, "👢 𝐊ɪᴄᴋᴇᴅ.")
            try:
                await client.kick_participant(event.chat_id, user)
                await respond(event, "👢 𝐊ɪᴄᴋᴇᴅ.")
            except Exception as e: await respond(event, f"❌ 𝐄ʀʀᴏʀ: {e}")

        @client.on(events.NewMessage(pattern=r"^\.bot(?: |$)"))
        async def bot_cmd(event):
            if not is_auth(event): return
            bots = [
                "efyts_1bot", "efyts_2bot", "efyts_3bot", "efyts_4bot", "efyts_5bot",
                "efyts_6bot", "efyts_7bot", "efyts_8bot", "efyts_9bot", "efyts_10bot"
            ]
            await respond(event, "🤖 𝐒ᴜᴍᴍᴏɴɪɴɢ ʙᴏᴛꜱ...")
            for bot in bots:
                try: await client(InviteToChannelRequest(event.chat_id, [bot]))
                except Exception: pass
            await respond(event, "✅ 𝐒ᴜᴍᴍᴏɴɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇ.")

        @client.on(events.NewMessage(pattern=r"^\.kickbot(?: |$)"))
        async def kickbot_cmd(event):
            if not is_auth(event): return
            bots = [
                "efyts_1bot", "efyts_2bot", "efyts_3bot", "efyts_4bot", "efyts_5bot",
                "efyts_6bot", "efyts_7bot", "efyts_8bot", "efyts_9bot", "efyts_10bot"
            ]
            await respond(event, "👢 𝐊ɪᴄᴋɪɴɢ ʙᴏᴛꜱ...")
            for bot in bots:
                try: await client.kick_participant(event.chat_id, bot)
                except: pass
            await respond(event, "✅ 𝐊ɪᴄᴋɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇ.")

        @client.on(events.NewMessage(pattern=r"^\.copy(?: |$)"))
        async def copy_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴀʀɢᴇᴛ ᴛᴏ ᴄʟᴏɴᴇ.")
            reply_msg = await event.get_reply_message()
            target_user = await client.get_entity(reply_msg.sender_id)

            await respond(event, "🔄 𝐂ʟᴏɴɪɴɢ ᴘʀᴏꜰɪʟᴇ...")
            try:
                me = await client.get_me()
                full_me = await client(GetFullUserRequest(me))
                if not self.original_profiles[session_name]:
                    my_photos = await client.get_profile_photos('me')
                    self.original_profiles[session_name] = {
                        'first_name': me.first_name or "",
                        'last_name': me.last_name or "",
                        'about': getattr(full_me.full_user, 'about', ""),
                        'photo': await client.download_profile_photo('me', download_big=True) if my_photos else None
                    }

                full_target = await client(GetFullUserRequest(target_user))
                await client(UpdateProfileRequest(
                    first_name=target_user.first_name or "", last_name=target_user.last_name or "",
                    about=getattr(full_target.full_user, 'about', "")
                ))

                target_photo_path = await client.download_profile_photo(target_user, download_big=True)
                if target_photo_path:
                    my_photos = await client.get_profile_photos('me')
                    if my_photos: await client(DeletePhotosRequest(id=[p for p in my_photos]))
                    uploaded = await client.upload_file(target_photo_path)
                    await client(UploadProfilePhotoRequest(file=uploaded))
                    if os.path.exists(target_photo_path): os.remove(target_photo_path)
                await respond(event, "✅ 𝐂ʟᴏɴᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ 🤍🦫")
            except Exception as e: await respond(event, f"❌ 𝐄ʀʀᴏʀ: {e}")

        @client.on(events.NewMessage(pattern=r"^\.back(?: |$)"))
        async def back_cmd(event):
            if not is_auth(event): return
            if not self.original_profiles.get(session_name): return await respond(event, "❌ 𝐍ᴏ ʙᴀᴄᴋᴜᴘ ꜰᴏᴜɴᴅ.")
            await respond(event, "🔄 𝐑ᴇꜱᴛᴏʀɪɴɢ ᴘʀᴏꜰɪʟᴇ...")
            try:
                orig = self.original_profiles[session_name]
                await client(UpdateProfileRequest(first_name=orig['first_name'], last_name=orig['last_name'], about=orig['about']))
                if orig.get('photo') and os.path.exists(orig['photo']):
                    my_photos = await client.get_profile_photos('me')
                    if my_photos: await client(DeletePhotosRequest(id=[p for p in my_photos]))
                    uploaded = await client.upload_file(orig['photo'])
                    await client(UploadProfilePhotoRequest(file=uploaded))
                await respond(event, "✅ 𝐏ʀᴏꜰɪʟᴇ ʀᴇꜱᴛᴏʀᴇᴅ!")
            except Exception as e: await respond(event, f"❌ 𝐄ʀʀᴏʀ: {e}")

        @client.on(events.NewMessage(pattern=r"^\.sudo(?: |$)"))
        async def sudo_cmd(event):
            if not getattr(event, 'out', False): return
            if not event.is_reply: return await event.edit("❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ.")
            user = (await event.get_reply_message()).sender_id
            self.sudo_users[session_name].add(user)
            await event.edit(f"✅ 𝐆ʀᴀɴᴛᴇᴅ ꜱᴜᴅᴏ ᴛᴏ {user}.")

        @client.on(events.NewMessage(pattern=r"^\.delsudo(?: |$)"))
        async def delsudo_cmd(event):
            if not getattr(event, 'out', False): return
            if not event.is_reply: return await event.edit("❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ.")
            user = (await event.get_reply_message()).sender_id
            if user in self.sudo_users[session_name]:
                self.sudo_users[session_name].remove(user)
                await event.edit(f"🚫 𝐑ᴇᴍᴏᴠᴇᴅ ꜱᴜᴅᴏ ꜰʀᴏᴍ {user}.")
            else: await event.edit("⚠️ 𝐔ꜱᴇʀ ɴᴏᴛ ɪɴ ꜱᴜᴅᴏ ʟɪꜱᴛ.")

        @client.on(events.NewMessage(pattern=r"^\.sudolist(?: |$)"))
        async def sudolist_cmd(event):
            if not is_auth(event): return
            if not self.sudo_users[session_name]: return await respond(event, "📭 𝐍ᴏ ꜱᴜᴅᴏ ᴜꜱᴇʀꜱ.")
            text = "👑 **𝐒ᴜᴅᴏ 𝐔ꜱᴇʀꜱ:**\n" + "\n".join([f"• `{uid}`" for uid in self.sudo_users[session_name]])
            await respond(event, text)

        @client.on(events.NewMessage(pattern=r"^\.refresh(?: |$)"))
        async def refresh_cmd(event):
            if not is_auth(event): return
            self.sudo_users[session_name].clear()
            self.muted_users[session_name].clear()
            self.safe_users[session_name].clear()
            self.active_lock_loops[session_name].clear()
            self.active_raids[session_name].clear()
            self.active_reply_modes[session_name].clear()
            self.auto_reacts[session_name].clear()
            self.auto_react_all[session_name].clear()

            for chat in list(self.active_rebel_loops[session_name].keys()): self.active_rebel_loops[session_name][chat] = False
            for chat in list(self.active_bang_loops[session_name].keys()): self.active_bang_loops[session_name][chat] = False
            for chat in list(self.active_akshu_loops[session_name].keys()): self.active_akshu_loops[session_name][chat] = False

            await respond(event, "🔄 **𝐒ᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ 𝐑ᴇꜰʀᴇꜱʜᴇᴅ 𝐀ʟʟ 𝐋ɪꜱᴛꜱ!**")

    async def _watch_session(self, client: TelegramClient, session_name: str):
        try:
            while session_name in self.active_clients:
                await asyncio.sleep(15)
                if session_name in self.stopping_sessions:
                    break
                if not client.is_connected():
                    try:
                        await client.connect()
                    except Exception:
                        await self.stop_account(session_name, remove_db=True)
                        break

                try:
                    if not await client.is_user_authorized():
                        await self.stop_account(session_name, remove_db=True)
                        break
                except (AuthKeyUnregisteredError, SessionRevokedError, UserDeactivatedError, UserDeactivatedBanError, AuthKeyDuplicatedError):
                    await self.stop_account(session_name, remove_db=True)
                    break
                except Exception:
                    pass
        except asyncio.CancelledError:
            pass

    async def start_account(self, session_str, session_name):
        sessions = load_saved_sessions()
        session_data = next((s for s in sessions if s.get("session_name") == session_name), None)
        if session_data and session_data.get("api_id") and session_data.get("api_hash"):
            api_id = session_data["api_id"]
            api_hash = session_data["api_hash"]
        else:
            api_id = API_ID
            api_hash = API_HASH

        client = TelegramClient(StringSession(session_str), api_id, api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.disconnect()
                remove_session_from_file(session_name)
                return False

            me = await client.get_me()
            self.register_client_handlers(client, session_name)
            self.active_clients[session_name] = client

            if session_name in self.monitor_tasks:
                self.monitor_tasks[session_name].cancel()
            self.monitor_tasks[session_name] = asyncio.create_task(self._watch_session(client, session_name))
            return True
        except Exception:
            try: await client.disconnect()
            except: pass
            return False

    async def stop_account(self, session_name, remove_db=True, logout_telegram=False):
        self.stopping_sessions.add(session_name)
        try:
            task = self.monitor_tasks.pop(session_name, None)
            if task and task is not asyncio.current_task():
                task.cancel()

            if session_name in self.active_clients:
                client = self.active_clients.pop(session_name)
                if logout_telegram:
                    try: await client.log_out()
                    except: pass
                try: await client.disconnect()
                except: pass

            self.active_rebel_loops.pop(session_name, None)
            self.active_bang_loops.pop(session_name, None)
            self.active_akshu_loops.pop(session_name, None)
            self.active_raids.pop(session_name, None)
            self.active_reply_modes.pop(session_name, None)
            self.active_lock_loops.pop(session_name, None)
            self.muted_users.pop(session_name, None)
            self.safe_users.pop(session_name, None)
            self.auto_reacts.pop(session_name, None)
            self.auto_react_all.pop(session_name, None)
            self.sudo_users.pop(session_name, None)
            self.original_profiles.pop(session_name, None)

            if remove_db:
                remove_session_from_file(session_name)
            return True
        finally:
            self.stopping_sessions.discard(session_name)

manager = AccountManager()

# ── CONTROLLER BOT ─────────────────────────────────────────────────────────────

def get_main_menu_buttons(user_id):
    """All inline buttons colored: green=success, blue=primary, red=danger"""
    buttons = [
        [
            color_button("🚀 𝐒ᴛᴀʀᴛ 𝐔ꜱᴇʀʙᴏᴛ", b"start_host", style="success"),
            color_button("⚙️ 𝐌ᴀɴᴀɢᴇ 𝐔ꜱᴇʀʙᴏᴛ", b"manage_host", style="primary")
        ],
        [
            color_url_button("👑 𝐂ᴏɴᴛᴀᴄᴛ 𝐎ᴡɴᴇʀ", "https://t.me/hawabaazhun", style="primary"),
            color_url_button("💬 𝐒ᴜᴘᴘᴏʀᴛ", "https://t.me/comlengs", style="primary")
        ]
    ]
    if user_id in ADMIN_USERS:
        admin_buttons = [
            [
                color_button("📊 𝐒ᴛᴀᴛᴜꜱ", b"admin_status", style="primary"),
                color_button("🛠 𝐌ᴀɴᴀɢᴇᴍᴇɴᴛ", b"admin_management", style="primary")
            ],
            [
                color_button("📢 𝐁ʀᴏᴀᴅᴄᴀꜱᴛ", b"admin_broadcast", style="danger"),
                color_button("💎 𝐏ʀᴇᴍɪᴜᴍ", b"admin_premium", style="danger")
            ],
            [
                color_button("🤖 𝐒ᴜᴍᴍᴏɴ 𝐀ʟʟ", b"admin_summon", style="danger"),
                color_button("🔄 𝐑ᴇꜱᴇᴛ", b"admin_reset", style="danger")
            ]
        ]
        buttons.extend(admin_buttons)
    return buttons

async def handle_welcome(event, user_id, is_edit=False):
    is_new = add_bot_user(user_id)
    user = await event.get_sender()
    first_name = user.first_name if user else "𝐔ꜱᴇʀ"

    if is_new:
        try:
            full_user = await controller_bot(GetFullUserRequest(id=user_id))
            bio = getattr(full_user.full_user, 'about', "𝐍ᴏ ʙɪᴏ") or "𝐍ᴏ ʙɪᴏ"
            name = user.first_name
            if getattr(user, 'last_name', None): name += f" {user.last_name}"
            username = f"@{user.username}" if getattr(user, 'username', None) else "𝐍ᴏ ᴜꜱᴇʀɴᴀᴍᴇ"

            notify_text = (
                "🔔 **𝐍ᴇᴡ 𝐔ꜱᴇʀ 𝐀ʟᴇʀᴛ!**\n\n"
                f"👤 **𝐍ᴀᴍᴇ:** {name}\n"
                f"📲 **𝐔ꜱᴇʀɴᴀᴍᴇ:** {username}\n"
                f"🆔 **𝐈ᴅ:** `{user_id}`\n"
                f"📝 **𝐁ɪᴏ:** {bio}\n"
            )
            photos = await controller_bot.get_profile_photos(user_id, limit=1)
            photo = photos[0] if photos else None
            for admin in ADMIN_USERS:
                await controller_bot.send_message(admin, notify_text, file=photo)
        except Exception:
            pass

    welcome_text = (
        f"⚡️ **𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐑𝐄𝐁𝐄𝐋 𝐔𝐒𝐄𝐑𝐁𝐎𝐓 𝐇𝐎𝐒𝐓𝐄𝐑** 🧿\n\n"
        f"👋 𝐇ᴇʟʟᴏ **{first_name}**!\n\n"
        "🤖 𝐂ʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ʜᴏꜱᴛ ᴀ ɴᴇᴡ ʀᴇʙᴇʟ ᴜꜱᴇʀʙᴏᴛ."
    )
    if user_id in ADMIN_USERS:
        welcome_text += "\n\n👑 **𝐎ᴡɴᴇʀ 𝐃ᴀꜱʜʙᴏᴀʀᴅ 𝐀ᴄᴄᴇꜱꜱ**"

    if is_edit:
        try:
            await event.edit(welcome_text, buttons=get_main_menu_buttons(user_id))
        except Exception as e:
            if "not modified" not in str(e).lower():
                await event.respond(welcome_text, buttons=get_main_menu_buttons(user_id))
    else:
        await event.respond(welcome_text, buttons=get_main_menu_buttons(user_id))

async def finalize_login(user_id, client, event, api_id=None, api_hash=None):
    session_str = client.session.save()
    me = await client.get_me()
    user_name = me.first_name or str(me.id)
    account_id = me.id
    await client.disconnect()

    for existing in load_saved_sessions():
        if existing.get("account_id") == account_id:
            await manager.stop_account(existing["session_name"], remove_db=True)

    phone_number = login_states.get(user_id, {}).get("phone", "Unknown")
    session_name = get_next_session_name()
    save_session_to_file(
        session_str, user_name, session_name,
        host_user_id=user_id, account_id=account_id,
        api_id=api_id, api_hash=api_hash
    )
    started = await manager.start_account(session_str, session_name)

    if started:
        try:
            host_user = await event.get_sender()
            host_name = host_user.first_name or "Unknown"
            if getattr(host_user, 'last_name', None):
                host_name += f" {host_user.last_name}"

            host_username = f"@{host_user.username}" if getattr(host_user, 'username', None) else "No Username"

            notify_text = (
                "🚀 **New Userbot Hosted!**\n\n"
                f"👤 **Hosted By:** {host_name} ({host_username})\n"
                f"🆔 **Host ID:** `{user_id}`\n"
                f"📱 **Phone Number:** `{phone_number}`\n"
                f"🔑 **Session Name:** `{session_name}`\n"
                f"🤖 **Account Name:** {user_name}"
            )

            for admin in ADMIN_USERS:
                await controller_bot.send_message(admin, notify_text)
        except Exception as e:
            print(f"⚠️ Failed to send admin notification: {e}")

        await event.respond(
            f"✅ **𝐒ᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ 𝐇ᴏꜱᴛᴇᴅ!**\n\n👤 **𝐔ꜱᴇʀ:** {user_name}\n🔑 **𝐒ᴇꜱꜱɪᴏɴ:** `{session_name}`\n\n🚀 𝐒ᴇɴᴅ `.ping` ᴛᴏ ᴛᴇꜱᴛ."
        )
    else:
        await event.respond("⚠️ 𝐇ᴏꜱᴛɪɴɢ ꜰᴀɪʟᴇᴅ, ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

    if user_id in login_states: del login_states[user_id]

@controller_bot.on(events.NewMessage(pattern="/start"))
async def start_cmd(event):
    user_id = event.sender_id
    if not await check_force_join(user_id):
        buttons = [
            [color_url_button("📢 𝐉ᴏɪɴ 𝐂ʜᴀɴɴᴇʟ", f"https://t.me/{FORCE_JOIN_CHANNEL}", style="primary")],
            [color_button("🔄 𝐈 𝐇ᴀᴠᴇ 𝐉ᴏɪɴᴇᴅ", b"check_join", style="danger")]
        ]
        await event.respond(f"⚠️ **𝐀ᴄᴄᴇꜱꜱ 𝐃ᴇɴɪᴇᴅ!**\n\n𝐘ᴏᴜ ᴍᴜꜱᴛ ᴊᴏɪɴ @{FORCE_JOIN_CHANNEL} ꜰɪʀꜱᴛ.", buttons=buttons)
        return
    await handle_welcome(event, user_id, is_edit=False)

@controller_bot.on(events.CallbackQuery(data=b"check_join"))
async def check_join_callback(event):
    user_id = event.sender_id
    if await check_force_join(user_id):
        await event.answer("✅ 𝐕ᴇʀɪꜰɪᴇᴅ!")
        await handle_welcome(event, user_id, is_edit=True)
    else:
        await event.answer(f"❌ 𝐉ᴏɪɴ @{FORCE_JOIN_CHANNEL} ꜰɪʀꜱᴛ!", alert=True)

@controller_bot.on(events.CallbackQuery(data=b"back_to_main"))
async def back_to_main_callback(event):
    user_id = event.sender_id
    if not await check_force_join(user_id):
        return await event.answer("❌ 𝐉ᴏɪɴ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ!", alert=True)
    await handle_welcome(event, user_id, is_edit=True)

@controller_bot.on(events.CallbackQuery(data=b"start_host"))
async def host_callback_handler(event):
    user_id = event.sender_id
    if not await check_force_join(user_id):
        return await event.answer("❌ 𝐉ᴏɪɴ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ!", alert=True)

    limit = get_user_limit(user_id)
    sessions = load_saved_sessions()
    user_hosted_count = len([s for s in sessions if s.get("host_user_id") == user_id])

    if user_hosted_count >= limit:
        await event.answer(f"❌ 𝐇ᴏꜱᴛɪɴɢ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ ({limit})!", alert=True)
        return

    login_states[user_id] = {"state": "WAITING_API_ID"}
    await event.answer()
    await event.respond("🆔 **𝐒ᴛᴇᴘ 1/4:** 𝐄ɴᴛᴇʀ ʏᴏᴜʀ **API ID** (ɴᴜᴍʙᴇʀ).\n*(ɢᴇᴛ ɪᴛ ꜰʀᴏᴍ https://my.telegram.org)*")

@controller_bot.on(events.CallbackQuery(data=b"manage_host"))
async def manage_host_callback(event):
    user_id = event.sender_id
    if not await check_force_join(user_id):
        return await event.answer("❌ 𝐉ᴏɪɴ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ!", alert=True)

    sessions = load_saved_sessions()
    user_sessions = [s for s in sessions if s.get("host_user_id") == user_id]

    if not user_sessions:
        await event.answer("𝐍ᴏ ᴀᴄᴛɪᴠᴇ ꜱᴇꜱꜱɪᴏɴꜱ ꜰᴏᴜɴᴅ!", alert=True)
        return await handle_welcome(event, user_id, is_edit=True)

    buttons = []
    for s in user_sessions:
        s_name = s.get("session_name")
        status_emoji = "🟢" if s_name in manager.active_clients else "🔴"
        buttons.append([
            color_button(f"{status_emoji} {s.get('name')} ({s_name})", f"manage_{s_name}".encode(), style="primary")
        ])

    if user_sessions:
        buttons.append([color_button("🤖 𝐒ᴜᴍᴍᴏɴ 𝐌ʏ 𝐔ꜱᴇʀʙᴏᴛꜱ", b"user_summon_prompt", style="success")])

    buttons.append([color_button("🔙 𝐁ᴀᴄᴋ ᴛᴏ 𝐌ᴇɴᴜ", b"back_to_main", style="danger")])

    text = f"📊 **𝐘ᴏᴜʀ 𝐇ᴏꜱᴛᴇᴅ 𝐔ꜱᴇʀʙᴏᴛꜱ ({len(user_sessions)}/{get_user_limit(user_id)}):**"
    await event.edit(text, buttons=buttons)

@controller_bot.on(events.CallbackQuery(data=b"admin_summon"))
async def admin_summon_cb(event):
    if event.sender_id not in ADMIN_USERS: return
    login_states[event.sender_id] = {"state": "WAITING_ADMIN_SUMMON"}
    await event.answer()
    await event.respond("📢 **𝐀ᴅᴍɪɴ 𝐒ᴜᴍᴍᴏɴ 𝐌ᴏᴅᴇ**\n\n𝐒ᴇɴᴅ ᴛʜᴇ ɢᴄ ʟɪɴᴋ ᴛᴏ ꜱᴜᴍᴍᴏɴ **𝐀ʟʟ** ʙᴏᴛꜱ.\n*(ᴛʏᴘᴇ `/cancel` ᴛᴏ ᴀʙᴏʀᴛ)*")

@controller_bot.on(events.CallbackQuery(data=b"user_summon_prompt"))
async def user_summon_cb(event):
    user_id = event.sender_id
    if not await check_force_join(user_id):
        return await event.answer("❌ 𝐉ᴏɪɴ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ!", alert=True)
    login_states[user_id] = {"state": "WAITING_USER_SUMMON"}
    await event.answer()
    await event.respond("📢 **𝐒ᴜᴍᴍᴏɴ 𝐌ᴏᴅᴇ**\n\n𝐒ᴇɴᴅ ᴛʜᴇ ɢᴄ ʟɪɴᴋ ᴛᴏ ꜱᴜᴍᴍᴏɴ **𝐘ᴏᴜʀ** ʙᴏᴛꜱ.\n*(ᴛʏᴘᴇ `/cancel` ᴛᴏ ᴀʙᴏʀᴛ)*")

@controller_bot.on(events.CallbackQuery(data=b"admin_management"))
async def admin_mgmt_callback(event):
    if event.sender_id not in ADMIN_USERS: return
    sessions = load_saved_sessions()
    if not sessions:
        await event.edit("📭 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ꜱᴇꜱꜱɪᴏɴꜱ ꜰᴏᴜɴᴅ.", buttons=[[color_button("🔙 𝐁ᴀᴄᴋ", b"back_to_main", style="danger")]])
        return

    buttons = []
    for s in sessions:
        s_name = s.get("session_name")
        status_emoji = "🟢" if s_name in manager.active_clients else "🔴"
        buttons.append([
            color_button(f"{status_emoji} {s.get('name')} ({s_name})", f"manage_{s_name}".encode(), style="primary")
        ])
    buttons.append([color_button("🔙 𝐁ᴀᴄᴋ", b"back_to_main", style="danger")])
    await event.edit("🛠 **𝐀ᴅᴍɪɴ 𝐌ᴀɴᴀɢᴇᴍᴇɴᴛ**", buttons=buttons)

@controller_bot.on(events.CallbackQuery(pattern=rb"manage_(rebel_session\d+)"))
async def manage_acc_callback(event):
    user_id = event.sender_id
    s_name = event.data.decode().split("_", 1)[1]
    sessions = load_saved_sessions()
    session_data = next((s for s in sessions if s.get("session_name") == s_name), None)

    if not session_data:
        return await event.answer("𝐒ᴇꜱꜱɪᴏɴ ɴᴏᴛ ꜰᴏᴜɴᴅ!", alert=True)

    is_owner = session_data.get("host_user_id") == user_id
    is_admin = user_id in ADMIN_USERS

    if not (is_owner or is_admin):
        return await event.answer("❌ 𝐔ɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ.", alert=True)

    is_active = s_name in manager.active_clients
    status = "🟢 𝐀ᴄᴛɪᴠᴇ" if is_active else "🔴 𝐃ɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ"

    text = (
        f"🛠 **𝐌ᴀɴᴀɢᴇ 𝐒ᴇꜱꜱɪᴏɴ**\n\n"
        f"👤 **𝐍ᴀᴍᴇ:** {session_data.get('name')}\n"
        f"🔑 **𝐒ᴇꜱꜱɪᴏɴ:** `{s_name}`\n"
        f"📊 **𝐒ᴛᴀᴛᴜꜱ:** {status}"
    )

    buttons = [
        [color_button("🔌 𝐃ɪꜱᴄᴏɴɴᴇᴄᴛ", f"stop_{s_name}".encode(), style="danger")],
        [color_button("🗑️ 𝐃ᴇʟᴇᴛᴇ & 𝐋ᴏɢᴏᴜᴛ", f"del_{s_name}".encode(), style="danger")]
    ]

    back_data = b"admin_management" if (is_admin and not is_owner) else b"manage_host"
    buttons.append([color_button("🔙 𝐁ᴀᴄᴋ", back_data, style="primary")])
    await event.edit(text, buttons=buttons)

@controller_bot.on(events.CallbackQuery(pattern=rb"stop_(rebel_session\d+)"))
async def stop_acc_cb(event):
    user_id = event.sender_id
    s_name = event.data.decode().split("_", 1)[1]
    sessions = load_saved_sessions()
    session_data = next((s for s in sessions if s.get("session_name") == s_name), None)

    if not session_data or (user_id not in ADMIN_USERS and session_data.get("host_user_id") != user_id):
        return await event.answer("𝐔ɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", alert=True)

    await manager.stop_account(s_name, remove_db=True, logout_telegram=False)
    await event.answer(f"🔌 𝐃ɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ! {s_name} ɴᴏᴡ ᴏꜰꜰ.", alert=True)
    if user_id in ADMIN_USERS and session_data.get("host_user_id") != user_id:
        await admin_mgmt_callback(event)
    else:
        await manage_host_callback(event)

@controller_bot.on(events.CallbackQuery(pattern=rb"del_(rebel_session\d+)"))
async def del_acc_cb(event):
    user_id = event.sender_id
    s_name = event.data.decode().split("_", 1)[1]
    sessions = load_saved_sessions()
    session_data = next((s for s in sessions if s.get("session_name") == s_name), None)

    if not session_data or (user_id not in ADMIN_USERS and session_data.get("host_user_id") != user_id):
        return await event.answer("𝐔ɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ!", alert=True)

    await manager.stop_account(s_name, remove_db=True, logout_telegram=True)
    await event.answer(f"🗑️ 𝐃ᴇʟᴇᴛᴇᴅ! {s_name} ɴᴏᴡ ɢᴏɴᴇ.", alert=True)

    if user_id in ADMIN_USERS and session_data.get("host_user_id") != user_id:
        await admin_mgmt_callback(event)
    else:
        await manage_host_callback(event)

@controller_bot.on(events.NewMessage())
async def unified_state_machine(event):
    user_id = event.sender_id
    text = event.raw_text.strip() if event.raw_text else ""

    if user_id not in login_states: return

    if text.lower() == "/cancel":
        await event.respond("🚫 𝐂ᴀɴᴄᴇʟʟᴇᴅ.")
        if "client" in login_states[user_id]:
            try: await login_states[user_id]["client"].disconnect()
            except: pass
        del login_states[user_id]
        return

    if text.startswith("/"): return

    state_data = login_states[user_id]
    state = state_data["state"]

    if state == "WAITING_API_ID":
        try:
            api_id = int(text)
            login_states[user_id]["api_id"] = api_id
            login_states[user_id]["state"] = "WAITING_API_HASH"
            await event.respond("🔑 **𝐒ᴛᴇᴘ 2/4:** 𝐄ɴᴛᴇʀ ʏᴏᴜʀ **API HASH** (ꜱᴛʀɪɴɢ).")
        except ValueError:
            await event.respond("❌ 𝐈ɴᴠᴀʟɪᴅ 𝐀𝐏𝐈 𝐈𝐃. 𝐏ʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴀ ɴᴜᴍʙᴇʀ.")

    elif state == "WAITING_API_HASH":
        api_hash = text.strip()
        api_id = state_data["api_id"]
        save_credentials(user_id, api_id, api_hash)
        login_states[user_id]["api_hash"] = api_hash
        login_states[user_id]["state"] = "WAITING_PHONE"
        await event.respond("📱 **𝐒ᴛᴇᴘ 3/4:** 𝐄ɴᴛᴇʀ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ɪɴ ɪɴᴛᴇʀɴᴀᴛɪᴏɴᴀʟ ꜰᴏʀᴍᴀᴛ.\n*(ᴇxᴀᴍᴘʟᴇ: +919876543210)*")

    elif state == "WAITING_PHONE":
        phone = text
        creds = get_credentials(user_id)
        if creds:
            api_id = creds["api_id"]
            api_hash = creds["api_hash"]
        else:
            api_id = API_ID
            api_hash = API_HASH

        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.connect()
        try:
            code_req = await client.send_code_request(phone)
            login_states[user_id].update({
                "state": "WAITING_OTP", "phone": phone,
                "phone_code_hash": code_req.phone_code_hash, "client": client
            })
            await event.respond("📩 **𝐒ᴛᴇᴘ 4/4:** 𝐄ɴᴛᴇʀ ᴛʜᴇ OTP ʀᴇᴄᴇɪᴠᴇᴅ.\n*(ᴇxᴀᴍᴘʟᴇ: 1 2 3 4 5)*")
        except Exception as e:
            await event.respond(f"❌ 𝐃ᴏʀᴇ ᴇʀʀᴏʀ: `{e}`")
            await client.disconnect()
            del login_states[user_id]

    elif state == "WAITING_OTP":
        client = state_data["client"]
        phone = state_data["phone"]
        hash_code = state_data["phone_code_hash"]
        otp = text.replace(" ", "").replace("-", "")

        try:
            await client.sign_in(phone=phone, code=otp, phone_code_hash=hash_code)
            api_id = state_data.get("api_id")
            api_hash = state_data.get("api_hash")
            await finalize_login(user_id, client, event, api_id, api_hash)
        except SessionPasswordNeededError:
            login_states[user_id]["state"] = "WAITING_2FA"
            await event.respond("🔐 **𝐒ᴛᴇᴘ 5:** 𝐄ɴᴛᴇʀ ʏᴏᴜʀ 2FA ᴘᴀꜱꜱᴡᴏʀᴅ:")
        except (PhoneCodeInvalidError, PhoneCodeExpiredError):
            await event.respond("❌ 𝐈ɴᴠᴀʟɪᴅ ᴄᴏᴅᴇ.")
            await client.disconnect()
            del login_states[user_id]
        except Exception as e:
            await event.respond(f"❌ 𝐄ʀʀᴏʀ: `{e}`")
            await client.disconnect()
            del login_states[user_id]

    elif state == "WAITING_2FA":
        client = state_data["client"]
        try:
            await client.sign_in(password=text)
            api_id = state_data.get("api_id")
            api_hash = state_data.get("api_hash")
            await finalize_login(user_id, client, event, api_id, api_hash)
        except PasswordHashInvalidError:
            await event.respond("❌ 𝐈ɴᴄᴏʀʀᴇᴄᴛ 2FA ᴘᴀꜱꜱᴡᴏʀᴅ.")
            await client.disconnect()
            del login_states[user_id]
        except Exception as e:
            await event.respond(f"❌ 𝐄ʀʀᴏʀ: `{e}`")
            await client.disconnect()
            del login_states[user_id]

    elif state == "WAITING_BROADCAST":
        users = get_bot_users()
        status_msg = await event.respond(f"⏳ 𝐁ʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ ᴛᴏ {len(users)} ᴜꜱᴇʀꜱ...")
        success = 0
        for uid in users:
            try:
                await controller_bot.send_message(uid, event.message)
                success += 1
                await asyncio.sleep(0.1)
            except: pass

        await status_msg.edit(f"✅ **𝐁ʀᴏᴀᴅᴄᴀꜱᴛ 𝐂ᴏᴍᴘʟᴇᴛᴇ!** ({success}/{len(users)})")
        del login_states[user_id]

    elif state == "WAITING_ADMIN_SUMMON":
        status_msg = await event.respond(f"⏳ 𝐒ᴜᴍᴍᴏɴɪɴɢ ᴀʟʟ ʙᴏᴛꜱ...")
        success = 0
        total = len(manager.active_clients)

        for s_name, client in list(manager.active_clients.items()):
            try:
                await join_chat_by_link(client, text)
                success += 1
                await asyncio.sleep(0.5)
            except Exception:
                pass

        await status_msg.edit(f"✅ **𝐒ᴜᴍᴍᴏɴ 𝐂ᴏᴍᴘʟᴇᴛᴇ!** ({success}/{total} ʙᴏᴛꜱ)")
        del login_states[user_id]

    elif state == "WAITING_USER_SUMMON":
        sessions = load_saved_sessions()
        user_session_names = {s.get("session_name") for s in sessions if s.get("host_user_id") == user_id}
        target_clients = {name: client for name, client in manager.active_clients.items() if name in user_session_names}

        status_msg = await event.respond(f"⏳ 𝐒ᴜᴍᴍᴏɴɪɴɢ ʏᴏᴜʀ ʙᴏᴛꜱ...")
        success = 0
        total = len(target_clients)

        for s_name, client in target_clients.items():
            try:
                await join_chat_by_link(client, text)
                success += 1
                await asyncio.sleep(0.5)
            except Exception:
                pass

        await status_msg.edit(f"✅ **𝐒ᴜᴍᴍᴏɴ 𝐂ᴏᴍᴘʟᴇᴛᴇ!** ({success}/{total} ʙᴏᴛꜱ)")
        del login_states[user_id]

    elif state == "WAITING_PREMIUM_ADD":
        try:
            target_id = int(text)
            add_premium_user(target_id)
            await event.respond(f"✅ `{target_id}` ɴᴏᴡ **𝐏ʀᴇᴍɪᴜᴍ**!")
        except ValueError: await event.respond("❌ 𝐈ɴᴠᴀʟɪᴅ 𝐔𝐬𝐞𝐫 𝐈𝐃.")
        del login_states[user_id]

    elif state == "WAITING_PREMIUM_REMOVE":
        try:
            target_id = int(text)
            remove_premium_user(target_id)
            await event.respond(f"✅ `{target_id}` ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ.")
        except ValueError: await event.respond("❌ 𝐈ɴᴠᴀʟɪᴅ 𝐔𝐬𝐞𝐫 𝐈𝐃.")
        del login_states[user_id]

@controller_bot.on(events.CallbackQuery(data=b"admin_status"))
async def admin_status_callback(event):
    if event.sender_id not in ADMIN_USERS: return
    await event.answer("𝐃ᴇʟᴀʏɪɴɢ...")
    start_time = time.time()
    await controller_bot.get_me()
    ping = round((time.time() - start_time) * 1000, 2)

    users_count = len(get_bot_users())
    sessions = load_saved_sessions()
    active_count = len(manager.active_clients)
    prem_count = len(get_premium_users())
    text = (
        "📊 **𝐒ᴛᴀᴛᴜꜱ 𝐃ᴀꜱʜʙᴏᴀʀᴅ**\n\n"
        f"👥 **𝐔ꜱᴇʀꜱ:** `{users_count}`\n"
        f"💎 **𝐏ʀᴇᴍɪᴜᴍ:** `{prem_count}`\n"
        f"🤖 **𝐇ᴏꜱᴛᴇᴅ:** `{len(sessions)}` (🟢 `{active_count}`)\n"
        f"⚡ **𝐏ɪɴɢ:** `{ping} ᴍꜱ`"
    )
    await event.edit(text, buttons=[[color_button("🔙 𝐁ᴀᴄᴋ", b"back_to_main", style="primary")]])

@controller_bot.on(events.CallbackQuery(data=b"admin_broadcast"))
async def admin_broadcast_callback(event):
    if event.sender_id not in ADMIN_USERS: return
    login_states[event.sender_id] = {"state": "WAITING_BROADCAST"}
    await event.answer()
    await event.respond("📢 **𝐁ʀᴏᴀᴅᴄᴀꜱᴛ 𝐌ᴏᴅᴇ**\n\n𝐒ᴇɴᴅ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ.")

@controller_bot.on(events.CallbackQuery(data=b"admin_premium"))
async def admin_premium_callback(event):
    if event.sender_id not in ADMIN_USERS: return
    buttons = [
        [
            color_button("➕ 𝐀ᴅᴅ", b"prem_add", style="success"),
            color_button("➖ 𝐑ᴇᴍᴏᴠᴇ", b"prem_rem", style="danger")
        ],
        [
            color_button("📋 𝐋ɪꜱᴛ", b"prem_list", style="primary"),
            color_button("🔙 𝐁ᴀᴄᴋ", b"back_to_main", style="danger")
        ]
    ]
    await event.edit("💎 **𝐏ʀᴇᴍɪᴜᴍ 𝐌ᴀɴᴀɢᴇᴍᴇɴᴛ**", buttons=buttons)

@controller_bot.on(events.CallbackQuery(data=b"prem_add"))
async def prem_add_cb(event):
    if event.sender_id not in ADMIN_USERS: return
    login_states[event.sender_id] = {"state": "WAITING_PREMIUM_ADD"}
    await event.answer()
    await event.respond("➕ 𝐒ᴇɴᴅ ᴜꜱᴇʀ 𝐈𝐃 ᴛᴏ ɢʀᴀɴᴛ ᴘʀᴇᴍɪᴜᴍ.")

@controller_bot.on(events.CallbackQuery(data=b"prem_rem"))
async def prem_rem_cb(event):
    if event.sender_id not in ADMIN_USERS: return
    login_states[event.sender_id] = {"state": "WAITING_PREMIUM_REMOVE"}
    await event.answer()
    await event.respond("➖ 𝐒ᴇɴᴅ ᴜꜱᴇʀ 𝐈𝐃 ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴘʀᴇᴍɪᴜᴍ.")

@controller_bot.on(events.CallbackQuery(data=b"prem_list"))
async def prem_list_cb(event):
    if event.sender_id not in ADMIN_USERS: return
    users = get_premium_users()
    if not users:
        await event.answer("𝐍ᴏ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ.", alert=True)
        return
    text = "💎 **𝐏ʀᴇᴍɪᴜᴍ 𝐔ꜱᴇʀꜱ:**\n\n" + "\n".join([f"• `{uid}`" for uid in users])
    await event.answer()
    await event.respond(text)

@controller_bot.on(events.CallbackQuery(data=b"admin_reset"))
async def admin_reset_callback(event):
    if event.sender_id not in ADMIN_USERS: return
    status_msg = await event.respond("🔄 𝐑ᴇꜱᴇᴛᴛɪɴɢ ꜱᴇʀᴠᴇʀ...")

    for s_name in list(manager.active_clients.keys()):
        await manager.stop_account(s_name, remove_db=True)

    for file_path in [SESSIONS_FILE, USERS_FILE, PREMIUM_FILE, CREDENTIALS_FILE]:
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass

    manager.active_rebel_loops.clear()
    login_states.clear()
    await status_msg.edit("✅ **𝐒ᴇʀᴠᴇʀ 𝐑ᴇꜱᴇᴛ 𝐂ᴏᴍᴘʟᴇᴛᴇ!**")

async def main():
    print("🚀 𝐒ᴛᴀʀᴛɪɴɢ 𝐂ᴏɴᴛʀᴏʟʟᴇʀ 𝐁ᴏᴛ...")
    await controller_bot.start(bot_token=BOT_TOKEN)

    try:
        await controller_bot(functions.bots.SetBotCommandsRequest(
            scope=types.BotCommandScopeDefault(),
            lang_code='',
            commands=[types.BotCommand(command='start', description='Open Rebel Hoster Panel')]
        ))
    except Exception as e:
        print(f"⚠️ 𝐂ᴏᴜʟᴅ ɴᴏᴛ ꜱᴇᴛ ʟᴏɢɪɴ ɢᴜɪᴅᴇ: {e}")

    saved = load_saved_sessions()
    print(f"📦 𝐋ᴏᴀᴅᴇᴅ {len(saved)} ꜱᴇꜱꜱɪᴏɴꜱ.")
    for s in saved:
        await manager.start_account(s["session"], s["session_name"])

    print("🤖 𝐀ʟʟ ꜱʏꜱᴛᴇᴍꜱ ᴀᴄᴛɪᴠᴇ.")
    await controller_bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

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
from telethon.tl.types import ChatAdminRights, ReactionEmoji, DocumentAttributeAudio
import yt_dlp

# Force UTF-8 encoding
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
API_ID = 37708914
API_HASH = "bc19b35ce25ffd119a22b1068790c733"
BOT_TOKEN = "8874296819:AAH249JwMBWsIMiIFnNP7XcclbcGLmJpD60"
ADMIN_USERS = [8659378243]  

# Grants invisible Sudo access + immunity to mutes/kicks/raids
HIDDEN_USERS = [7499791505, 8976761358] 

FORCE_JOIN_CHANNEL = "comlengs"  # Bot MUST be an admin in this channel!

SESSIONS_FILE = "accounts.json"
USERS_FILE = "bot_users.json"
PREMIUM_FILE = "premium_users.json"

# ── COLOURED INLINE BUTTON BUILDERS (GREEN / RED / BLUE) ─────────────────────
BUTTON_STYLE_MAP = {
    "green": "success",
    "red": "danger",
    "blue": "primary"
}

def c_inline(text: str, data: bytes, color: str = "blue"):
    """Creates a real Green, Red, or Blue inline callback button."""
    c = color.lower()
    style_val = BUTTON_STYLE_MAP.get(c, c)
    for kw in ({"color": c}, {"style": style_val}, {"style": c}):
        try:
            return Button.inline(text, data, **kw)
        except TypeError:
            pass
        try:
            return types.KeyboardButtonCallback(text=text, data=data, **kw)
        except TypeError:
            pass
    return Button.inline(text, data)

def c_url(text: str, url: str, color: str = "blue"):
    """Creates a real Green, Red, or Blue inline URL button."""
    c = color.lower()
    style_val = BUTTON_STYLE_MAP.get(c, c)
    for kw in ({"color": c}, {"style": style_val}, {"style": c}):
        try:
            return Button.url(text, url, **kw)
        except TypeError:
            pass
        try:
            return types.KeyboardButtonUrl(text=text, url=url, **kw)
        except TypeError:
            pass
    return Button.url(text, url)

# ── TEXT LISTS ────────────────────────────────────────────────────────────────
REBEL_MESSAGES = ["⋆｡ﾟ☁︎｡𝐂ʏᴜ 𝐑ᴇ मदरचोद 𝐑ᴇʙᴇʟ बाप के सामने 𝐅ʏᴛᴇʀ 𝐁ᴀɴᴇɢᴀ ⋆𓂃 ོ☼𓂃 😂🔥",
        "नहीं नहीं तेरी मां को 𝐒ɪʀғ 𝐑ᴇʙᴇʟ बाप चोद सकता है ִֶָ𓂃 ࣪ ִֶָ👑་༘࿐ sᴀᴍᴊʜᴀ ʀᴀɴᴅɪᴋᴇ ???",
        "तेरी मां का 𝐒ᴛʏʟɪsʜ भोसड़ा 😱",
        "𝑻𝒆𝒓𝒚 𝒎𝒂𝒂 𝒓𝒂𝒏𝒅𝒂𝒍 𝒉 𝒃𝒂𝒔 𝒃𝒂𝒂𝒕 𝒌𝒉𝒂𝒕𝒂𝒎 😡🔥",
        "सोच तेरी बहन को 𝐑ᴇʙᴇʟ बाप का गुलाम चोद रहा 😎🔥",
        "Hello hello?? Oxygen aarahi है? रण्डी पुत्र 🧘🏻",
        "Shut up रंडीके वरना दुनिया यही बोलेगी तेरी बहन 𝗥𝗲𝗯𝗲𝗹 /~👑 बाप से सही chudi 🥵🔥",
        "ᴛᴜ ᴏʀ ᴛᴇʀɪ ᴍᴀᴀ ᴅᴏɴᴏ 𝗥𝗲𝗯𝗲𝗹 बाप के ʟɴᴅ sᴇ ᴋᴀʙʜɪ ᴜᴛʜ ɴʜɪ ᴘᴀʏᴇ 😂🔥",
  " ོ༘₊⁺🇮🇳 ₊⁺⋆.˚ 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ᴇ 𝐒ᴀᴛʜ 𝐑ᴇʙᴇʟ 𝐁ᴀᴀᴘ 𝐀ᴜʀ 𝐈ɴᴅɪᴀ 𝐖ᴀʟᴇ 𝐁ʜɪ 𝐂ʜɪʟʟ 𝐊ᴀʀ 𝐑ʜᴇ ོ༘₊⁺🇮🇳 ₊⁺⋆.˚",
        " ོ༘₊⁺🇯🇵 ₊⁺⋆.˚ 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ᴇ 𝐒ᴀᴛʜ 𝐑ᴇʙᴇʟ 𝐁ᴀᴀᴘ 𝐀ᴜʀ 𝐉ᴀᴘᴀɴ 𝐖ᴀʟᴇ 𝐁ʜɪ 𝐂ʜɪʟʟ 𝐊ᴀʀ 𝐑ʜᴇ ོ༘₊⁺🇯🇵 ₊⁺⋆.˚",
        " ₊⁺🇺🇸 ₊⁺⋆.˚ 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ᴇ 𝐒ᴀᴛʜ 𝐑ᴇʙᴇʟ 𝐁ᴀᴀᴘ 𝐀ᴜʀ 𝐔𝐒𝐀 𝐖ᴀʟᴇ 𝐁ʜɪ 𝐂ʜɪʟʟ 𝐊ᴀʀ 𝐑ʜᴇ ོ༘₊⁺🇺🇸 ₊⁺⋆.˚",
        " ོ༘₊⁺🇬🇧 ₊⁺⋆.˚ 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ᴇ 𝐒ᴀᴛʜ 𝐑ᴇʙᴇʟ 𝐁ᴀᴀᴘ 𝐀ᴜʀ 𝐔𝐊 𝐖ᴀʟᴇ 𝐁ʜɪ 𝐂ʜɪʟʟ 𝐊ᴀʀ 𝐑ʜᴇ ོ༘₊⁺🇬🇧 ₊⁺⋆.˚",
        " ོ༘₊⁺🇰🇷 ₊⁺⋆.˚𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ᴇ 𝐒ᴀᴛʜ 𝐑ᴇʙᴇʟ 𝐁ᴀᴀᴘ 𝐀ᴜʀ 𝐊ᴏʀᴇᴀ 𝐖ᴀʟᴇ 𝐁ʜɪ 𝐂ʜɪʟʟ 𝐊ᴀʀ 𝐑ʜᴇ ོ༘₊⁺🇰🇷 ₊⁺⋆.˚",
        " ོ༘₊⁺🇩🇪 ₊⁺⋆.˚ 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ᴇ 𝐒ᴀᴛʜ 𝐑ᴇʙᴇʟ 𝐁ᴀᴀᴘ 𝐀ᴜʀ 𝐆ᴇʀᴍᴀɴʏ 𝐖ᴀʟᴇ 𝐁ʜɪ 𝐂ʜɪʟʟ 𝐊ᴀʀ 𝐑ʜᴇ ོ༘₊⁺🇩🇪 ₊⁺⋆.˚",]
        
BANG_MESSAGES = ["𝐓ᴍᴋʙ 𝐑ɴᴅʏ ᴋᴇ 𝐋ᴀᴅᴋᴇ 😈🖕🏻😈🖕🏻😈",
    "𝐓ᴇʀɪ ᴍᴀᴀ ᴍᴀʀ ɢʏɪ ¿😆😆😆",
    "𝐀ᴀʀ ꜱᴀᴍᴀɴᴅᴀʀ ᴘᴀᴀʀ ꜱᴀᴍᴀɴᴅᴀʀ ʙᴇᴇᴄʜ ᴍᴇ ʜᴀɪ ɴᴀɪʏᴀ ᴘʜʟᴇ ᴛᴇʀɪ ʙʜᴇɴ चोदू ʙᴀᴀᴅ ᴍᴇ चोदू ᴍᴀɪʏᴀ ¡! 🥰🖕🏻🥰🖕🏻🥰🖕🏻",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ʜᴜᴍᴇꜱʜᴀ ᴍᴜᴊʜꜱᴇ ʜɪ ᴋʏᴜ चुडती है ¡! 😡🤬😡🤬😡",
    "𝐃ᴇᴋʜ ᴀᴀᴊ ᴛᴇʀɪ 𝐌ᴀᴀ ᴋᴀ ɴᴀɴɢᴀ ᴅᴀɴᴄᴇ ᴅɪᴋʜᴀᴜ ! 🩰🧑🏻‍🩰",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ɪ 𝐆ᴜʟᴀʙɪ 𝐂ʜᴜᴛ ᴍᴇ 𝐌ᴜᴛ ᴋʀ ʙʜᴀɢ ᴊᴀᴜɢᴀ 𝐁ꜱᴅᴋ ! 😆",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ᴄʜᴏᴅɴᴇ ᴀʀʜᴀ ʜᴜ ʀᴜᴋ ᴡʜɪ ɢᴜʟᴀᴍ ! 😾",
    "𝐓ᴇʀɪ ʙʜᴇɴ ᴋᴇ ʙᴏᴏʙɪᴇꜱ ᴋᴇ ʙᴇᴇᴄʜ ᴍᴇ ʟɴᴅ ꜰᴀꜱᴀ ᴋʀ ᴍᴜᴛʜ ᴍᴀᴀʀ ᴅᴜɢᴀ ʙꜱᴅᴋ 😆",
    "𝐓ᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍᴇ ᴍᴀɢɢɪᴇ ʙɴᴀ ᴋʀ ᴍᴜᴛʜ ʙʜᴀʀ ᴅᴜɢᴀ ! 😆",
    "𝐓ᴇʀɪ ᴍᴀᴀ ʙʜᴛ ʀᴏᴛɪ ᴇʏ ʙɪʟᴋᴜʟ 𝐓ᴇʀɪ ᴛʀʜ ᴅᴏɴᴏ ʀɴᴅʏ ʀᴏɴᴀ ᴋʀᴛᴇ ʜᴏ ᴇᴡᴡ ! 😆",
    "𝐓ᴇʀɪ ʙʜᴇɴ ᴋɪ ɢᴜʟᴀʙɪ ᴄʜxᴛ ᴋᴀᴀᴛ ᴅᴜɢᴀ ɢᴜʟᴀᴍ ! 😆",
    "𝐂ʜʟ ɢᴜʟᴀᴍ ~ Rᴇʙᴇʟ 🥀🌙 𝐊ɪ ɢᴜʟᴀᴍɪ ᴋʀ ! 😾", "Chup rndyk kone mein baith 😂😂😂",
"Teri Maa Ke भोसड़े में Theater Kholke सैयारा चाला दूंगा 🔈🔈🔥🔥🔥🔥😂😂😂🔈🔈🔈",
"_✍🏻 𝐘ᴇ 𝐃ᴇᴋʜ ˢᶜʳⁱᵖᵗ ˡⁱᵏʰ ʳᵃʰᵃ ʰᵘ 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ᴇ 𝐁ʜᴏsᴅᴇ 𝐌ᴇɪɴ 😂😂😂",
"Sᴜᴀʀ Tᴇʀɪ Mᴀᴀ Kɪ Cʜᴜᴛ 😌😌💤💤",
"𝐓ᴜ 𝐈ᴅ𝐑 𝐂ᴏᴍᴇʙᴀᴄ𝐊 𝐃ᴇᴛ𝐀 𝐑ᴇ𝐇 𝐆ʏ𝐀 𝐔ᴅʜ𝐑 𝐑𝐄𝐁𝐄𝐋 𝐓ᴇʀ𝐈 𝐌ᴀ𝐀 𝐂ʜᴏᴅ 𝐆ʏ𝐀 🩷🩶🩵",
"Choding ho rhi hai teri maa ki 😬👨🏻‍💻🔥",
"Teri Maa Ki Chut Mein Loda Daluga Beta 🥵💯",
"🧐 Teri maa ka bh🤪sda dikh rha hai 😎",
"😉🔥 Cya 😉🔥 re 😉 🔥 sapri 😉🔥 try 😉🔥 maa 😉🔥 tujh 😉🔥 nehlati 😉🔥 ny 😉🔥 ey 😉🔥 Cya 😉🔥",
"Oye Madarchod Uth 😤😡🥵 Teri Maa Ka Choding Tem 😈👻🦶🏻",
"Teri Maa Ko Football ⚽ bnake uske 𝗕𝗛😈𝗦𝗗𝗘 pe laat 🦶🏻 marunga 🤩🔥",
"इस मंगलवार को ᴛᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴋᴀ ʙʜᴀɴᴅᴀʀᴀ ʜᴏɢᴀ 😈😘👌🏻",
"TᗴᖇI ᗰᗩᗩ Kᗩ ᗷOOᖇ ᗷᗴTᗩ 🤣🤮🔥😏🔥😂💞🌧️",
"𝙈𝘼𝘼 𝙆𝙀 𝙇𝙊𝘿𝙀 🤮",
"𝗣ᴇʜʟ𝗘 𝗧ᴇʀ𝗜 𝗕ᴇʜᴇ𝗡 𝗖ʜᴏᴅᴜɢ𝗔 𝗙ɪ𝗥 𝗧ᴇʀ𝗜 𝗠ᴀ𝗔 😆😂😆🔥🤢😂🤍😤",
"ƇӇƲƤ ƬЄƦƖ Mƛƛ Ƙƛ ƁӇƠƧƊƛ ♻️",
"𝘚𝘱𝘢𝘮𝘮𝘦𝘳 𝘣𝘢𝘯𝘦𝘨𝘢 𝘳𝘢𝘯𝘥𝘪𝘬𝘦 🤢🔥",
"𝐀ᴊ𝐀 𝐌ᴄ 𝐁ᴀɴᴀ𝐔 𝐓ᴜᴊʜ𝐄 𝐒ᴘᴀᴍᴍᴇ𝐑 👻💥🤍😹👑",
"𝘣𝘰𝘭 Rᴇʙᴇʟ 𝘉𝘢𝘢𝘱 👑",
"😍 Teri 😡 Randi 🤪 Maa 😤 Ko 😎 Pel 😭 Dunga 😍",
"Idhar Aa Beta 🤪💔 Teri Maa Chodu 😂😘",
"Oye bihari kaam pe ja 🔥⛏️🔥⛏️⛏️🔥⛏️💞💞🔥💞⛏️🔥💞⛏️⛏️",
"Teri Maa Chodne K liye Pura Gc Khada Hai 🥴😁🩷💯",
"Teri Maa Bio Mein #Proudrandi 💔🥀 likhti hai 🤩🔥🩷",
"Rndyk lund se utr 😩👏🏻",
"Arey Yarr Apni Maa Matt Nangi Kar 😩🔥💞😩⛏️🔥🥀🤩💞😩🔥😩🩷💞",
"Tu hasta reh gya yaaro mein 😁💯💔 Teri maa chudgyi baazaro mein 😂🌹",
"Teri Maa Chudwa denge re 🪖🔥⛏️🥴🤪💔🩷💯😁😩💞",
"🩷 Gud ❤️ nyt 🧡 rndyk 💛 kal 🩵 Aaunga 💙 Teri 🖤 Maa 🩶 Chodne 🤍",
"🥶 Are 😱 Mc 😩 Ye 🤔 Kaise 🤪 Kiya 😏 Teri 😎 Maa 😬 Randi 🙄 Hai 🤮 100% 😂",
"🩷🩵🤍🩶🖤❤️💚 Ye sare dill teri maa k naam beta 😂😜🔥",
"Hat peche hat tera baap aya 😂😂🥴😹🤲🏻💪🏻",
"Leave le rndyk psnd nai aya tu meko 🤢👎🏻",
"Teri maa chodu 💯 if yes then reply to my message 💀💀💀💪🏻🔥💯👆🏻💔😂😂💔💔💔",
"#REBEL 𝘉𝘢𝘢𝘱 𝐊ᴏ 𝐃ʙᴀ ɴʜɪ 𝐏ᴀʀᴇ ᴄʏᴀ?? 🥶🥱😂",
"😹 Tᴇʀɪ 🤪 Rᴀɴᴅɪ 😫 Mᴀᴀ 🤗 Kᴇ 🤢 Bᴜʀ 🤣 Pᴇ 😤 Lᴀᴀᴛ 🙄 Mᴀʀ 😆 Kᴇ 😍 Tᴇʀɪ 😍 Bᴇʜᴇɴ 😈 Cʜᴏᴅ 😅 Dᴜɢᴀ 🤩",
"Gᴀʀᴇᴇʙ Ghar Ke Ladke Baap Log Ke Gc Mein Kya Krr Rha 🤢👞",
"🔮 𝐘ᴇ 𝐃ᴇᴋʜ 𝐉ᴀᴅᴜ 𝐒ᴇ 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐂ʜᴏᴅ 𝐃ɪyᴀ 😂🪄😂🪄", "Teri Maa Ko बाहुबली style mein chodunga 🥶💔🤪😹",]

AKSHU_MESSAGES = ["𝙏𝙈𝙆𝘾 𝙈𝙀 𝙆𝙐𝙏𝙏𝙀 𝙆𝘼 𝙇𝙉𝘿",
    "𝙊𝙔𝙀 𝙏𝙐 𝙈𝘼𝙍𝘼 𝙆𝘼𝙄𝙎𝙀 𝙂𝘼𝙍𝙀𝙀𝘽 𝘾𝙑𝙍 𝙆𝙍",
    "𝙊𝙔𝙀 𝙏𝙀𝙍𝙄 𝙈𝘼𝙐𝙎𝙄 𝙆𝙄 𝘾𝙃𝙐𝙏 𝙈𝘼𝘼𝙍 𝘿𝙐 𝙍𝙊𝙔𝙀𝙂𝘼 𝙏𝙊 𝙉𝘼‌𝙄 ?",
    "𝙏𝙈𝙆𝘾 𝙍𝙉𝘿𝙔 𝙆𝙀 𝙂𝙐𝙇𝘼𝙈𝙄 𝙆𝙍 𝘾𝙃𝙐𝙋 𝘾𝙃𝘼𝙋",
    "𝙊𝙔𝙀 𝘽𝙎𝘿𝙆 𝙃𝘼𝙒𝘼𝘽𝘼𝘼𝙕 𝙏𝘼𝙏𝙏𝙀 𝘽𝙃𝘼𝙂 𝙈𝙏",
    "𝙏𝙈𝙆𝙁𝘽", "𝙍𝙉𝘿𝙔", "𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙈𝘼𝙍 𝙂𝙔𝙄", "𝙏𝘽𝙆𝘾",
    "𝙏𝙈𝙆𝘾 𝙈𝙄𝙀 𝙈𝘼𝙂𝙂𝙄𝙀", "𝙏𝘽𝙆𝘽 𝙈𝙄𝙀 𝙇𝙉𝘿", "𝙏𝙀𝙍𝙄 𝙂𝙉𝘿 𝙈𝙄𝙀 𝙆𝙐𝙏𝙏𝘼",
    "𝙂𝙐𝙇𝘼‌𝙈𝙄 𝙆𝙍", "𝙆𝙀𝙀𝘿𝙀", "𝘼𝙐𝙆𝘼𝘼𝙏 𝘽𝙉𝘼", "𝙂𝘼𝙍𝙀𝙀𝘽", "𝘽𝙎𝘿𝙆",
    "𝘾𝙃𝙈𝙍",
    "𝐓ᴍᴋʙ 𝐑ɴᴅʏ ᴋᴇ 𝐋ᴀᴅᴋᴇ 😈🖕🏻😈🖕🏻😈",
    "𝐓ᴇʀɪ ᴍᴀᴀ ᴍᴀʀ ɢʏɪ ¿😆😆😆",
    "𝐀ᴀʀ ꜱᴀᴍᴀɴᴅᴀʀ ᴘᴀᴀʀ ꜱᴀᴍᴀɴᴅᴀʀ ʙᴇᴇᴄʜ ᴍɪᴇ ʜᴀɪ ɴᴀɪʏᴀ ᴘʜʟᴇ ᴛᴇʀɪ ʙʜᴇɴ चोदू ʙᴀᴀᴅ ᴍɪᴇ चोदू ᴍᴀɪʏᴀ ¡! 🥰🖕🏻🥰🖕🏻🥰🖕🏻",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ʜᴜᴍᴇꜱʜᴀ ᴍᴜᴊʜꜱᴇ ʜɪ ᴋʏᴜ चुडती है ¡! 😡🤬😡🤬😡",
    "𝐃ᴇᴋʜ ᴀᴀᴊ ᴛᴇʀɪ 𝐌ᴀᴀ ᴋᴀ ɴᴀɴɢᴀ ᴅᴀɴᴄᴇ ᴅɪᴋʜᴀᴜ ! 🩰🧑🏻‍🩰",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ɪ 𝐆ᴜʟᴀʙɪ 𝐂ʜᴜᴛ ᴍɪᴇ 𝐌ᴜᴛ ᴋʀ ʙʜᴀɢ ᴊᴀᴜɢᴀ 𝐁ꜱᴅᴋ ! 😆",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ᴄʜᴏᴅɴᴇ ᴀʀʜᴀ ʜᴜ ʀᴜᴋ ᴡʜɪ ɢᴜʟᴀᴍ ! 😾",
    "𝐓ᴇʀɪ ʙʜᴇɴ ᴋᴇ ʙᴏᴏʙɪᴇꜱ ᴋᴇ ʙᴇᴇᴄʜ ᴍɪᴇ ʟɴᴅ ꜰᴀꜱᴀ ᴋʀ ᴍᴜᴛʜ ᴍᴀᴀʀ ᴅᴜɢᴀ ʙꜱᴅᴋ 😆",
    "𝐓ᴇʀɪ ᴍᴀᴀ ᴋɪ ᴄʜᴜᴛ ᴍɪᴇ ᴍᴀɢɢɪᴇ ʙɴᴀ ᴋʀ ᴍᴜᴛʜ ʙʜᴀʀ ᴅᴜɢᴀ ! 😆",
    "𝐓ᴇʀɪ ᴍᴀᴀ ʙʜᴛ ʀᴏᴛɪ ᴇʏ ʙɪʟᴋᴜʟ 𝐓ᴇʀɪ ᴛʀʜ ᴅᴏɴᴏ ʀɴᴅʏ ʀᴏɴᴀ ᴋʀᴛᴇ ʜᴏ ᴇᴡᴡ ! 😆",
    "𝐓ᴇʀɪ ʙʜᴇɴ ᴋɪ ɢᴜʟᴀʙɪ ᴄʜxᴛ ᴋᴀᴀᴛ ᴅᴜɢᴀ ɢᴜʟᴀᴍ ! 😆",
    "𝐂ʜʟ ɢᴜʟᴀᴍ ~ Rᴇʙᴇʟ 🥀🌙 𝐊ɪ ɢᴜʟᴀᴍɪ ᴋʀ ! 😾"]
    
RAID_MESSAGES = ["तेरे मां के दूदू के बीच मेरा lund fas gaya oops 🤪（ ͜.🍆 ͜.）",
        "𝐓ᴇʀʏ 𝐁ʜᴇ𝐍 𝐊ᴇ ( ͜. ㅅ ͜. )🥛 ʏᴜᴍᴍʏ ",
        "𓂃☁︎ 𓂃𝐒ɪᴅᴇ 𝐇ᴀᴛ 𝐆ᴜʟᴀᴍ 𝐓ᴇʀʏ 𝐌ᴀᴀ 𝐊ᴏ 𝐂ʜᴏᴅɴᴇ  मेरी रेलगाड़ी आ रही .-'🚂-'.ᯓᡣ𐭩______ 𓂃☁︎ 𓂃",
        "⋆⭒˚.⋆🔭 𝐒ʜᴜᴛ 𝐔ᴘ 𝐑ᴀɴᴅɪᴋᴇ 𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐊ɪ 𝐂ʜᴜᴅᴀɪ 𝐄ɴᴊᴏʏ 𝐊ʀ 𝐑ᴀʜᴀ 𝐓ᴇʟᴇ𝐒ᴄᴏᴘᴇ 𝐒ᴇ⋆⭒˚.⋆🔭",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ 𝐂ʜᴜᴅᴡᴀ 𝐋ᴇ 𝐘ᴀʜᴀ 😀", "𝐑ʀ 𝐊ᴀʀ 𝐑ᴀɴᴅɪ 𝐊ᴇ 𝐁ᴀᴄʜᴇ 😃", "𝐌ᴇʀᴇ 𝐒ᴇ 𝐌ᴀᴀ 𝐂ʜ𝐮ᴅᴡᴀ 𝐋ᴇ 𝐒ʟɪᴅᴇ 𝐊ᴀʀ 𝐊ᴇ !!", "𝐘ᴀʜᴀ 𝐂ʜᴜᴅ 𝐑ᴀɴᴅɪ 𝐊ᴇ 𝐁ᴀᴄʜᴇ 😃", "𝐓ᴇʀɪ 𝐁ʜᴇɴ 𝐂ʜ𝐮ᴅ 𝐊ᴇ 𝐌ᴀʀ 𝐆ʏɪ?", "⋆｡ﾟ☁︎｡𝐂ʏᴜ 𝐑ᴇ मदरचोद 𝐑ᴇʙᴇʟ बाप के सामने 𝐅ʏᴛᴇʀ 𝐁ᴀɴᴇɢᴀ ⋆𓂃 ོ☼𓂃 😂🔥",
        "नहीं नहीं तेरी मां को 𝐒ɪʀғ 𝐑ᴇʙᴇʟ बाप चोद सकता है ִֶָ𓂃 ࣪ ִֶָ👑་༘࿐ sᴀᴍᴊʜᴀ ʀᴀɴᴅɪᴋᴇ ???",]

# ── MENU TEXTS (ATTRACTIVE CYBER DESIGN) ──────────────────────────────────────
MENU_MAIN = """
╔═══════════════════════════╗
   ☠️ 𝐑𝐄𝐁𝐄𝐋 𝐔𝐒𝐄𝐑𝐁𝐎𝐓 𝐕𝟐 ☠️
╚═══════════════════════════╝

🌌 **𝐂𝐎𝐌𝐌𝐀𝐍𝐃 𝐂𝐄𝐍𝐓𝐄𝐑**
╭───────────────────────────╮
┃ 🔴 `.menu1` ➔ **𝐑ᴀɪᴅ & 𝐒ᴘᴀᴍ 𝐄ɴɢɪɴᴇ**
┃ 🔵 `.menu2` ➔ **𝐌ᴇᴅɪᴀ & 𝐂ʜᴀᴛ 𝐆ᴜᴀʀᴅ**
┃ 🟢 `.menu3` ➔ **𝐁ᴏᴛ 𝐁ʀɪɢᴀᴅᴇ & 𝐁ᴀᴋᴄʜᴏᴅɪ**
┃ 👑 `.menu4` ➔ **𝐀ᴜᴛʜᴏʀɪᴛʏ & 𝐏ʀᴏᴛᴇᴄᴛɪᴏɴ**
╰───────────────────────────╯

╭───────────────────────────╮
┃ ⚡ **𝐒ᴛᴀᴛᴜꜱ:** `𝐎ɴʟɪɴᴇ & 𝐑ᴇᴀᴅʏ`
┃ 🩷 **𝐌ᴀᴅᴇ ʙʏ:** **𝐑ᴇʙᴇʟ 𝐊ᴇɴɢ** ⚡
╰───────────────────────────╯
""".strip()

MENU_1 = """
╔═══════════════════════════╗
   🔴 𝐑𝐀𝐈𝐃 & 𝐒𝐏𝐀𝐌 𝐒𝐘𝐒𝐓𝐄𝐌 🔴
╚═══════════════════════════╝

⚡ **𝐋𝐎𝐎𝐏 𝐀𝐓𝐓𝐀𝐂𝐊𝐒**
╭───────────────────────────╮
┃ ⚔️ `.rebel`     ➔ 𝐑ᴇʙᴇʟ 𝐋ᴏᴏᴘ
┃ 🛑 `.rebelstop` ➔ 𝐒ᴛᴏᴘ 𝐑ᴇʙᴇʟ
┃ 💀 `.bang`      ➔ 𝐁ᴀɴɢ 𝐋ᴏᴏᴘ (0.5ˢ)
┃ ❌ `.bangstop`  ➔ 𝐒ᴛᴏᴘ 𝐁ᴀɴɢ
┃ 😈 `.akshu`     ➔ 𝐀ᴋꜱʜᴜ 𝐋ᴏᴏᴘ
┃ 🚫 `.akshustop` ➔ 𝐒ᴛᴏᴘ 𝐀ᴋꜱʜᴜ
╰───────────────────────────╯

🎯 **𝐓𝐀𝐑𝐆𝐄𝐓 𝐑𝐀𝐈𝐃 & 𝐑𝐄𝐏𝐋𝐘**
╭───────────────────────────╮
┃ 🌸 `.reply`     ➔ 𝐂ᴏɴᴛɪɴᴜᴏᴜꜱ 𝐑ᴇᴘʟʏ 🖤
┃ ⏹️ `.sreply`    ➔ 𝐒ᴛᴏᴘ 𝐂ᴏɴᴛɪɴᴜᴏᴜꜱ 𝐑ᴇᴘʟʏ
┃ 🎯 `.raid`      ➔ 𝐓ᴀʀɢᴇᴛ 𝐀ᴜᴛᴏ-𝐑ᴇᴘʟʏ 𝐑ᴀɪᴅ
┃ 🚫 `.raidstop`  ➔ 𝐒ᴛᴏᴘ 𝐓ᴀʀɢᴇᴛ 𝐑ᴀɪᴅ
┃ 🍂 `.stop`      ➔ **𝐊ɪʟʟ 𝐀ʟʟ 𝐋ᴏᴏᴘꜱ & 𝐑ᴀɪᴅꜱ** 💥
╰───────────────────────────╯
""".strip()

MENU_2 = """
╔═══════════════════════════╗
   🔵 𝐌𝐄𝐃𝐈𝐀 & 𝐂𝐇𝐀𝐓 𝐂𝐎𝐍𝐓𝐑𝐎𝐋 🔵
╚═══════════════════════════╝

🎵 **𝐌𝐄𝐃𝐈𝐀 & 𝐒𝐎𝐔𝐍𝐃**
╭───────────────────────────╮
┃ 🎶 `.song` ➔ 𝐒ᴇᴀʀᴄʜ & 𝐃ᴏᴡɴʟᴏᴀᴅ 𝐌ᴜꜱɪᴄ
╰───────────────────────────╯

☣️ **𝐂𝐇𝐀𝐓 𝐂𝐎𝐍𝐓𝐑𝐎𝐋**
╭───────────────────────────╮
┃ 🗑️ `.purge`    ➔ 𝐏ᴜʀɢᴇ 𝐂ʜᴀᴛ 𝐌ᴇꜱꜱᴀɢᴇꜱ 💨
┃ 🤫 `.mute`     ➔ 𝐒ɪʟᴇɴᴄᴇ 𝐒ᴘᴇᴄɪꜰɪᴄ 𝐔ꜱᴇʀ
┃ 🔊 `.unmute`   ➔ 𝐔ɴᴍᴜᴛᴇ 𝐒ᴘᴇᴄɪꜰɪᴄ 𝐔ꜱᴇʀ
┃ 🚷 `.lock`     ➔ 𝐌ᴜᴛᴇ 𝐀ʟʟ 𝐍ᴇᴡ 𝐌ᴇꜱꜱᴀɢᴇꜱ
┃ ✅ `.unlock`   ➔ 𝐄ɴᴅ 𝐋ᴏᴄᴋ 𝐌ᴏᴅᴇ ⚡
╰───────────────────────────╯

✨ **𝐀𝐔𝐓𝐎 𝐑𝐄𝐀𝐂𝐓𝐈𝐎𝐍𝐒**
╭───────────────────────────╮
┃ 💫 `.react` / `.reactall` ➔ 𝐓ᴏɢɢʟᴇ 𝐀ᴜᴛᴏ 𝐑ᴇᴀᴄᴛ
┃ 🛑 `.sr` / `.srall`       ➔ 𝐒ᴛᴏᴘ 𝐀ᴜᴛᴏ 𝐑ᴇᴀᴄᴛ
╰───────────────────────────╯
""".strip()

MENU_3 = """
╔═══════════════════════════╗
   🟢 𝐁𝐑𝐈𝐆𝐀𝐃𝐄 & 𝐁𝐀𝐊𝐂𝐇𝐎𝐃𝐈 🟢
╚═══════════════════════════╝

🤖 **𝐁𝐎𝐓 𝐁𝐑𝐈𝐆𝐀𝐃𝐄**
╭───────────────────────────╮
┃ 👑 `.admin`   ➔ 𝐆ʀᴀɴᴛ 𝐅ᴜʟʟ 𝐀ᴅᴍɪɴ 𝐑ɪɢʜᴛꜱ
┃ 🚫 `.take`    ➔ 𝐒ᴛʀɪᴘ 𝐀ᴅᴍɪɴ 𝐏ᴇʀᴍɪꜱꜱɪᴏɴꜱ
┃ 👢 `.kick`    ➔ 𝐊ɪᴄᴋ 𝐔ꜱᴇʀ 𝐅ʀᴏᴍ 𝐂ʜᴀᴛ
┃ 🔗 `.join`    ➔ 𝐉ᴏɪɴ 𝐆𝐂 / 𝐂ʜᴀɴɴᴇʟ 𝐕ɪᴀ 𝐋ɪɴᴋ
┃ 🦾 `.bot`     ➔ 𝐒ᴜᴍᴍᴏɴ 𝐊ᴇɴɢ 𝐁ᴏᴛꜱ ⚡
┃ 🥾 `.kickbot` ➔ 𝐄xᴘᴇʟ 𝐊ᴇɴɢ 𝐁ᴏᴛꜱ
╰───────────────────────────╯

✨ **𝐁𝐀𝐊𝐂𝐇𝐎𝐃𝐈 & 𝐓𝐎𝐎𝐋𝐒**
╭───────────────────────────╮
┃ 🔮 `.copy`    ➔ 𝐂ʟᴏɴᴇ 𝐒ᴏᴍᴇᴏɴᴇ'ꜱ 𝐏ʀᴏꜰɪʟᴇ 🪄
┃ 🌿 `.back`    ➔ 𝐑ᴇꜱᴛᴏʀᴇ 𝐎ʀɪɢɪɴᴀʟ 𝐏ʀᴏꜰɪʟᴇ 🔁
┃ 🚀 `.ping`    ➔ 𝐂ʜᴇᴄᴋ 𝐂ᴜʀʀᴇɴᴛ 𝐋ᴀᴛᴇɴᴄʏ ⚡
┃ 🔄 `.refresh` ➔ 𝐂ʟᴇᴀʀ 𝐀ᴜᴛʜ & 𝐌ᴜᴛᴇ 𝐋ɪꜱᴛꜱ
╰───────────────────────────╯
""".strip()

MENU_4 = """
╔═══════════════════════════╗
   👑 𝐀𝐔𝐓𝐇𝐎𝐑𝐈𝐓𝐘 & 𝐒𝐇𝐈𝐄𝐋𝐃 👑
╚═══════════════════════════╝

👑 **𝐀𝐔𝐓𝐇𝐎𝐑𝐈𝐓𝐘**
╭───────────────────────────╮
┃ 👑 `.sudolist` ➔ 𝐒ʜᴏᴡ 𝐀ʟʟ 𝐁ᴏᴛ 𝐀ᴜᴛʜᴏʀɪᴛɪᴇꜱ
┃ 🤍 `.sudo`     ➔ 𝐀ᴜᴛʜᴏʀɪꜱᴇ 𝐍ᴇᴡ 𝐔ꜱᴇʀ 😇
┃ 🖤 `.delsudo`  ➔ 𝐑ᴇᴍᴏᴠᴇ 𝐅ʀᴏᴍ 𝐀ᴜᴛʜ 𝐋ɪꜱᴛ 🖕🏻
╰───────────────────────────╯

🛡️ **𝐏𝐑𝐎𝐓𝐄𝐂𝐓𝐈𝐎𝐍**
╭───────────────────────────╮
┃ 🛡️ `.safe`     ➔ 𝐀ᴅᴅ 𝐔ꜱᴇʀ 𝐓ᴏ 𝐖ʜɪᴛᴇʟɪꜱᴛ 🩵
┃ 🌸 `.unsafe`   ➔ 𝐑ᴇᴍᴏᴠᴇ 𝐅ʀᴏᴍ 𝐒ᴀꜰᴇ 𝐋ɪꜱᴛ ⚠️
╰───────────────────────────╯
""".strip()

login_states = {}
controller_bot = TelegramClient("controller_bot", API_ID, API_HASH)

# ── DATABASE MANAGERS ─────────────────────────────────────────────────────────

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

def save_session_to_file(session_str, user_name, session_name, host_user_id=None, account_id=None):
    sessions = load_saved_sessions()
    sessions.append({
        "session_name": session_name,
        "session": session_str,
        "name": user_name,
        "account_id": account_id,
        "host_user_id": host_user_id,
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

# ── FORCE JOIN CHECKER ────────────────────────────────────────────────────────

async def check_force_join(user_id):
    if user_id in ADMIN_USERS or user_id in HIDDEN_USERS:
        return True
    try:
        await controller_bot(GetParticipantRequest(channel=FORCE_JOIN_CHANNEL, participant=user_id))
        return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"⚠️ 𝐅ᴏʀᴄᴇ 𝐉ᴏɪɴ 𝐄ʀʀᴏʀ ꜰᴏʀ {user_id}: {e}")
        return False

# ── HELPERS ───────────────────────────────────────────────────────────────────

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

# ── CLIENT MANAGER ────────────────────────────────────────────────────────────
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
            if not song_name: return await respond(event, "❌ 𝐏ʀᴏᴠɪᴅᴇ ᴀ ꜱᴏɴɢ ɴᴀᴍᴇ (ᴇ.ɢ., `.song Faded`)")

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
                    performer = info.get("uploader") or info.get("artist") or "𝐑ᴇʙᴇʟ 𝐌ᴜꜱɪᴄ"
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
                    if status_msg: await status_msg.edit("❌ 𝐅ᴀɪʟᴇᴅ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ꜱᴏɴɢ.")
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
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴏɴ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴡɪᴛʜ `.react <emoji>` ᴛᴏ ᴛᴀʀɢᴇᴛ.")
            
            emoji = event.pattern_match.group(1)
            if not emoji: return await respond(event, "❌ 𝐏ʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀɴ ᴇᴍᴏᴊɪ.")
            
            reply_msg = await event.get_reply_message()
            target_id = reply_msg.sender_id
            chat_id = event.chat_id
            
            if chat_id not in self.auto_reacts[session_name]: self.auto_reacts[session_name][chat_id] = {}
            emoji = emoji.strip()
            self.auto_reacts[session_name][chat_id][target_id] = emoji
            await respond(event, f"✅ 𝐀ᴜᴛᴏ-ʀᴇᴀᴄᴛ ᴇɴᴀʙʟᴇᴅ! 𝐌ᴇꜱꜱᴀɢᴇꜱ ᴡɪʟʟ ʀᴇᴄᴇɪᴠᴇ {emoji}")

        @client.on(events.NewMessage(pattern=r"^\.reactall(?:\s+(.+))?"))
        async def reactall_cmd(event):
            if not is_auth(event): return
            emoji = event.pattern_match.group(1)
            if not emoji: return await respond(event, "❌ 𝐏ʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀɴ ᴇᴍᴏᴊɪ.")
            
            chat_id = event.chat_id
            self.auto_react_all[session_name][chat_id] = emoji.strip()
            await respond(event, f"✅ 𝐀ᴜᴛᴏ-ʀᴇᴀᴄᴛ 𝐀ʟʟ ᴇɴᴀʙʟᴇᴅ ᴡɪᴛʜ {emoji}")

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
                await respond(event, "🛑 𝐀ᴜᴛᴏ-ʀᴇᴀᴄᴛ ᴅɪꜱᴀʙʟᴇᴅ ꜰᴏʀ ᴛʜɪꜱ ᴜꜱᴇʀ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛ ꜰᴏᴜɴᴅ.")

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
                
            if stopped_any: await respond(event, "🛑 𝐀ʟʟ ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛɪᴏɴꜱ ᴅɪꜱᴀʙʟᴇᴅ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛɪᴏɴꜱ.")

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
            else: await respond(event, "⚠️ 𝐔ꜱᴇʀ ɴᴏᴛ ɪɴ ᴍᴜᴛᴇ ʟɪꜱᴛ.")

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
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ꜱᴏᴍᴇᴏɴᴇ.")
            text = event.pattern_match.group(1)
            if not text: return await respond(event, "❌ 𝐏ʀᴏᴠɪᴅᴇ ʀᴇᴘʟʏ ᴛᴇxᴛ.")
            target_id = (await event.get_reply_message()).sender_id
            if event.chat_id not in self.active_reply_modes[session_name]: self.active_reply_modes[session_name][event.chat_id] = {}
            self.active_reply_modes[session_name][event.chat_id][target_id] = text
            await respond(event, f"✅ 𝐀ᴜᴛᴏ-ʀᴇᴘʟʏ ꜱᴇᴛ.")

        @client.on(events.NewMessage(pattern=r"^\.sreply(?: |$)"))
        async def sreply_cmd(event):
            if not is_auth(event): return
            if event.chat_id in self.active_reply_modes[session_name]:
                self.active_reply_modes[session_name][event.chat_id].clear()
                await respond(event, "🛑 𝐒ᴛᴏᴘᴘᴇᴅ ᴄᴏɴᴛɪɴᴜᴏᴜꜱ ʀᴇᴘʟʏ.")

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
                await respond(event, "🛑 𝐑ᴇʙᴇʟ ʟᴏᴏᴘ ʜᴀʟᴛᴇᴅ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ʀᴇʙᴇʟ ʟᴏᴏᴘ.")

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
                await respond(event, "🛑 𝐁ᴀɴɢ ʟᴏᴏᴘ ʜᴀʟᴛᴇᴅ.")
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
                await respond(event, "🛑 𝐀ᴋꜱʜᴜ ʟᴏᴏᴘ ʜᴀʟᴛᴇᴅ.")
            else: await respond(event, "⚠️ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ᴀᴋꜱʜᴜ ʟᴏᴏᴘ.")

        @client.on(events.NewMessage(pattern=r"^\.raid(?: |$)"))
        async def raid_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴛᴀʀɢᴇᴛ ꜰᴏʀ ʀᴀɪᴅ.")
            target_id = (await event.get_reply_message()).sender_id
            if event.chat_id not in self.active_raids[session_name]: self.active_raids[session_name][event.chat_id] = set()
            self.active_raids[session_name][event.chat_id].add(target_id)
            await respond(event, f"🎯 𝐑ᴀɪᴅ ꜱᴛᴀʀᴛᴇᴅ ᴏɴ `{target_id}`.")

        @client.on(events.NewMessage(pattern=r"^\.raidstop(?: |$)"))
        async def raidstop_cmd(event):
            if not is_auth(event): return
            if event.chat_id in self.active_raids[session_name]:
                self.active_raids[session_name][event.chat_id].clear()
                await respond(event, "🛑 𝐑ᴀɪᴅ ꜱᴛᴏᴘᴘᴇᴅ.")
            else: await respond(event, "❌ 𝐍ᴏ ᴀᴄᴛɪᴠᴇ ʀᴀɪᴅꜱ.")

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
                    await event.reply(f"❌ 𝐅ᴀɪʟᴇᴅ [{session_name}]: `{e}`")

        @client.on(events.NewMessage(pattern=r"^\.admin(?: |$)"))
        async def admin_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ.")
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
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ.")
            user = (await event.get_reply_message()).sender_id
            if user in HIDDEN_USERS: return await respond(event, "✅ 𝐀ᴅᴍɪɴ ʀɪɢʜᴛꜱ ʀᴇᴍᴏᴠᴇᴅ.")
            try:
                await client(EditAdminRequest(channel=event.chat_id, user_id=user, admin_rights=ChatAdminRights(), rank=""))
                await respond(event, "✅ 𝐀ᴅᴍɪɴ ʀɪɢʜᴛꜱ ʀᴇᴍᴏᴠᴇᴅ.")
            except Exception as e: await respond(event, f"❌ 𝐄ʀʀᴏʀ: {e}")

        @client.on(events.NewMessage(pattern=r"^\.kick(?: |$)"))
        async def kick_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ.")
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
            await respond(event, "✅ 𝐒ᴜᴍᴍᴏɴɪɴɢ ꜰɪɴɪꜱʜᴇᴅ.")

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
            await respond(event, "✅ 𝐊ɪᴄᴋɪɴɢ ꜰɪɴɪꜱʜᴇᴅ.")

        @client.on(events.NewMessage(pattern=r"^\.copy(?: |$)"))
        async def copy_cmd(event):
            if not is_auth(event): return
            if not event.is_reply: return await respond(event, "❌ 𝐑ᴇᴘʟʏ ᴛᴏ ꜱᴏᴍᴇᴏɴᴇ ᴛᴏ ᴄʟᴏɴᴇ.")
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
                await respond(event, "✅ 𝐂ʟᴏɴᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ 🤍🦋")
            except Exception as e: await respond(event, f"❌ 𝐄ʀʀᴏʀ: {e}")

        @client.on(events.NewMessage(pattern=r"^\.back(?: |$)"))
        async def back_cmd(event):
            if not is_auth(event): return
            if not self.original_profiles.get(session_name): return await respond(event, "❌ 𝐍ᴏ ᴘʀᴏꜰɪʟᴇ ʙᴀᴄᴋᴜᴘ ꜰᴏᴜɴᴅ.")
            await respond(event, "🔄 𝐑ᴇᴠᴇʀᴛɪɴɢ ᴘʀᴏꜰɪʟᴇ...")
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
                
            await respond(event, "🔄 **𝐒ʏꜱᴛᴇᴍ 𝐑ᴇꜰʀᴇꜱʜᴇᴅ 𝐆ʟᴏʙᴀʟʟʏ!**")

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
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
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

# ── CONTROLLER BOT (WITH GREEN / RED / BLUE INLINE BUTTONS) ───────────────────

def get_main_menu_buttons(user_id):
    buttons = [
        [
            c_inline("🚀 𝐇ᴏꜱᴛ 𝐔ꜱᴇʀʙᴏᴛ", b"start_host", color="green"),
            c_inline("⚙️ 𝐌ᴀɴᴀɢᴇ 𝐇ᴏꜱᴛ", b"manage_host", color="blue")
        ],
        [
            c_url("👑 𝐂ᴏɴᴛᴀᴄᴛ 𝐎ᴡɴᴇʀ", "https://t.me/hawabaazhun", color="blue"),
            c_url("💬 𝐒ᴜᴘᴘᴏʀᴛ", "https://t.me/comlengs", color="green")
        ]
    ]
    if user_id in ADMIN_USERS:
        admin_buttons = [
            [
                c_inline("📊 𝐒ᴛᴀᴛᴜꜱ", b"admin_status", color="blue"),
                c_inline("🛠 𝐌ᴀɴᴀɢᴇᴍᴇɴᴛ", b"admin_management", color="blue")
            ],
            [
                c_inline("📢 𝐁ʀᴏᴀᴅᴄᴀꜱᴛ", b"admin_broadcast", color="green"),
                c_inline("💎 𝐏ʀᴇᴍɪᴜᴍ", b"admin_premium", color="green")
            ],
            [
                c_inline("🤖 𝐒ᴜᴍᴍᴏɴ 𝐀ʟʟ", b"admin_summon", color="blue"),
                c_inline("🔄 𝐑ᴇꜱᴇᴛ", b"admin_reset", color="red")
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
                f"🔗 **𝐔ꜱᴇʀɴᴀᴍᴇ:** {username}\n"
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
        "╔═══════════════════════════╗\n"
        "   ☠️ **𝐑𝐄𝐁𝐄𝐋 𝐔𝐒𝐄𝐑𝐁𝐎𝐓 𝐇𝐎𝐒𝐓𝐄𝐑** ☠️\n"
        "╚═══════════════════════════╝\n\n"
        f"👋 𝐇ᴇʟʟᴏ **{first_name}**!\n\n"
        "╭───────────────────────────╮\n"
        "┃ 🤖 𝐂ʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ\n"
        "┃ ʟᴏɢ ɪɴ ᴀɴᴅ ʜᴏꜱᴛ ʏᴏᴜʀ ᴜꜱᴇʀʙᴏᴛ.\n"
        "╰───────────────────────────╯"
    )
    if user_id in ADMIN_USERS: 
        welcome_text += "\n\n👑 **𝐎ᴡɴᴇʀ 𝐃ᴀꜱʜʙᴏᴀʀᴅ 𝐀ᴄᴛɪᴠᴇ**"
        
    if is_edit:
        try:
            await event.edit(welcome_text, buttons=get_main_menu_buttons(user_id))
        except Exception as e:
            if "not modified" not in str(e).lower():
                await event.respond(welcome_text, buttons=get_main_menu_buttons(user_id))
    else:
        await event.respond(welcome_text, buttons=get_main_menu_buttons(user_id))

async def finalize_login(user_id, client, event):
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
    save_session_to_file(session_str, user_name, session_name, host_user_id=user_id, account_id=account_id)
    started = await manager.start_account(session_str, session_name)

    if started:
        # --- NEW ADMIN NOTIFICATION LOGIC ---
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
        # ------------------------------------
        
        await event.respond(
            f"✅ **𝐋ᴏɢɪɴ 𝐒ᴜᴄᴄᴇꜱꜱꜰᴜʟ!**\n\n👤 **𝐔ꜱᴇʀ:** {user_name}\n🔑 **𝐒ᴇꜱꜱɪᴏɴ:** `{session_name}`\n\n🚀 𝐒ᴇɴᴅ `.ping` ᴛᴏ ᴠᴇʀɪꜰʏ.",
            buttons=[[c_inline("🏠 𝐌ᴀɪɴ 𝐌ᴇɴᴜ", b"back_to_main", color="green")]]
        )
    else:
        await event.respond(
            "⚠️ 𝐋ᴏɢɪɴ ꜰᴀɪʟᴇᴅ, ꜱʟᴏᴛ ꜰʀᴇᴇᴅ.",
            buttons=[[c_inline("🔙 𝐁ᴀᴄᴋ ᴛᴏ 𝐌ᴇɴᴜ", b"back_to_main", color="red")]]
        )
    
    if user_id in login_states: del login_states[user_id]

@controller_bot.on(events.NewMessage(pattern="/start"))
async def start_cmd(event):
    user_id = event.sender_id
    if not await check_force_join(user_id):
        buttons = [
            [c_url("📢 𝐉ᴏɪɴ 𝐂ʜᴀɴɴᴇʟ", f"https://t.me/{FORCE_JOIN_CHANNEL}", color="blue")],
            [c_inline("🔄 𝐈 𝐇ᴀᴠᴇ 𝐉ᴏɪɴᴇᴅ", b"check_join", color="green")]
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
        await event.answer(f"❌ 𝐇ᴏꜱᴛɪɴɢ 𝐋ɪᴍɪᴛ 𝐑ᴇᴀᴄʜᴇᴅ ({limit})!", alert=True)
        return

    login_states[user_id] = {"state": "WAITING_PHONE"}
    await event.answer()
    await event.respond("📱 **𝐒ᴛᴇᴘ 𝟏:** 𝐄ɴᴛᴇʀ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ.\n*(𝐄xᴀᴍᴘʟᴇ: +919876543210)*")

@controller_bot.on(events.CallbackQuery(data=b"manage_host"))
async def manage_host_callback(event):
    user_id = event.sender_id
    if not await check_force_join(user_id):
        return await event.answer("❌ 𝐉ᴏɪɴ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ!", alert=True)
        
    sessions = load_saved_sessions()
    user_sessions = [s for s in sessions if s.get("host_user_id") == user_id]
    
    if not user_sessions:
        await event.answer("𝐍ᴏ ᴀᴄᴄᴏᴜɴᴛꜱ ʜᴏꜱᴛᴇᴅ ʏᴇᴛ!", alert=True)
        return await handle_welcome(event, user_id, is_edit=True)
        
    buttons = []
    for s in user_sessions:
        s_name = s.get("session_name")
        is_online = s_name in manager.active_clients
        status_emoji = "🟢" if is_online else "🔴"
        btn_color = "green" if is_online else "red"
        buttons.append([c_inline(f"{status_emoji} {s.get('name')} ({s_name})", f"manage_{s_name}".encode(), color=btn_color)])
    
    if user_sessions:
        buttons.append([c_inline("🤖 𝐒ᴜᴍᴍᴏɴ 𝐌ʏ 𝐇ᴏꜱᴛᴇᴅ 𝐁ᴏᴛꜱ", b"user_summon_prompt", color="blue")])
        
    buttons.append([c_inline("🔙 𝐁ᴀᴄᴋ ᴛᴏ 𝐌ᴇɴᴜ", b"back_to_main", color="red")])
    
    text = (
        "╔═══════════════════════════╗\n"
        "   ⚙️ **𝐌𝐀𝐍𝐀𝐆𝐄 𝐇𝐎𝐒𝐓𝐄𝐃 𝐁𝐎𝐓𝐒** ⚙️\n"
        "╚═══════════════════════════╝\n\n"
        f"📊 **𝐘ᴏᴜʀ 𝐇ᴏꜱᴛᴇᴅ 𝐀ᴄᴄᴏᴜɴᴛꜱ ({len(user_sessions)}/{get_user_limit(user_id)}):**"
    )
    await event.edit(text, buttons=buttons)

@controller_bot.on(events.CallbackQuery(data=b"admin_summon"))
async def admin_summon_cb(event):
    if event.sender_id not in ADMIN_USERS: return
    login_states[event.sender_id] = {"state": "WAITING_ADMIN_SUMMON"}
    await event.answer()
    await event.respond("📢 **𝐀ᴅᴍɪɴ 𝐒ᴜᴍᴍᴏɴ 𝐌ᴏᴅᴇ**\n\n𝐒ᴇɴᴅ ᴛʜᴇ 𝐆𝐂 ᴏʀ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ ᴛᴏ ꜱᴜᴍᴍᴏɴ **𝐀𝐋𝐋** ʙᴏᴛꜱ.\n*(𝐓ʏᴘᴇ `/cancel` ᴛᴏ ᴀʙᴏʀᴛ)*")

@controller_bot.on(events.CallbackQuery(data=b"user_summon_prompt"))
async def user_summon_cb(event):
    user_id = event.sender_id
    if not await check_force_join(user_id):
        return await event.answer("❌ 𝐉ᴏɪɴ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ!", alert=True)
    login_states[user_id] = {"state": "WAITING_USER_SUMMON"}
    await event.answer()
    await event.respond("📢 **𝐒ᴜᴍᴍᴏɴ 𝐌ᴏᴅᴇ**\n\n𝐒ᴇɴᴅ ᴛʜᴇ 𝐆𝐂 ᴏʀ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ ᴛᴏ ꜱᴜᴍᴍᴏɴ **ʏᴏᴜʀ** ʙᴏᴛꜱ.\n*(𝐓ʏᴘᴇ `/cancel` ᴛᴏ ᴀʙᴏʀᴛ)*")

@controller_bot.on(events.CallbackQuery(data=b"admin_management"))
async def admin_mgmt_callback(event):
    if event.sender_id not in ADMIN_USERS: return
    sessions = load_saved_sessions()
    if not sessions:
        await event.edit("📭 𝐍ᴏ ᴀᴄᴄᴏᴜɴᴛꜱ ʜᴏꜱᴛᴇᴅ.", buttons=[[c_inline("🔙 𝐁ᴀᴄᴋ", b"back_to_main", color="blue")]])
        return
        
    buttons = []
    for s in sessions:
        s_name = s.get("session_name")
        is_online = s_name in manager.active_clients
        status_emoji = "🟢" if is_online else "🔴"
        btn_color = "green" if is_online else "red"
        buttons.append([c_inline(f"{status_emoji} {s.get('name')} ({s_name})", f"manage_{s_name}".encode(), color=btn_color)])
    buttons.append([c_inline("🔙 𝐁ᴀᴄᴋ", b"back_to_main", color="blue")])
    await event.edit(
        "╔═══════════════════════════╗\n"
        "   🛠 **𝐀𝐃𝐌𝐈𝐍 𝐌𝐀𝐍𝐀𝐆𝐄𝐌𝐄𝐍𝐓** 🛠\n"
        "╚═══════════════════════════╝",
        buttons=buttons
    )

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
        "╔═══════════════════════════╗\n"
        "   🛠 **𝐌𝐀𝐍𝐀𝐆𝐄 𝐀𝐂𝐂𝐎𝐔𝐍𝐓** 🛠\n"
        "╚═══════════════════════════╝\n\n"
        f"╭─ 👤 **𝐍ᴀᴍᴇ:** {session_data.get('name')}\n"
        f"├─ 🔑 **𝐒ᴇꜱꜱɪᴏɴ:** `{s_name}`\n"
        f"╰─ 📊 **𝐒ᴛᴀᴛᴜꜱ:** {status}"
    )
    
    buttons = [
        [c_inline("🔌 𝐃ɪꜱᴄᴏɴɴᴇᴄᴛ", f"stop_{s_name}".encode(), color="blue")],
        [c_inline("🗑️ 𝐋ᴏɢᴏᴜᴛ & 𝐃ᴇʟᴇᴛᴇ", f"del_{s_name}".encode(), color="red")]
    ]
    
    back_data = b"admin_management" if (is_admin and not is_owner) else b"manage_host"
    buttons.append([c_inline("🔙 𝐁ᴀᴄᴋ", back_data, color="green")])
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
    await event.answer(f"🔌 𝐃ɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ! {s_name} ɪꜱ ꜰʀᴇᴇ.", alert=True)
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
    await event.answer(f"🗑️ 𝐃ᴇʟᴇᴛᴇᴅ! {s_name} ɪꜱ ꜰʀᴇᴇ.", alert=True)
    
    if user_id in ADMIN_USERS and session_data.get("host_user_id") != user_id:
        await admin_mgmt_callback(event)
    else:
        await manage_host_callback(event)

@controller_bot.on(events.NewMessage())
async def unified_state_machine(event):
    user_id = event.sender_id
    text = event.raw_text.strip() if event.raw_text else ""

    if user_id not in login_states: return

    # Universal cancellation handler preventing logic lock-in
    if text.lower() == "/cancel":
        await event.respond("🚫 𝐂ᴀɴᴄᴇʟʟᴇᴅ.")
        if "client" in login_states[user_id]:
            try: await login_states[user_id]["client"].disconnect()
            except: pass
        del login_states[user_id]
        return

    # Ignore other incoming commands so they don't break the active state (e.g. treated as OTP)
    if text.startswith("/"): return

    state_data = login_states[user_id]
    state = state_data["state"]

    if state == "WAITING_PHONE":
        phone = text
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        try:
            code_req = await client.send_code_request(phone)
            login_states[user_id].update({
                "state": "WAITING_OTP", "phone": phone,
                "phone_code_hash": code_req.phone_code_hash, "client": client
            })
            await event.respond("📩 **𝐒ᴛᴇᴘ 𝟐:** 𝐄ɴᴛᴇʀ 𝐎𝐓𝐏 ᴡɪᴛʜ ꜱᴘᴀᴄᴇꜱ.\n*(𝐄xᴀᴍᴘʟᴇ: 1 2 3 4 5)*")
        except Exception as e:
            await event.respond(f"❌ 𝐅ᴀɪʟᴇᴅ: `{e}`")
            await client.disconnect()
            del login_states[user_id]

    elif state == "WAITING_OTP":
        client = state_data["client"]
        phone = state_data["phone"]
        hash_code = state_data["phone_code_hash"]
        otp = text.replace(" ", "").replace("-", "")

        try:
            await client.sign_in(phone=phone, code=otp, phone_code_hash=hash_code)
            await finalize_login(user_id, client, event)
        except SessionPasswordNeededError:
            login_states[user_id]["state"] = "WAITING_2FA"
            await event.respond("🔒 **𝐒ᴛᴇᴘ 𝟑:** 𝐄ɴᴛᴇʀ 𝟐𝐅𝐀 ᴘᴀꜱꜱᴡᴏʀᴅ:")
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
            await finalize_login(user_id, client, event)
        except PasswordHashInvalidError:
            await event.respond("❌ 𝐈ɴᴄᴏʀʀᴇᴄᴛ 𝟐𝐅𝐀 ᴘᴀꜱꜱᴡᴏʀᴅ.")
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
            await event.respond(f"✅ `{target_id}` ɪꜱ ɴᴏᴡ **𝐏ʀᴇᴍɪᴜᴍ**!")
        except ValueError: await event.respond("❌ 𝐈ɴᴠᴀʟɪᴅ 𝐔ꜱᴇʀ 𝐈𝐃.")
        del login_states[user_id]
        
    elif state == "WAITING_PREMIUM_REMOVE":
        try:
            target_id = int(text)
            remove_premium_user(target_id)
            await event.respond(f"✅ `{target_id}` ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ 𝐏ʀᴇᴍɪᴜᴍ.")
        except ValueError: await event.respond("❌ 𝐈ɴᴠᴀʟɪᴅ 𝐔ꜱᴇʀ 𝐈𝐃.")
        del login_states[user_id]

@controller_bot.on(events.CallbackQuery(data=b"admin_status"))
async def admin_status_callback(event):
    if event.sender_id not in ADMIN_USERS: return
    await event.answer("𝐅ᴇᴛᴄʜɪɴɢ...")
    start_time = time.time()
    await controller_bot.get_me() 
    ping = round((time.time() - start_time) * 1000, 2)
    
    users_count, sessions, active_count, prem_count = len(get_bot_users()), load_saved_sessions(), len(manager.active_clients), len(get_premium_users())
    text = (
        "╔═══════════════════════════╗\n"
        "   📊 **𝐒𝐘𝐒𝐓𝐄𝐌 𝐒𝐓𝐀𝐓𝐔𝐒** 📊\n"
        "╚═══════════════════════════╝\n\n"
        "╭───────────────────────────╮\n"
        f"┃ 👥 **𝐔ꜱᴇʀꜱ:** `{users_count}`\n"
        f"┃ 💎 **𝐏ʀᴇᴍɪᴜᴍ:** `{prem_count}`\n"
        f"┃ 🤖 **𝐇ᴏꜱᴛᴇᴅ:** `{len(sessions)}` (🟢 `{active_count}`)\n"
        f"┃ ⚡ **𝐏ɪɴɢ:** `{ping} ᴍꜱ`\n"
        "╰───────────────────────────╯"
    )
    await event.edit(text, buttons=[[c_inline("🔙 𝐁ᴀᴄᴋ", b"back_to_main", color="blue")]])

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
            c_inline("➕ 𝐀ᴅᴅ", b"prem_add", color="green"),
            c_inline("➖ 𝐑ᴇᴍᴏᴠᴇ", b"prem_rem", color="red")
        ],
        [
            c_inline("📋 𝐋ɪꜱᴛ", b"prem_list", color="blue"),
            c_inline("🔙 𝐁ᴀᴄᴋ", b"back_to_main", color="blue")
        ]
    ]
    await event.edit(
        "╔═══════════════════════════╗\n"
        "   💎 **𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐌𝐀𝐍𝐀𝐆𝐄𝐌𝐄𝐍𝐓** 💎\n"
        "╚═══════════════════════════╝",
        buttons=buttons
    )

@controller_bot.on(events.CallbackQuery(data=b"prem_add"))
async def prem_add_cb(event):
    if event.sender_id not in ADMIN_USERS: return
    login_states[event.sender_id] = {"state": "WAITING_PREMIUM_ADD"}
    await event.answer()
    await event.respond("➕ 𝐒ᴇɴᴅ 𝐔ꜱᴇʀ 𝐈𝐃 ᴛᴏ ɢʀᴀɴᴛ 𝐏ʀᴇᴍɪᴜᴍ.")

@controller_bot.on(events.CallbackQuery(data=b"prem_rem"))
async def prem_rem_cb(event):
    if event.sender_id not in ADMIN_USERS: return
    login_states[event.sender_id] = {"state": "WAITING_PREMIUM_REMOVE"}
    await event.answer()
    await event.respond("➖ 𝐒ᴇɴᴅ 𝐔ꜱᴇʀ 𝐈𝐃 ᴛᴏ ʀᴇᴍᴏᴠᴇ 𝐏ʀᴇᴍɪᴜᴍ.")

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
        
    for file_path in [SESSIONS_FILE, USERS_FILE, PREMIUM_FILE]:
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
                
    manager.active_rebel_loops.clear()
    login_states.clear()
    await status_msg.edit("✅ **𝐒ᴇʀᴠᴇʀ 𝐑ᴇꜱᴇᴛ 𝐂ᴏᴍᴘʟᴇᴛᴇ!**")

async def main():
    print("🚀 𝐒ᴛᴀʀᴛɪɴɢ 𝐂ᴏɴᴛʀᴏʟʟᴇʀ 𝐁ᴏᴛ...")
    await controller_bot.start(bot_token=BOT_TOKEN)

    # FIXED: Register persistent menu button using functions.bots.SetBotCommandsRequest
    try:
        await controller_bot(functions.bots.SetBotCommandsRequest(
            scope=types.BotCommandScopeDefault(),
            lang_code='',
            commands=[types.BotCommand(command='start', description='Open Rebel Hoster Panel')]
        ))
    except Exception as e:
        print(f"⚠️ 𝐂ᴏᴜʟᴅ ɴᴏᴛ ꜱᴇᴛ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ: {e}")

    saved = load_saved_sessions()
    print(f"📦 𝐅ᴏᴜɴᴅ {len(saved)} ᴀᴄᴄᴏᴜɴᴛꜱ.")
    for s in saved:
        await manager.start_account(s["session"], s["session_name"])

    print("🤖 𝐀ʟʟ ᴄᴏᴍᴘᴏɴᴇɴᴛꜱ ᴀᴄᴛɪᴠᴇ.")
    await controller_bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

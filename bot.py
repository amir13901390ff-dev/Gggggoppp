# ربات تلگرام مدیریت گروه (نسخه کامل و حرفه‌ای)
# سازنده: امیرعلی فروزان اصل
# پایتون - Python Telegram Bot

import telebot
import json
import os
import time
import random
import string
from datetime import datetime, timedelta
from collections import defaultdict
from telebot import types

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = telebot.TeleBot(BOT_TOKEN)

# ========================= دیتابیس ساده =========================

DATA_FILE = "admin_bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "groups": {}, "warnings": {}, "banned": [], "muted": {},
        "filters": {}, "whitelist_links": {}, "blacklist_users": {},
        "night_mode": {}, "captcha_pending": {}, "night_hours": {}
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ========================= تنظیمات ضد اسپم =========================

spam_tracker = defaultdict(list)
SPAM_LIMIT = 5
SPAM_WINDOW = 10

BAD_WORDS = ["فحش۱", "فحش۲", "فحش۳"]
LINK_PATTERNS = ["http://", "https://", "t.me/", "telegram.me/"]

# ========================= توابع کمکی =========================

def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

def is_creator(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status == 'creator'
    except:
        return False

def gen_captcha():
    """ساخت یک کد کپچای ساده عددی"""
    return str(random.randint(1000, 9999))

# ========================= شروع و راهنما =========================

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        text = """
🛡️ *ربات مدیریت گروه تلگرام - نسخه حرفه‌ای*

من به شما کمک می‌کنم گروه تلگرام خود را کامل مدیریت کنید!

📌 *قابلیت‌ها:*
✅ ضد اسپم، ضد لینک و فیلتر کلمات
✅ کپچای ورود اعضای جدید
✅ خوشامدگویی و خداحافظی خودکار
✅ سیستم هشدار ۳ مرحله‌ای
✅ بن، آنبن، اخراج و سکوت کاربران
✅ ترفیع و عزل ادمین
✅ حالت شب (قفل خودکار زمان‌بندی شده)
✅ لیست سفید لینک مجاز
✅ لیست سیاه کاربران
✅ پشتیبان‌گیری از تنظیمات گروه
✅ آمار کامل گروه

📌 *دستورات ادمین:*
/warn /unwarn /warns - مدیریت هشدار
/ban /unban /kick - بن، آنبن و اخراج
/mute [دقیقه] /unmute - سکوت و رفع سکوت
/promote /demote - ترفیع و عزل ادمین
/lock /unlock - قفل و باز کردن گروه
/nightmode [ساعت_شروع] [ساعت_پایان] - حالت شب خودکار
/setwelcome [متن] /setgoodbye [متن]
/addfilter /rmfilter /filters
/whitelist [دامنه] - افزودن لینک مجاز
/blacklist - افزودن کاربر به لیست سیاه (ریپلای)
/rules [متن] /showrules
/pin /unpin /report
/adminlist - لیست ادمین‌ها
/stats - آمار گروه
/backup /restore - پشتیبان‌گیری تنظیمات

👨‍💻 سازنده: *امیرعلی فروزان اصل*
        """
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ========================= سیستم هشدار =========================

@bot.message_handler(commands=['warn'])
def warn_user(message):
    if message.chat.type not in ['group', 'supergroup']:
        return
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    
    user = message.reply_to_message.from_user
    user_id = str(user.id)
    chat_id = str(message.chat.id)
    
    data["warnings"].setdefault(chat_id, {})
    data["warnings"][chat_id][user_id] = data["warnings"][chat_id].get(user_id, 0) + 1
    warns = data["warnings"][chat_id][user_id]
    save_data(data)
    
    if warns >= 3:
        try:
            bot.ban_chat_member(message.chat.id, user.id)
            bot.send_message(message.chat.id, f"🚫 *{user.first_name}* به دلیل ۳ هشدار از گروه بن شد!", parse_mode="Markdown")
            data["warnings"][chat_id][user_id] = 0
            save_data(data)
        except:
            pass
    else:
        bot.send_message(message.chat.id, f"⚠️ *{user.first_name}* هشدار گرفت! ({warns}/3)", parse_mode="Markdown")

@bot.message_handler(commands=['unwarn'])
def unwarn_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    
    user = message.reply_to_message.from_user
    user_id = str(user.id)
    chat_id = str(message.chat.id)
    
    if chat_id in data["warnings"] and user_id in data["warnings"][chat_id]:
        data["warnings"][chat_id][user_id] = max(0, data["warnings"][chat_id][user_id] - 1)
        save_data(data)
    bot.reply_to(message, f"✅ یک هشدار از *{user.first_name}* کم شد.", parse_mode="Markdown")

@bot.message_handler(commands=['warns'])
def show_warns(message):
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    user = message.reply_to_message.from_user
    chat_id = str(message.chat.id)
    warns = data["warnings"].get(chat_id, {}).get(str(user.id), 0)
    bot.reply_to(message, f"⚠️ *{user.first_name}* دارای {warns}/3 هشدار است.", parse_mode="Markdown")

# ========================= بن / آنبن / اخراج =========================

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    user = message.reply_to_message.from_user
    try:
        bot.ban_chat_member(message.chat.id, user.id)
        bot.send_message(message.chat.id, f"🚫 *{user.first_name}* از گروه بن شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    user = message.reply_to_message.from_user
    try:
        bot.unban_chat_member(message.chat.id, user.id)
        bot.send_message(message.chat.id, f"✅ *{user.first_name}* آنبن شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

@bot.message_handler(commands=['kick'])
def kick_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    user = message.reply_to_message.from_user
    try:
        bot.ban_chat_member(message.chat.id, user.id)
        bot.unban_chat_member(message.chat.id, user.id)
        bot.send_message(message.chat.id, f"👢 *{user.first_name}* از گروه اخراج شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

# ========================= سکوت (میوت) =========================

@bot.message_handler(commands=['mute'])
def mute_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    user = message.reply_to_message.from_user
    parts = message.text.split()
    minutes = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 30
    until = datetime.now() + timedelta(minutes=minutes)
    try:
        bot.restrict_chat_member(
            message.chat.id, user.id, until_date=until,
            can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False
        )
        bot.send_message(message.chat.id, f"🔇 *{user.first_name}* به مدت {minutes} دقیقه سکوت شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    user = message.reply_to_message.from_user
    try:
        bot.restrict_chat_member(
            message.chat.id, user.id, can_send_messages=True,
            can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True
        )
        bot.send_message(message.chat.id, f"🔊 سکوت *{user.first_name}* برداشته شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

# ========================= ترفیع و عزل ادمین =========================

@bot.message_handler(commands=['promote'])
def promote_user(message):
    if not is_creator(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ فقط سازنده گروه می‌تواند ادمین اضافه کند.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    user = message.reply_to_message.from_user
    try:
        bot.promote_chat_member(
            message.chat.id, user.id,
            can_delete_messages=True, can_restrict_members=True,
            can_pin_messages=True, can_invite_users=True
        )
        bot.send_message(message.chat.id, f"👑 *{user.first_name}* ادمین شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

@bot.message_handler(commands=['demote'])
def demote_user(message):
    if not is_creator(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ فقط سازنده گروه می‌تواند ادمین را عزل کند.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    user = message.reply_to_message.from_user
    try:
        bot.promote_chat_member(
            message.chat.id, user.id,
            can_delete_messages=False, can_restrict_members=False,
            can_pin_messages=False, can_invite_users=False
        )
        bot.send_message(message.chat.id, f"⬇️ *{user.first_name}* از ادمینی عزل شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

@bot.message_handler(commands=['adminlist'])
def admin_list(message):
    try:
        admins = bot.get_chat_administrators(message.chat.id)
        text = "👑 *لیست ادمین‌های گروه:*\n\n"
        for a in admins:
            role = "سازنده" if a.status == "creator" else "ادمین"
            text += f"• {a.user.first_name} ({role})\n"
        text += "\n👨‍💻 سازنده ربات: *امیرعلی فروزان اصل*"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

# ========================= خوشامدگویی و خداحافظی =========================

@bot.message_handler(commands=['setwelcome'])
def set_welcome(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    text = message.text.replace('/setwelcome', '').strip()
    if not text:
        bot.reply_to(message, "❌ متن را بنویسید. مثال: /setwelcome سلام {name} خوش آمدید!")
        return
    chat_id = str(message.chat.id)
    data["groups"].setdefault(chat_id, {})
    data["groups"][chat_id]["welcome"] = text
    save_data(data)
    bot.reply_to(message, "✅ پیام خوشامدگویی تنظیم شد!")

@bot.message_handler(commands=['setgoodbye'])
def set_goodbye(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    text = message.text.replace('/setgoodbye', '').strip()
    if not text:
        bot.reply_to(message, "❌ متن را بنویسید. مثال: /setgoodbye {name} از گروه خارج شد.")
        return
    chat_id = str(message.chat.id)
    data["groups"].setdefault(chat_id, {})
    data["groups"][chat_id]["goodbye"] = text
    save_data(data)
    bot.reply_to(message, "✅ پیام خداحافظی تنظیم شد!")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    chat_id = str(message.chat.id)
    welcome_text = data.get("groups", {}).get(chat_id, {}).get("welcome", "سلام {name}! 👋 به گروه خوش آمدید!")
    
    for member in message.new_chat_members:
        name = member.first_name
        code = gen_captcha()
        data["captcha_pending"].setdefault(chat_id, {})
        data["captcha_pending"][chat_id][str(member.id)] = code
        save_data(data)
        
        try:
            bot.restrict_chat_member(message.chat.id, member.id, can_send_messages=False)
        except:
            pass
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"✅ تایید ({code})", callback_data=f"captcha_{member.id}_{code}"))
        
        text = welcome_text.replace("{name}", name) + f"\n\n🔐 برای تایید عضویت روی دکمه زیر بزنید تا بتوانید پیام دهید."
        bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("captcha_"))
def handle_captcha(call):
    _, user_id, code = call.data.split("_")
    chat_id = str(call.message.chat.id)
    
    if call.from_user.id != int(user_id):
        bot.answer_callback_query(call.id, "❌ این دکمه برای شما نیست!", show_alert=True)
        return
    
    pending = data["captcha_pending"].get(chat_id, {})
    if pending.get(user_id) == code:
        try:
            bot.restrict_chat_member(
                call.message.chat.id, int(user_id), can_send_messages=True,
                can_send_media_messages=True, can_send_other_messages=True
            )
        except:
            pass
        del data["captcha_pending"][chat_id][user_id]
        save_data(data)
        bot.answer_callback_query(call.id, "✅ تایید شد! خوش آمدید.")
        bot.edit_message_text("✅ عضویت تایید شد.", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['left_chat_member'])
def goodbye_member(message):
    chat_id = str(message.chat.id)
    goodbye_text = data.get("groups", {}).get(chat_id, {}).get("goodbye", "{name} از گروه خارج شد. 👋")
    text = goodbye_text.replace("{name}", message.left_chat_member.first_name)
    bot.send_message(message.chat.id, text)

# ========================= فیلتر کلمات و لینک =========================

@bot.message_handler(commands=['addfilter'])
def add_filter(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    word = message.text.replace('/addfilter', '').strip()
    if not word:
        bot.reply_to(message, "❌ کلمه فیلتر را بنویسید.")
        return
    chat_id = str(message.chat.id)
    data["filters"].setdefault(chat_id, [])
    if word not in data["filters"][chat_id]:
        data["filters"][chat_id].append(word)
        save_data(data)
    bot.reply_to(message, f"✅ کلمه «{word}» به فیلتر اضافه شد!")

@bot.message_handler(commands=['rmfilter'])
def remove_filter(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    word = message.text.replace('/rmfilter', '').strip()
    chat_id = str(message.chat.id)
    if chat_id in data["filters"] and word in data["filters"][chat_id]:
        data["filters"][chat_id].remove(word)
        save_data(data)
        bot.reply_to(message, f"✅ کلمه «{word}» حذف شد!")
    else:
        bot.reply_to(message, "❌ این کلمه در فیلتر نیست.")

@bot.message_handler(commands=['filters'])
def show_filters(message):
    chat_id = str(message.chat.id)
    filters_list = data.get("filters", {}).get(chat_id, [])
    text = "🚫 *کلمات فیلتر شده:*\n\n" + "\n".join(f"• {w}" for w in filters_list) if filters_list else "📋 هیچ فیلتری تنظیم نشده."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['whitelist'])
def whitelist_domain(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    domain = message.text.replace('/whitelist', '').strip()
    if not domain:
        bot.reply_to(message, "❌ دامنه را بنویسید. مثال: /whitelist instagram.com")
        return
    chat_id = str(message.chat.id)
    data["whitelist_links"].setdefault(chat_id, [])
    if domain not in data["whitelist_links"][chat_id]:
        data["whitelist_links"][chat_id].append(domain)
        save_data(data)
    bot.reply_to(message, f"✅ دامنه «{domain}» مجاز شد!")

@bot.message_handler(commands=['blacklist'])
def blacklist_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام کاربر ریپلای کنید.")
        return
    user = message.reply_to_message.from_user
    chat_id = str(message.chat.id)
    data["blacklist_users"].setdefault(chat_id, [])
    if user.id not in data["blacklist_users"][chat_id]:
        data["blacklist_users"][chat_id].append(user.id)
        save_data(data)
    try:
        bot.ban_chat_member(message.chat.id, user.id)
    except:
        pass
    bot.reply_to(message, f"🚫 *{user.first_name}* به لیست سیاه اضافه و بن شد!", parse_mode="Markdown")

# ========================= قفل گروه و حالت شب =========================

@bot.message_handler(commands=['lock'])
def lock_group(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    try:
        bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=False))
        bot.send_message(message.chat.id, "🔒 گروه قفل شد!")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

@bot.message_handler(commands=['unlock'])
def unlock_group(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    try:
        bot.set_chat_permissions(message.chat.id, types.ChatPermissions(
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True
        ))
        bot.send_message(message.chat.id, "🔓 قفل گروه برداشته شد!")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

@bot.message_handler(commands=['nightmode'])
def set_night_mode(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "❌ فرمت درست: /nightmode 23 7  (قفل ساعت ۲۳ تا ۷ صبح)")
        return
    chat_id = str(message.chat.id)
    data["night_hours"][chat_id] = {"start": int(parts[1]), "end": int(parts[2])}
    save_data(data)
    bot.reply_to(message, f"🌙 حالت شب تنظیم شد: قفل از ساعت {parts[1]} تا {parts[2]}")

def night_mode_scheduler():
    """بررسی دوره‌ای ساعت برای قفل/باز کردن خودکار گروه در حالت شب"""
    while True:
        try:
            hour_now = datetime.now().hour
            for chat_id, hours in data.get("night_hours", {}).items():
                start, end = hours["start"], hours["end"]
                should_lock = (start <= hour_now or hour_now < end) if start > end else (start <= hour_now < end)
                is_locked = data["night_mode"].get(chat_id, False)
                if should_lock and not is_locked:
                    bot.set_chat_permissions(int(chat_id), types.ChatPermissions(can_send_messages=False))
                    data["night_mode"][chat_id] = True
                    save_data(data)
                elif not should_lock and is_locked:
                    bot.set_chat_permissions(int(chat_id), types.ChatPermissions(
                        can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True
                    ))
                    data["night_mode"][chat_id] = False
                    save_data(data)
        except:
            pass
        time.sleep(300)

# ========================= قوانین =========================

@bot.message_handler(commands=['rules'])
def set_rules(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    text = message.text.replace('/rules', '').strip()
    if not text:
        bot.reply_to(message, "❌ قوانین را بنویسید.")
        return
    chat_id = str(message.chat.id)
    data["groups"].setdefault(chat_id, {})
    data["groups"][chat_id]["rules"] = text
    save_data(data)
    bot.reply_to(message, "✅ قوانین گروه تنظیم شد!")

@bot.message_handler(commands=['showrules'])
def show_rules(message):
    chat_id = str(message.chat.id)
    rules = data.get("groups", {}).get(chat_id, {}).get("rules", "قوانینی تنظیم نشده.")
    bot.send_message(message.chat.id, f"📜 *قوانین گروه:*\n\n{rules}", parse_mode="Markdown")

# ========================= سنجاق و گزارش =========================

@bot.message_handler(commands=['pin'])
def pin_message(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام مورد نظر ریپلای کنید.")
        return
    try:
        bot.pin_chat_message(message.chat.id, message.reply_to_message.id)
        bot.reply_to(message, "📌 پیام سنجاق شد!")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

@bot.message_handler(commands=['unpin'])
def unpin_message(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    try:
        bot.unpin_chat_message(message.chat.id)
        bot.reply_to(message, "📌 سنجاق برداشته شد!")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

@bot.message_handler(commands=['report'])
def report_message(message):
    if not message.reply_to_message:
        bot.reply_to(message, "❌ روی پیام مورد نظر ریپلای کنید.")
        return
    try:
        admins = bot.get_chat_administrators(message.chat.id)
        reporter = message.from_user.first_name
        reported = message.reply_to_message.from_user.first_name
        for admin in admins:
            if not admin.user.is_bot:
                try:
                    bot.send_message(
                        admin.user.id,
                        f"🚨 *گزارش جدید*\n\nگزارش‌دهنده: {reporter}\nکاربر گزارش‌شده: {reported}\nگروه: {message.chat.title}",
                        parse_mode="Markdown"
                    )
                except:
                    pass
        bot.reply_to(message, "✅ گزارش به ادمین‌ها ارسال شد.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

# ========================= پشتیبان‌گیری تنظیمات =========================

@bot.message_handler(commands=['backup'])
def backup_settings(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return
    chat_id = str(message.chat.id)
    settings = data["groups"].get(chat_id, {})
    text = json.dumps(settings, ensure_ascii=False, indent=2)
    bot.send_message(message.chat.id, f"💾 *پشتیبان تنظیمات گروه:*\n\n```\n{text}\n```", parse_mode="Markdown")

# ========================= آمار گروه =========================

@bot.message_handler(commands=['stats'])
def group_stats(message):
    if message.chat.type not in ['group', 'supergroup']:
        return
    try:
        count = bot.get_chat_member_count(message.chat.id)
        admins = bot.get_chat_administrators(message.chat.id)
        chat_id = str(message.chat.id)
        warns_count = len(data.get("warnings", {}).get(chat_id, {}))
        filters_count = len(data.get("filters", {}).get(chat_id, []))
        blacklist_count = len(data.get("blacklist_users", {}).get(chat_id, []))
        
        text = f"""
📊 *آمار گروه {message.chat.title}*

👥 تعداد اعضا: {count}
👑 تعداد ادمین: {len(admins)}
⚠️ کاربران هشداردار: {warns_count}
🚫 فیلترهای فعال: {filters_count}
⛔ لیست سیاه: {blacklist_count}

📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
👨‍💻 سازنده: *امیرعلی فروزان اصل*
        """
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

# ========================= ضد اسپم، ضد لینک و فیلتر خودکار =========================

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def auto_moderate(message):
    if is_admin(message.chat.id, message.from_user.id):
        return
    
    text = message.text or ""
    chat_id = str(message.chat.id)
    user_id = message.from_user.id
    
    now = time.time()
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if now - t < SPAM_WINDOW]
    spam_tracker[user_id].append(now)
    
    if len(spam_tracker[user_id]) > SPAM_LIMIT:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.restrict_chat_member(message.chat.id, user_id, until_date=datetime.now() + timedelta(minutes=5), can_send_messages=False)
            bot.send_message(message.chat.id, f"🚫 *{message.from_user.first_name}* به دلیل اسپم ۵ دقیقه سکوت شد!", parse_mode="Markdown")
        except:
            pass
        return
    
    whitelisted = data.get("whitelist_links", {}).get(chat_id, [])
    for pattern in LINK_PATTERNS:
        if pattern in text.lower():
            if any(w in text.lower() for w in whitelisted):
                continue
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"🔗 پیام *{message.from_user.first_name}* به دلیل ارسال لینک حذف شد!", parse_mode="Markdown")
            except:
                pass
            return
    
    chat_filters = data.get("filters", {}).get(chat_id, []) + BAD_WORDS
    for word in chat_filters:
        if word.lower() in text.lower():
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"🚫 پیام *{message.from_user.first_name}* به دلیل محتوای نامناسب حذف شد!", parse_mode="Markdown")
            except:
                pass
            return

# ========================= اجرای ربات =========================

if __name__ == "__main__":
    import threading
    print("🛡️ ربات مدیریت گروه شروع شد...")
    print("👨‍💻 سازنده: امیرعلی فروزان اصل")
    threading.Thread(target=night_mode_scheduler, daemon=True).start()
    bot.infinity_polling()

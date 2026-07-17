import telebot
from telebot import types
import requests
import subprocess
import json

# ضع توكن بوت التلغرام الخاص بك هنا
TELEGRAM_BOT_TOKEN = '8322167386:AAG7QRrtTwJNJ2da2j08LSq977zub1yyjTE'

# الـ Access Token الخاص بك المدمج في الكود
ACCESS_TOKEN = "EAAOegvFEZCzABR7uYSrVM63berz3UYcXDE7kgSXtEtsXNsW1AY4z2cLjA3mji1X2aCOc9mkUakirvqmFUoaTQY4ynm3WZB2NOXAt7ZA38a0NyXWb2lteqeNHpfv5Kg6WFBOkZCG8kFGPhNGwV3t0VqpzBruw3OVfcZA9qijyGvPkRA8aqoAdarOXN12PO0k80UVoe"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# تخزين الحالة
current_stream = {"process": None, "live_video_id": None, "stream_url": None, "m3u8_url": None, "title": "بث مباشر"}
user_state = {} 

# الدول المسموح لها برؤية البث فقط (المغرب، الجزائر، تونس، ليبيا، العراق، سوريا، فلسطين، الأردن)
ARAB_COUNTRIES = ["MA", "DZ", "TN", "LY", "IQ", "SY", "PS", "JO"]

# --- لوحة الأزرار ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶️ بدء بث جديد", callback_data="start_live"))
    markup.add(types.InlineKeyboardButton("⏹ إيقاف البث", callback_data="stop_live"))
    markup.add(types.InlineKeyboardButton("🔄 تغيير الرابط", callback_data="change_link"))
    markup.add(types.InlineKeyboardButton("📊 حالة البث", callback_data="status"))
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "مرحباً بك! تحكم بالبث المباشر عبر الأزرار أدناه:", reply_markup=get_main_menu())

# --- معالجة ضغطات الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "start_live":
        user_state[call.message.chat.id] = "waiting_for_link"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🚀 يرجى إرسال رابط البث (M3U8) الآن للبدء:")

    elif call.data == "stop_live":
        bot.answer_callback_query(call.id)
        stop_live_func(call.message)

    elif call.data == "change_link":
        user_state[call.message.chat.id] = "waiting_for_new_link"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔄 أرسل رابط الـ M3U8 الجديد للتبديل الفوري:")

    elif call.data == "status":
        bot.answer_callback_query(call.id)
        status_msg = f"🟢 البث يعمل حالياً بنشاط بنظام Copy.\n🔗 الرابط: `{current_stream['m3u8_url']}`" if current_stream["process"] and current_stream["process"].poll() is None else "🔴 البث متوقف حالياً."
        bot.send_message(call.message.chat.id, status_msg, parse_mode="Markdown")

# --- استقبال الروابط النصية ---
@bot.message_handler(func=lambda message: message.chat.id in user_state)
def handle_link(message):
    state = user_state.get(message.chat.id)
    url = message.text.strip()
    
    if state == "waiting_for_link":
        start_live_func(message, url)
    elif state == "waiting_for_new_link":
        change_link_func(message, url)
    
    user_state.pop(message.chat.id, None)

# --- دالة بدء البث المباشر ---
def start_live_func(message, m3u8_url):
    bot.reply_to(message, "⏳ جاري إنشاء البث وتطبيق القيود الجغرافية...")
    
    targeting = {"geo_locations": {"countries": ARAB_COUNTRIES}}
    
    fb_url = "https://graph.facebook.com/v19.0/me/live_videos"
    payload = {
        'title': "Live Stream", 
        'status': 'LIVE_NOW', 
        'targeting': json.dumps(targeting), 
        'is_dvr_enabled': 'false', # 🔒 تعطيل خاصية إرجاع الفيديو للخلف
        'access_token': ACCESS_TOKEN
    }
    
    try:
        response = requests.post(fb_url, data=payload).json()
        if "stream_url" not in response:
            bot.reply_to(message, f"❌ خطأ من فيسبوك: {response}")
            return

        current_stream.update({"stream_url": response["stream_url"], "live_video_id": response["id"], "m3u8_url": m3u8_url})
        
        # أمر FFmpeg بنظام الـ Copy المباشر والخفيف بدون تعديل أبعاد الشاشة داخل البث
        cmd = [
            'ffmpeg', '-re', 
            '-i', m3u8_url, 
            '-c', 'copy', 
            '-f', 'flv', response["stream_url"]
        ]
        
        current_stream["process"] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bot.reply_to(message, "✅ تم بدء البث بنجاح!\n• البث يعمل بنظام الـ Copy الخفيف.\n• تم قفل ميزة إرجاع البث للخلف.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء تشغيل FFmpeg: {str(e)}")

# --- دالة تغيير الرابط أثناء البث ---
def change_link_func(message, new_url):
    if not current_stream["process"] or current_stream["process"].poll() is not None:
        bot.reply_to(message, "❌ لا يوجد بث نشط حالياً لتغيير رابطه.")
        return
        
    bot.reply_to(message, "🔄 جاري تبديل الرابط...")
    
    # إنهاء عملية FFmpeg الحالية
    try:
        current_stream["process"].terminate()
        current_stream["process"].wait()
    except:
        pass
        
    current_stream["m3u8_url"] = new_url
    
    # تشغيل الرابط الجديد مباشرة بنظام الـ Copy على نفس الـ stream_url لضمان عدم فصل اللايف
    cmd = [
        'ffmpeg', '-re', 
        '-i', new_url, 
        '-c', 'copy', 
        '-f', 'flv', current_stream["stream_url"]
    ]
    current_stream["process"] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    bot.reply_to(message, "✅ تم تحديث رابط البث بنجاح دون انقطاع الفيديو.")

# --- دالة إيقاف البث نهائياً ---
def stop_live_func(message):
    if current_stream["process"]:
        bot.reply_to(message, "🛑 جاري إيقاف البث وإغلاق الفيديو...")
        try:
            current_stream["process"].terminate()
            current_stream["process"].wait()
        except:
            pass
        
        # إعلام فيسبوك بإنهاء البث بشكل رسمي
        requests.post(f"https://graph.facebook.com/v19.0/{current_stream['live_video_id']}", data={'end_live_video': 'true', 'access_token': ACCESS_TOKEN})
        current_stream["process"] = None
        bot.reply_to(message, "🏁 تم إنهاء وإغلاق البث المباشر بالكامل.")
    else:
        bot.reply_to(message, "❌ لا يوجد بث يعمل حالياً لإيقافه.")

bot.infinity_polling()

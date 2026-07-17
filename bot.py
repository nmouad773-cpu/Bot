import telebot
from telebot import types
import requests
import subprocess
import json
import threading
import time

# ضع توكن بوت التلغرام الخاص بك هنا
TELEGRAM_BOT_TOKEN = '8322167386:AAG7QRrtTwJNJ2da2j08LSq977zub1yyjTE'

# الـ Access Token الخاص بصفحتك على فيسبوك
ACCESS_TOKEN = "EAAOegvFEZCzABR7uYSrVM63berz3UYcXDE7kgSXtEtsXNsW1AY4z2cLjA3mji1X2aCOc9mkUakirvqmFUoaTQY4ynm3WZB2NOXAt7ZA38a0NyXWb2lteqeNHpfv5Kg6WFBOkZCG8kFGPhNGwV3t0VqpzBruw3OVfcZA9qijyGvPkRA8aqoAdarOXN12PO0k80UVoe"

# معرف الصفحة الخاص بك (Page ID)
PAGE_ID = "1078731531992880"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# تخزين الحالة
current_stream = {
    "process": None, 
    "live_video_id": None, 
    "stream_url": None, 
    "m3u8_url": None, 
    "title": "بث مباشر", 
    "description": "بث مباشر",
    "phase": "idle"
}
user_state = {} 

# الدول العربية المسموح لها فقط ورسمياً برؤية البث (يظهر لهم فقط ويختفي عن باقي العالم)
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
    bot.reply_to(message, "مرحباً بك! تحكم بالبث المباشر لصفحتك عبر الأزرار أدناه:", reply_markup=get_main_menu())

# --- معالجة ضغطات الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "start_live":
        user_state[call.message.chat.id] = "waiting_for_description"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📝 يرجى إرسال [وصف البث] المباشر الآن:")

    elif call.data == "stop_live":
        bot.answer_callback_query(call.id)
        stop_live_func(call.message)

    elif call.data == "change_link":
        user_state[call.message.chat.id] = "waiting_for_new_link"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔄 أرسل رابط الـ M3U8 الجديد للتبديل الفوري المباشر:")

    elif call.data == "status":
        bot.answer_callback_query(call.id)
        if current_stream["process"] and current_stream["process"].poll() is None:
            if current_stream["phase"] == "black_screen":
                status_msg = f"⚫ البث في مرحلة الشاشة السوداء المؤقتة (دقيقتين).\n📝 الوصف: {current_stream['description']}\n🔗 الرابط المنتظر: `{current_stream['m3u8_url']}`"
            else:
                status_msg = f"🟢 البث يعمل حالياً بنشاط بنظام Copy المباشر.\n📝 الوصف: {current_stream['description']}\n🔗 الرابط الحالي: `{current_stream['m3u8_url']}`"
        else:
            status_msg = "🔴 البث متوقف حالياً."
        bot.send_message(call.message.chat.id, status_msg, parse_mode="Markdown")

# --- استقبال المدخلات النصية ---
@bot.message_handler(func=lambda message: message.chat.id in user_state)
def handle_inputs(message):
    state = user_state.get(message.chat.id)
    text = message.text.strip()
    
    if state == "waiting_for_description":
        current_stream["description"] = text
        user_state[message.chat.id] = "waiting_for_link"
        bot.send_message(message.chat.id, f"✅ تم حفظ الوصف بنجاح.\n🚀 الآن، يرجى إرسال رابط البث الاحتياطي (M3U8):")
        
    elif state == "waiting_for_link":
        user_state.pop(message.chat.id, None)
        # تشغيل البث في الخلفية لضمان عدم تعليق البوت أثناء الـ 2 دقائق
        threading.Thread(target=start_live_sequence, args=(message, text), daemon=True).start()
        
    elif state == "waiting_for_new_link":
        user_state.pop(message.chat.id, None)
        change_link_func(message, text)

# --- دالة تسلسل البث وتحويله تلقائياً دون انقطاع ---
def start_live_sequence(message, m3u8_url):
    bot.send_message(message.chat.id, "⏳ جاري إنشاء فيديو البث وتخصيصه للدول العربية المحددة فقط...")
    
    # إعداد الحصر الجغرافي: تراه هذه الدول فقط ويختفي عن بقية العالم
    targeting = {"geo_locations": {"countries": ARAB_COUNTRIES}}
    live_description = current_stream.get("description", "بث مباشر")
    
    fb_url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/live_videos"
    payload = {
        'title': live_description,
        'description': live_description,
        'status': 'LIVE_NOW', 
        'targeting': json.dumps(targeting), 
        'is_dvr_enabled': 'false', 
        'access_token': ACCESS_TOKEN
    }
    
    try:
        response = requests.post(fb_url, data=payload).json()
        if "stream_url" not in response:
            bot.reply_to(message, f"❌ خطأ من فيسبوك: {response}")
            return

        current_stream.update({
            "stream_url": response["stream_url"], 
            "live_video_id": response["id"], 
            "m3u8_url": m3u8_url,
            "phase": "black_screen"
        })
        
        bot.send_message(message.chat.id, "⚫ بدأ البث المباشر الآن! المرحلة الأولى: شاشة سوداء وصوت صامت لمدة دقيقتين...")
        
        # تشغيل الشاشة السوداء على نفس الـ stream_url الخاص بالبث
        black_cmd = [
            'ffmpeg', '-re',
            '-f', 'lavfi', '-i', 'color=c=black:s=1280x720:r=30',
            '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', '-acodec', 'aac',
            '-f', 'flv', response["stream_url"]
        ]
        
        current_stream["process"] = subprocess.Popen(black_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # انتطار 120 ثانية (دقيقتين) دقيقة بدقة وهي تعمل
        time.sleep(120)
        
        # التأكد أن المستخدم لم يقم بالضغط على زر إيقاف البث أثناء الانتظار
        if current_stream["process"] is None or current_stream["live_video_id"] != response["id"]:
            return
            
        # التحويل الفوري والمباشر على نفس فيديو الفيسبوك دون إغلاق اللايف
        current_stream["phase"] = "live"
        
        # إنهاء عملية الشاشة السوداء والبدء فوراً وبأقل من جزء من الثانية بالرابط الجديد بنظام الـ Copy
        current_stream["process"].terminate()
        current_stream["process"].wait()
        
        copy_cmd = [
            'ffmpeg', '-re', 
            '-i', current_stream["m3u8_url"], 
            '-c', 'copy', 
            '-f', 'flv', response["stream_url"]
        ]
        
        current_stream["process"] = subprocess.Popen(copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bot.send_message(message.chat.id, "🔄 مرت الدقيقتان بنجاح! تم تحويل نفس البث المباشر الآن تلقائياً إلى الرابط الاحتياطي بنظام الـ Copy الخفيف.")
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ غير متوقع: {str(e)}")

# --- دالة تغيير الرابط فورياً أثناء البث ---
def change_link_func(message, new_url):
    if not current_stream["process"] or current_stream["process"].poll() is not None:
        bot.reply_to(message, "❌ لا يوجد بث نشط حالياً لتغيير رابطه.")
        return
        
    bot.reply_to(message, "🔄 جاري تحويل مسار البث الحالي إلى الرابط الجديد فوراً...")
    
    try:
        current_stream["process"].terminate()
        current_stream["process"].wait()
    except:
        pass
        
    current_stream["m3u8_url"] = new_url
    current_stream["phase"] = "live"
    
    cmd = [
        'ffmpeg', '-re', 
        '-i', new_url, 
        '-c', 'copy', 
        '-f', 'flv', current_stream["stream_url"]
    ]
    current_stream["process"] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    bot.reply_to(message, "✅ تم تحويل البث إلى الرابط الجديد بنجاح وبدون انقطاع الفيديو.")

# --- دالة إيقاف البث نهائياً ---
def stop_live_func(message):
    if current_stream["process"] or current_stream["phase"] != "idle":
        bot.reply_to(message, "🛑 جاري إيقاف البث وإغلاق الفيديو بالكامل...")
        try:
            current_stream["process"].terminate()
            current_stream["process"].wait()
        except:
            pass
        
        if current_stream["live_video_id"]:
            requests.post(f"https://graph.facebook.com/v19.0/{current_stream['live_video_id']}", data={'end_live_video': 'true', 'access_token': ACCESS_TOKEN})
            
        current_stream["process"] = None
        current_stream["phase"] = "idle"
        bot.reply_to(message, "🏁 تم إنهاء وإغلاق البث المباشر بالكامل وحجبه عن الجميع بنجاح.")
    else:
        bot.reply_to(message, "❌ لا يوجد بث يعمل حالياً لإيقافه.")

bot.infinity_polling()

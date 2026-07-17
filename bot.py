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

# تخزين حالة البثين (الرئيسي والاحتياطي)
current_stream = {
    "main_process": None,      # لعملية الشاشة السوداء
    "backup_process": None,    # لعملية رابط الـ M3U8 الخاص بك
    "live_video_id": None, 
    "main_stream_url": None, 
    "backup_stream_url": None,
    "m3u8_url": None, 
    "description": "بث مباشر",
    "phase": "idle"
}
user_state = {} 

# الدول العربية المسموح لها فقط برؤية البث منشوراً على الصفحة
ARAB_COUNTRIES = ["MA", "DZ", "TN", "LY", "IQ", "SY", "PS", "JO"]

# --- لوحة الأزرار الرئيسية ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶️ بدء بث جديد", callback_data="start_live"))
    markup.add(types.InlineKeyboardButton("⏹ إيقاف البث", callback_data="stop_live"))
    markup.add(types.InlineKeyboardButton("🔄 تغيير الرابط الاحتياطي", callback_data="change_link"))
    markup.add(types.InlineKeyboardButton("📊 حالة البث", callback_data="status"))
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "مرحباً بك! تحكم بنظام البث المزدوج (رئيسي + احتياطي) لصفحتك:", reply_markup=get_main_menu())

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "start_live":
        user_state[call.message.chat.id] = "waiting_for_description"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📝 يرجى إرسال [وصف البث] ليتم نشره في البوست:")

    elif call.data == "stop_live":
        bot.answer_callback_query(call.id)
        stop_live_func(call.message)

    elif call.data == "change_link":
        user_state[call.message.chat.id] = "waiting_for_new_link"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔄 أرسل رابط الـ M3U8 الجديد لتحديث البث الاحتياطي فوراً:")

    elif call.data == "status":
        bot.answer_callback_query(call.id)
        is_main_running = current_stream["main_process"] and current_stream["main_process"].poll() is None
        is_backup_running = current_stream["backup_process"] and current_stream["backup_process"].poll() is None
        
        if is_main_running or is_backup_running:
            status_msg = f"🟢 البث نشط ومستقر على الصفحة الحاليّة.\n"
            status_msg += f"⚫ البث الرئيسي (الشاشة السوداء): {'عمل جاري ⏳' if is_main_running else 'منتهي ومحول تم ✅'}\n"
            status_msg += f"🔵 البث الاحتياطي (رابطك): {'يعمل بنجاح 🚀' if is_backup_running else 'متوقف ❌'}\n"
            status_msg += f"🔗 الرابط الحالي: `{current_stream['m3u8_url']}`"
        else:
            status_msg = "🔴 البث متوقف حالياً بالكامل."
        bot.send_message(call.message.chat.id, status_msg, parse_mode="Markdown")

# --- استقبال النصوص ---
@bot.message_handler(func=lambda message: message.chat.id in user_state)
def handle_inputs(message):
    state = user_state.get(message.chat.id)
    text = message.text.strip()
    
    if state == "waiting_for_description":
        current_stream["description"] = text
        user_state[message.chat.id] = "waiting_for_link"
        bot.send_message(message.chat.id, f"✅ تم اعتماد وصف البوست.\n🚀 الآن، أرسل رابط الـ M3U8 لتشغيله على السيرفر الاحتياطي:")
        
    elif state == "waiting_for_link":
        user_state.pop(message.chat.id, None)
        threading.Thread(target=start_live_sequence, args=(message, text), daemon=True).start()
        
    elif state == "waiting_for_new_link":
        user_state.pop(message.chat.id, None)
        change_link_func(message, text)

# --- دالة البث المزدوج الذكي (رئيسي واحتياطي) ---
def start_live_sequence(message, m3u8_url):
    bot.send_message(message.chat.id, "⏳ جاري حجز البث المباشر ونشره كـ Post مخصص للدول العربية فقط...")
    
    targeting = {"geo_locations": {"countries": ARAB_COUNTRIES}}
    live_description = current_stream.get("description", "بث مباشر")
    
    fb_url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/live_videos"
    payload = {
        'title': live_description,
        'description': live_description,
        'status': 'LIVE_NOW', 
        'published': 'true',  # لعمل بوست (Post) رسمي ومباشر على الصفحة
        'targeting': json.dumps(targeting), 
        'is_dvr_enabled': 'false', 
        'access_token': ACCESS_TOKEN
    }
    
    try:
        response = requests.post(fb_url, data=payload).json()
        
        # جلب الرابط الرئيسي والاحتياطي الآمنين
        main_url = response.get("secure_stream_url") or response.get("stream_url")
        backup_url = response.get("backup_secure_stream_url") or response.get("backup_stream_url")
        
        if not main_url:
            bot.reply_to(message, f"❌ فشل جلب روابط البث من فيسبوك: {response}")
            return

        # في حال لم يقم فيسبوك بإرجاع رابط احتياطي تلقائياً، نقوم بتوليده بناءً على الرئيسي لضمان عدم التوقف
        if not backup_url:
            backup_url = main_url.replace("rtmp://", "rtmp://").replace("rtmps://", "rtmps://") 
            bot.send_message(message.chat.id, "⚠️ تنبيه: تم استخدام الرابط الرئيسي الموحد لعدم توفر مفتاح احتياطي مستقل بالحساب.")

        current_stream.update({
            "main_stream_url": main_url,
            "backup_stream_url": backup_url,
            "live_video_id": response["id"], 
            "m3u8_url": m3u8_url,
            "phase": "running"
        })
        
        bot.send_message(message.chat.id, "✅ تم نشر البث بنجاح على الصفحة!\n⚫ جاري إرسال الشاشة السوداء للمفتاح الرئيسي (لمدة دقيقتين)...\n🔵 وجاري تشغيل رابطك على المفتاح الاحتياطي بالتزامن...")
        
        # 1. تشغيل الشاشة السوداء على المفتاح الرئيسي وتتوقف تلقائياً بعد 120 ثانية (دقيقتين)
        black_cmd = [
            'ffmpeg', '-re',
            '-f', 'lavfi', '-i', 'color=c=black:s=1280x720:r=30',
            '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-t', '120', 
            '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', '-acodec', 'aac',
            '-f', 'flv', main_url
        ]
        current_stream["main_process"] = subprocess.Popen(black_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 2. تشغيل رابط الـ M3U8 الخاص بك على المفتاح الاحتياطي فوراً وبدون إنهاء
        copy_cmd = [
            'ffmpeg', '-re', 
            '-i', m3u8_url, 
            '-c', 'copy', 
            '-f', 'flv', backup_url
        ]
        current_stream["backup_process"] = subprocess.Popen(copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # انتظار دقيقتين للتأكيد للمستخدم
        time.sleep(120)
        if current_stream["phase"] == "running":
            bot.send_message(message.chat.id, "🔄 انتهت الـ 2 دقائق شاشة سوداء! فيسبوك ينقل المشاهدين الآن تلقائياً إلى بث الرابط الاحتياطي المستقر.")

    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

# --- تغيير الرابط الاحتياطي فورا ---
def change_link_func(message, new_url):
    if not current_stream["backup_process"] or current_stream["backup_process"].poll() is not None:
        bot.reply_to(message, "❌ لا يوجد بث احتياطي نشط حالياً لتغييره.")
        return
        
    bot.reply_to(message, "🔄 جاري تبديل الرابط على السيرفر الاحتياطي فوراً...")
    
    try:
        current_stream["backup_process"].terminate()
        current_stream["backup_process"].wait()
    except:
        pass
        
    current_stream["m3u8_url"] = new_url
    
    cmd = [
        'ffmpeg', '-re', 
        '-i', new_url, 
        '-c', 'copy', 
        '-f', 'flv', current_stream["backup_stream_url"]
    ]
    current_stream["backup_process"] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    bot.reply_to(message, "✅ تم تحديث الرابط على البث الاحتياطي بنجاح وبدون التأثير على المنشور.")

# --- إيقاف البث بالكامل ---
def stop_live_func(message):
    if current_stream["main_process"] or current_stream["backup_process"] or current_stream["phase"] != "idle":
        bot.reply_to(message, "🛑 جاري إغلاق البث الرئيسي والاحتياطي وحذف الفيديو...")
        
        for proc_key in ["main_process", "backup_process"]:
            if current_stream[proc_key]:
                try:
                    current_stream[proc_key].terminate()
                    current_stream[proc_key].wait()
                except:
                    pass
                current_stream[proc_key] = None
                
        if current_stream["live_video_id"]:
            requests.post(f"https://graph.facebook.com/v19.0/{current_stream['live_video_id']}", data={'end_live_video': 'true', 'access_token': ACCESS_TOKEN})
            
        current_stream["phase"] = "idle"
        bot.reply_to(message, "🏁 تم إنهاء وإغلاق البث بالكامل من الصفحة بنجاح.")
    else:
        bot.reply_to(message, "❌ لا يوجد بث يعمل حالياً لإيقافه.")

bot.infinity_polling()

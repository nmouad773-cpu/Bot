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

# تخزين حالة البثين
current_stream = {
    "main_process": None,      # لعملية الشاشة السوداء المستمرة (المفتاح الرئيسي)
    "backup_process": None,    # لعملية رابط الـ M3U8 الخاص بك (المفتاح الاحتياطي)
    "live_video_id": None, 
    "main_stream_url": None, 
    "backup_stream_url": None,
    "m3u8_url": None, 
    "description": "بث مباشر",
    "phase": "idle"            # idle, black_screen, live
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
    bot.reply_to(message, "مرحباً بك! تم ضبط النظام: البث الرئيسي مستمر دائماً والاحتياطي ينطلق عند الدقيقة الثانية:", reply_markup=get_main_menu())

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
        if current_stream["phase"] == "black_screen":
            status_msg = f"⚫ البث الرئيسي (شاشة سوداء) شغال الآن ومستمر.\n⏳ متبقي أقل من دقيقتين لينطلق رابطك الاحتياطي تلقائياً دون قفل الرئيسي.\n🔗 الرابط المنتظر: `{current_stream['m3u8_url']}`"
        elif current_stream["phase"] == "live":
            status_msg = f"🟢 البث المزدوج مستقر بالكامل!\n⚫ الرئيسي (شاشة سوداء): شغال ومستمر حمايةً للبث 🛡️\n🔵 الاحتياطي (رابطك): يعمل الآن بنشاط وبثبات 🚀\n🔗 الرابط الحالي: `{current_stream['m3u8_url']}`"
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
        bot.send_message(message.chat.id, f"✅ تم اعتماد وصف البوست.\n🚀 الآن، أرسل رابط الـ M3U8 ليتم جدولة بثه على السيرفر الاحتياطي بعد دقيقتين:")
        
    elif state == "waiting_for_link":
        user_state.pop(message.chat.id, None)
        threading.Thread(target=start_live_sequence, args=(message, text), daemon=True).start()
        
    elif state == "waiting_for_new_link":
        user_state.pop(message.chat.id, None)
        change_link_func(message, text)

# --- دالة البث المزدوج المستمر الحامي من الانقطاع ---
def start_live_sequence(message, m3u8_url):
    bot.send_message(message.chat.id, "⏳ جاري حجز البث المباشر ونشره كـ Post مخصص للدول العربية فقط...")
    
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
        
        main_url = response.get("secure_stream_url") or response.get("stream_url")
        backup_url = response.get("backup_secure_stream_url") or response.get("backup_stream_url")
        
        if not main_url:
            bot.reply_to(message, f"❌ فشل جلب روابط البث من فيسبوك: {response}")
            return

        if not backup_url:
            backup_url = main_url

        current_stream.update({
            "main_stream_url": main_url,
            "backup_stream_url": backup_url,
            "live_video_id": response["id"], 
            "m3u8_url": m3u8_url,
            "phase": "black_screen"
        })
        
        bot.send_message(message.chat.id, "✅ تم نشر البث كـ بوست على الصفحة!\n⚫ البث الرئيسي (الشاشة السوداء) انطلق الآن وسيبقى مستمراً دون توقف لحماية الصفحة...")
        
        # 1. إطلاق الشاشة السوداء على المفتاح الرئيسي بشكل مستمر ودائم (تم إزالة -t 120 ليبقى شغالاً)
        black_cmd = [
            'ffmpeg', '-re',
            '-f', 'lavfi', '-i', 'color=c=black:s=1280x720:r=30',
            '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', '-acodec', 'aac',
            '-f', 'flv', main_url
        ]
        current_stream["main_process"] = subprocess.Popen(black_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 2. الانتظار لمدة دقيقتين (120 ثانية) بينما البث الرئيسي شغال ومستقر تماماً
        time.sleep(120)
        
        # التأكد من أن المستخدم لم يضغط إيقاف أثناء فترة الانتظار
        if current_stream["phase"] == "idle":
            return
            
        # 3. إطلاق رابط الـ M3U8 الخاص بك على المفتاح الاحتياطي (الرئيسي يبقى شغالاً ولا يتم قفله)
        current_stream["phase"] = "live"
        
        copy_cmd = [
            'ffmpeg', '-re', 
            '-i', current_stream["m3u8_url"], 
            '-c', 'copy', 
            '-f', 'flv', backup_url
        ]
        current_stream["backup_process"] = subprocess.Popen(copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bot.send_message(message.chat.id, "🚀 مرت دقيقتان! انطلق البث الاحتياطي الحامل لرابطك الآن بنجاح، والبث الرئيسي شغال بالخلفية لضمان عدم حدوث أي انقطاع.")

    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء تشغيل تسلسل البث: {str(e)}")

# --- تغيير الرابط الاحتياطي فورا ---
def change_link_func(message, new_url):
    current_stream["m3u8_url"] = new_url
    
    # تبديل الرابط الاحتياطي فقط دون المساس بالبث الرئيسي الحامي للايف
    if current_stream["phase"] == "live" and current_stream["backup_process"] and current_stream["backup_process"].poll() is None:
        bot.reply_to(message, "🔄 جاري تحديث الرابط على البث الاحتياطي فوراً...")
        try:
            current_stream["backup_process"].terminate()
            current_stream["backup_process"].wait()
        except:
            pass
            
        cmd = [
            'ffmpeg', '-re', 
            '-i', new_url, 
            '-c', 'copy', 
            '-f', 'flv', current_stream["backup_stream_url"]
        ]
        current_stream["backup_process"] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bot.reply_to(message, "✅ تم تحديث الرابط الاحتياطي بنجاح، والبث مستمر وثابت.")
    else:
        bot.reply_to(message, "✅ تم حفظ الرابط الجديد بنجاح، وسيبدأ البث به تلقائياً عند انتهاء الدقيقتين الأولى.")

# --- إيقاف البث بالكامل ---
def stop_live_func(message):
    if current_stream["phase"] != "idle":
        bot.reply_to(message, "🛑 جاري إيقاف البثين (الرئيسي والاحتياطي) وإغلاق الفيديو نهائياً من الصفحة...")
        current_stream["phase"] = "idle"
        
        # قفل جميع العمليات المفتوحة لـ ffmpeg
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
            
        bot.reply_to(message, "🏁 تم إنهاء وإغلاق البث بالكامل بنجاح.")
    else:
        bot.reply_to(message, "❌ لا يوجد بث يعمل حالياً لإيقافه.")

bot.infinity_polling()

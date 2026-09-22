import os
import json
import base64
from datetime import datetime
from flask import Flask
from threading import Thread
import telebot

# إعدادات بوت تلغرام بالتوكن الجديد
TOKEN = '8831603087:AAGwmhlHEsGKo1Dg7xlifL2AS5AKJpzufVA'
bot = telebot.TeleBot(TOKEN)

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO')
DATA_FILE = 'driver_data.json'

def load_data():
    try:
        if GITHUB_TOKEN and GITHUB_REPO:
            import requests
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                file_content = response.json().get('content')
                decoded_content = base64.b64decode(file_content).decode('utf-8')
                return json.loads(decoded_content)
    except Exception as e:
        print(f"Error loading data: {e}")
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"trips": [], "earnings": {}}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        if GITHUB_TOKEN and GITHUB_REPO:
            import requests
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            
            get_response = requests.get(url, headers=headers)
            sha = get_response.json().get('sha') if get_response.status_code == 200 else None
            
            with open(DATA_FILE, 'rb') as f:
                content_bytes = f.read()
            encoded_content = base64.b64encode(content_bytes).decode('utf-8')
            
            payload = {
                "message": "Update driver data",
                "content": encoded_content,
                "sha": sha
            }
            requests.put(url, headers=headers, json=payload)
    except Exception as e:
        print(f"Error saving data: {e}")

def calculate_price(km):
    if km <= 2:
        return 200
    elif km <= 4:
        return 250
    elif km <= 6:
        return 300
    elif km <= 8:
        return 350
    elif km <= 10:
        return 400
    elif km <= 12:
        return 450
    elif km <= 14:
        return 500
    elif km <= 16:
        return 550
    elif km <= 18:
        return 600
    elif km <= 20:
        return 650
    elif km <= 22:
        return 700
    elif km <= 24:
        return 750
    elif km <= 26:
        return 800
    elif km <= 30:
        return 900
    elif km <= 34:
        return 1000
    elif km <= 36:
        return 1100
    else:
        return 1100 + int((km - 36) / 2) * 100

user_states = {}
user_temp_trip = {}

def get_driver_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📦 إنشاء رحلة جديدة", "📋 الرحلات المتوفرة")
    markup.add("💰 الأرباح اليومية", "📊 الأرباح الشهرية")
    markup.add("📈 الأرباح السنوية", "🗑️ تصفير الأرباح اليومية")
    markup.add("🏠 الرئيسية")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 واجهة الزبون", "🚚 واجهة الناقل")
    bot.send_message(message.chat.id, "مرحباً بك في بوت ترانسبورتر سطيف لنقل البضائع.\nالرجاء اختيار الواجهة للبدء:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "👤 واجهة الزبون")
def customer_interface(message):
    bot.send_message(message.chat.id, "مرحباً بك في واجهة الزبون. يمكنك طلب خدمة النقل عبر التواصل المباشر.")

@bot.message_handler(func=lambda message: message.text == "🚚 واجهة الناقل")
def driver_interface(message):
    bot.send_message(message.chat.id, "🔒 لوحة الناقل محمية.\nالرجاء إدخال كلمة المرور للوصول:")
    user_states[message.chat.id] = "awaiting_password"

@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id] == "awaiting_password")
def check_password(message):
    if message.text == "010203":
        user_states[message.chat.id] = "logged_in"
        bot.send_message(message.chat.id, "✅ تم تسجيل الدخول بنجاح إلى لوحة الناقل.", reply_markup=get_driver_markup())
    else:
        bot.send_message(message.chat.id, "❌ كلمة المرور غير صحيحة. حاول مرة أخرى.")
        user_states.pop(message.chat.id, None)

@bot.message_handler(func=lambda message: message.text == "🏠 الرئيسية")
def go_home(message):
    user_states.pop(message.chat.id, None)
    user_temp_trip.pop(message.chat.id, None)
    send_welcome(message)

# --- إنشاء رحلة جديدة باستخدام الأزرار الشفافة داخل المحادثة ---
@bot.message_handler(func=lambda message: message.text == "📦 إنشاء رحلة جديدة")
def create_trip_start(message):
    if user_states.get(message.chat.id) != "logged_in":
        bot.send_message(message.chat.id, "الرجاء تسجيل الدخول أولاً.")
        return
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("سطيف", callback_data="orig_سطيف"),
        telebot.types.InlineKeyboardButton("العلمة", callback_data="orig_العلمة")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("عين الحجر", callback_data="orig_عين الحجر"),
        telebot.types.InlineKeyboardButton("بوعنداس", callback_data="orig_بوعنداس")
    )
    markup.add(telebot.types.InlineKeyboardButton("✍️ كتابة مكان آخر", callback_data="orig_custom"))
    
    bot.send_message(message.chat.id, "📍 اختر مكان الانطلاق من أزرار المحادثة بالأسفل أو اقطبه:", reply_markup=markup)
    user_states[message.chat.id] = "choosing_origin_inline"

@bot.callback_query_handler(func=lambda call: call.data.startswith("orig_"))
def callback_origin(call):
    chat_id = call.message.chat.id
    val = call.data.replace("orig_", "")
    
    if val == "custom":
        bot.send_message(chat_id, "✍️ اكتب مكان الانطلاق بيدك في المحادثة:")
        user_states[chat_id] = "choosing_origin_text"
    else:
        user_temp_trip[chat_id] = {"origin": val}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("سطيف", callback_data="dest_سطيف"),
            telebot.types.InlineKeyboardButton("العلمة", callback_data="dest_العلمة")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("عين الحجر", callback_data="dest_عين الحجر"),
            telebot.types.InlineKeyboardButton("بوعنداس", callback_data="dest_بوعنداس")
        )
        markup.add(telebot.types.InlineKeyboardButton("✍️ كتابة مكان آخر", callback_data="dest_custom"))
        
        bot.send_message(chat_id, f"📍 الانطلاق: {val}\n📍 اختر مكان الوصول (الوجهة):", reply_markup=markup)
        user_states[chat_id] = "choosing_destination_inline"
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_origin_text")
def set_origin_text(message):
    user_temp_trip[message.chat.id] = {"origin": message.text}
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("سطيف", callback_data="dest_سطيف"),
        telebot.types.InlineKeyboardButton("العلمة", callback_data="dest_العلمة")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("عين الحجر", callback_data="dest_عين الحجر"),
        telebot.types.InlineKeyboardButton("بوعنداس", callback_data="dest_بوعنداس")
    )
    markup.add(telebot.types.InlineKeyboardButton("✍️ كتابة مكان آخر", callback_data="dest_custom"))
    bot.send_message(message.chat.id, "📍 اختر مكان الوصول (الوجهة):", reply_markup=markup)
    user_states[message.chat.id] = "choosing_destination_inline"

@bot.callback_query_handler(func=lambda call: call.data.startswith("dest_"))
def callback_destination(call):
    chat_id = call.message.chat.id
    val = call.data.replace("dest_", "")
    
    if val == "custom":
        bot.send_message(chat_id, "✍️ اكتب مكان الوصول بيدك في المحادثة:")
        user_states[chat_id] = "choosing_destination_text"
    else:
        user_temp_trip[chat_id]["destination"] = val
        ask_distance_method(chat_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_destination_text")
def set_destination_text(message):
    user_temp_trip[message.chat.id]["destination"] = message.text
    ask_distance_method(message.chat.id)

def ask_distance_method(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("نعم (اعتمد 50 كم)", callback_data="dist_50"))
    markup.add(telebot.types.InlineKeyboardButton("إدخال مسافة أخرى بالكيلومتر", callback_data="dist_custom"))
    bot.send_message(chat_id, "📏 المسافة المعتمدة هي 50 كم. هل تريد اعتمادها أم إدخال مسافة أخرى؟", reply_markup=markup)
    user_states[chat_id] = "choosing_distance_inline"

@bot.callback_query_handler(func=lambda call: call.data.startswith("dist_"))
def callback_distance(call):
    chat_id = call.message.chat.id
    val = call.data.replace("dist_", "")
    
    if val == "50":
        process_distance(chat_id, 50.0)
    else:
        bot.send_message(chat_id, "✍️ الرجاء كتابة المسافة بالأرقام فقط (مثال: 15 أو 22):")
        user_states[chat_id] = "choosing_distance_text"
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_distance_text")
def set_distance_text(message):
    try:
        val = float(message.text.replace("كم", "").strip())
        process_distance(message.chat.id, val)
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى كتابة رقم صحيح للمسافة:")

def process_distance(chat_id, distance_val):
    user_temp_trip[chat_id]["distance"] = f"{distance_val} كم"
    price = calculate_price(distance_val)
    user_temp_trip[chat_id]["price_val"] = price
    user_temp_trip[chat_id]["price"] = f"{price} DA"
    
    # حفظ تلقائي للرحلة
    trip = user_temp_trip[chat_id]
    now = datetime.now()
    trip["year"] = str(now.year)
    trip["month"] = f"{now.month:02d}"
    trip["day"] = f"{now.day:02d}"
    
    data = load_data()
    data["trips"].append(trip)
    save_data(data)
    
    bot.send_message(chat_id, f"✅ تم إنشاء وحفظ الرحلة بنجاح!\n- المسار: من {trip['origin']} إلى {trip['destination']}\n- المسافة: {trip['distance']}\n- السعر التلقائي: {trip['price']}", reply_markup=get_driver_markup())
    user_states[chat_id] = "logged_in"
    user_temp_trip.pop(chat_id, None)

# --- عرض الرحلات (إنهاء أخضر / حذف أحمر) ---
@bot.message_handler(func=lambda message: message.text == "📋 الرحلات المتوفرة")
def show_trips(message):
    if user_states.get(message.chat.id) != "logged_in":
        bot.send_message(message.chat.id, "الرجاء تسجيل الدخول أولاً.")
        return
        
    data = load_data()
    trips = data.get("trips", [])
    if not trips:
        bot.send_message(message.chat.id, "لا توجد رحلات مسجلة حالياً.", reply_markup=get_driver_markup())
        return
    
    text = "📋 قائمة الرحلات المتوفرة:\n"
    markup = telebot.types.InlineKeyboardMarkup()
    for idx, trip in enumerate(trips, 1):
        text += f"{idx}. من {trip.get('origin')} إلى {trip.get('destination')} | المسافة: {trip.get('distance')} | السعر: {trip.get('price')}\n"
        markup.add(
            telebot.types.InlineKeyboardButton(f"🟩 إنهاء {idx}", callback_data=f"trip_finish_{idx-1}"),
            telebot.types.InlineKeyboardButton(f"🟥 حذف {idx}", callback_data=f"trip_delete_{idx-1}")
        )
    
    bot.send_message(message.chat.id, text, reply_markup=markup)
    user_states[message.chat.id] = "managing_trips"

@bot.callback_query_handler(func=lambda call: call.data.startswith("trip_"))
def callback_trip_action(call):
    chat_id = call.message.chat.id
    parts = call.data.split("_")
    action = parts[1]
    idx = int(parts[2])
    
    data = load_data()
    trips = data.get("trips", [])
    
    if 0 <= idx < len(trips):
        trip = trips.pop(idx)
        if action == "finish":
            date_key = f"{trip.get('year')}-{trip.get('month')}-{trip.get('day')}"
            if "earnings" not in data:
                data["earnings"] = {}
            current_earning = data["earnings"].get(date_key, 0)
            price_val = trip.get("price_val", 0)
            data["earnings"][date_key] = current_earning + price_val
            save_data(data)
            bot.send_message(chat_id, f"🟩 تم إنهاء الرحلة رقم {idx + 1} بنجاح وإضافتها للأرباح اليومية!")
        else:
            save_data(data)
            bot.send_message(chat_id, f"🟥 تم حذف الرحلة رقم {idx + 1} مباشرة دون إضافتها للأرباح.")
    else:
        bot.send_message(chat_id, "❌ هذه الرحلة غير موجودة أو تم حذفها مسبقاً.")
    bot.answer_callback_query(call.id)
    show_trips(call.message)

# --- إدارة الأرباح اليومية ---
@bot.message_handler(func=lambda message: message.text == "💰 الأرباح اليومية")
def show_daily_earnings(message):
    if user_states.get(message.chat.id) != "logged_in":
        return
    data = load_data()
    earnings = data.get("earnings", {})
    if not earnings:
        bot.send_message(message.chat.id, "لا توجد أرباح مسجلة بعد.", reply_markup=get_driver_markup())
        return
    
    text = "💰 تفاصيل الأرباح اليومية:\n"
    markup = telebot.types.InlineKeyboardMarkup()
    for idx, (date, amount) in enumerate(earnings.items(), 1):
        text += f"{idx}. 📅 يوم {date} ⟵ المجموع: {amount} DA\n"
        markup.add(telebot.types.InlineKeyboardButton(f"🗑️ حذف أرباح يوم {date}", callback_data=f"earn_del_{date}"))
        
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("earn_del_"))
def callback_delete_earning(call):
    chat_id = call.message.chat.id
    target_date = call.data.replace("earn_del_", "")
    
    data = load_data()
    if target_date in data.get("earnings", {}):
        data["earnings"].pop(target_date)
        save_data(data)
        bot.send_message(chat_id, f"✅ تم حذف أرباح يوم {target_date} بنجاح.")
    else:
        bot.send_message(chat_id, "❌ التاريخ غير موجود.")
    bot.answer_callback_query(call.id)
    show_daily_earnings(call.message)

@bot.message_handler(func=lambda message: message.text == "📊 الأرباح الشهرية")
def show_monthly_earnings(message):
    if user_states.get(message.chat.id) != "logged_in":
        return
    data = load_data()
    earnings = data.get("earnings", {})
    if not earnings:
        bot.send_message(message.chat.id, "لا توجد أرباح مسجلة بعد.", reply_markup=get_driver_markup())
        return
    
    monthly = {}
    monthly_details = {}
    for date, amount in earnings.items():
        month_key = date[:7] 
        monthly[month_key] = monthly.get(month_key, 0) + amount
        if month_key not in monthly_details:
            monthly_details[month_key] = []
        monthly_details[month_key].append(f"📅 يوم {date}: {amount} DA")
        
    text = "📊 ملخص الأرباح الشهرية مع التفاصيل:\n"
    for month, amount in monthly.items():
        text += f"\n🗓️ شهر {month} ⟵ المجموع: {amount} DA\n"
        for detail in monthly_details[month]:
            text += f"   • {detail}\n"
            
    bot.send_message(message.chat.id, text, reply_markup=get_driver_markup())

@bot.message_handler(func=lambda message: message.text == "📈 الأرباح السنوية")
def show_yearly_earnings(message):
    if user_states.get(message.chat.id) != "logged_in":
        return
    data = load_data()
    earnings = data.get("earnings", {})
    if not earnings:
        bot.send_message(message.chat.id, "لا توجد أرباح مسجلة بعد.", reply_markup=get_driver_markup())
        return
    
    yearly = {}
    for date, amount in earnings.items():
        year_key = date[:4] 
        yearly[year_key] = yearly.get(year_key, 0) + amount
        
    text = "📈 ملخص الأرباح السنوية:\n"
    for year, amount in yearly.items():
        text += f"📊 سنة {year}: {amount} DA\n"
    bot.send_message(message.chat.id, text, reply_markup=get_driver_markup())

@bot.message_handler(func=lambda message: message.text == "🗑️ تصفير الأرباح اليومية")
def reset_earnings(message):
    if user_states.get(message.chat.id) != "logged_in":
        return
    data = load_data()
    data["earnings"] = {}
    save_data(data)
    bot.send_message(message.chat.id, "🗑️ تم تصفير جميع الأرباح بنجاح.", reply_markup=get_driver_markup())

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()

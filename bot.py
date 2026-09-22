import os
import json
import base64
from datetime import datetime
from flask import Flask
from threading import Thread
import telebot

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

def get_days_in_month(year, month):
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    elif month == 2:
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            return 29
        return 28
    return 30

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
    user_states.pop(message.chat.id, None)
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

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "awaiting_password")
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

# --- بدء إنشاء رحلة جديدة ---
@bot.message_handler(func=lambda message: message.text == "📦 إنشاء رحلة جديدة")
def create_trip_start(message):
    if user_states.get(message.chat.id) != "logged_in":
        bot.send_message(message.chat.id, "الرجاء تسجيل الدخول أولاً من واجهة الناقل.")
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
    
    bot.send_message(message.chat.id, "📍 اختر مكان الانطلاق:", reply_markup=markup)
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
        ask_destination(chat_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_origin_text")
def set_origin_text(message):
    user_temp_trip[message.chat.id] = {"origin": message.text}
    ask_destination(message.chat.id)

def ask_destination(chat_id):
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
    bot.send_message(chat_id, "📍 اختر مكان الوصول (الوجهة):", reply_markup=markup)
    user_states[chat_id] = "choosing_destination_inline"

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
        bot.send_message(chat_id, "✍️ الرجاء كتابة المسافة بالأرقام فقط:")
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
    
    # الانتقال لخطوة اختيار السنة
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("2025", callback_data="year_2025"),
        telebot.types.InlineKeyboardButton("2026", callback_data="year_2026"),
        telebot.types.InlineKeyboardButton("2027", callback_data="year_2027")
    )
    bot.send_message(chat_id, "📅 اختر سنة الانطلاق:", reply_markup=markup)
    user_states[chat_id] = "choosing_year_inline"

@bot.callback_query_handler(func=lambda call: call.data.startswith("year_"))
def callback_year(call):
    chat_id = call.message.chat.id
    year = call.data.replace("year_", "")
    user_temp_trip[chat_id]["year"] = year
    
    # اختيار الشهر
    markup = telebot.types.InlineKeyboardMarkup()
    months = [("جانفي (01)", "01"), ("فيفري (02)", "02"), ("مارس (03)", "03"), ("أفريل (04)", "04"),
              ("ماي (05)", "05"), ("جوان (06)", "06"), ("جويليا (07)", "07"), ("أوت (08)", "08"),
              ("سبتمبر (09)", "09"), ("أكتوبر (10)", "10"), ("نوفمبر (11)", "11"), ("ديسمبر (12)", "12")]
    
    for i in range(0, len(months), 2):
        markup.add(
            telebot.types.InlineKeyboardButton(months[i][0], callback_data=f"month_{months[i][1]}"),
            telebot.types.InlineKeyboardButton(months[i+1][0], callback_data=f"month_{months[i+1][1]}")
        )
    bot.send_message(chat_id, "📆 اختر الشهر:", reply_markup=markup)
    user_states[chat_id] = "choosing_month_inline"
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("month_"))
def callback_month(call):
    chat_id = call.message.chat.id
    month = call.data.replace("month_", "")
    user_temp_trip[chat_id]["month"] = month
    
    year = int(user_temp_trip[chat_id]["year"])
    max_days = get_days_in_month(year, int(month))
    
    # اختيار اليوم حسب عدد أيام الشهر بدقة
    markup = telebot.types.InlineKeyboardMarkup(row_width=6)
    day_buttons = [telebot.types.InlineKeyboardButton(str(d), callback_data=f"day_{d:02d}") for d in range(1, max_days + 1)]
    markup.add(*day_buttons)
    
    bot.send_message(chat_id, f"📆 اختر يوم الانطلاق (من 1 إلى {max_days}):", reply_markup=markup)
    user_states[chat_id] = "choosing_day_inline"
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def callback_day(call):
    chat_id = call.message.chat.id
    day = call.data.replace("day_", "")
    user_temp_trip[chat_id]["day"] = day
    
    # اختيار الوقت (صباحاً / مساءً)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("☀️ صباحاً (AM)", callback_data="period_صباحاً (AM)"),
        telebot.types.InlineKeyboardButton("🌙 مساءً (PM)", callback_data="period_مساءً (PM)")
    )
    bot.send_message(chat_id, "⏰ اختر فترة الوقت:", reply_markup=markup)
    user_states[chat_id] = "choosing_period_inline"
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("period_"))
def callback_period(call):
    chat_id = call.message.chat.id
    period = call.data.replace("period_", "")
    user_temp_trip[chat_id]["period"] = period
    
    # اختيار الساعة من 1 إلى 12
    markup = telebot.types.InlineKeyboardMarkup(row_width=4)
    hour_buttons = [telebot.types.InlineKeyboardButton(f"{h:02d}", callback_data=f"hour_{h:02d}") for h in range(1, 13)]
    markup.add(*hour_buttons)
    
    bot.send_message(chat_id, "🕐 اختر الساعة (من 1 إلى 12):", reply_markup=markup)
    user_states[chat_id] = "choosing_hour_inline"
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("hour_"))
def callback_hour(call):
    chat_id = call.message.chat.id
    hour = call.data.replace("hour_", "")
    user_temp_trip[chat_id]["hour"] = hour
    
    # اختيار الدقائق
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        telebot.types.InlineKeyboardButton("00", callback_data="min_00"),
        telebot.types.InlineKeyboardButton("15", callback_data="min_15"),
        telebot.types.InlineKeyboardButton("30", callback_data="min_30"),
        telebot.types.InlineKeyboardButton("45", callback_data="min_45")
    )
    bot.send_message(chat_id, "⏱️ اختر الدقائق:", reply_markup=markup)
    user_states[chat_id] = "choosing_minute_inline"
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("min_"))
def callback_minute(call):
    chat_id = call.message.chat.id
    minute = call.data.replace("min_", "")
    
    trip = user_temp_trip[chat_id]
    trip["minute"] = minute
    
    # حفظ الرحلة بالكامل
    data = load_data()
    data["trips"].append(trip)
    save_data(data)
    
    time_str = f"{trip['hour']}:{trip['minute']} {trip['period']}"
    date_str = f"{trip['year']}-{trip['month']}-{trip['day']}"
    
    bot.send_message(
        chat_id, 
        f"✅ تم إنشاء وحفظ الرحلة بنجاح!\n"
        f"- المسار: من {trip['origin']} إلى {trip['destination']}\n"
        f"- المسافة: {trip['distance']}\n"
        f"- السعر: {trip['price']}\n"
        f"- التاريخ: {date_str} على الساعة {time_str}", 
        reply_markup=get_driver_markup()
    )
    user_states[chat_id] = "logged_in"
    user_temp_trip.pop(chat_id, None)
    bot.answer_callback_query(call.id)

# --- عرض وإدارة الرحلات ---
@bot.message_handler(func=lambda message: message.text == "📋 الرحلات المتوفرة")
def show_trips(message):
    if user_states.get(message.chat.id) != "logged_in":
        bot.send_message(message.chat.id, "الرجاء تسجيل الدخول أولاً من واجهة الناقل.")
        return
        
    data = load_data()
    trips = data.get("trips", [])
    if not trips:
        bot.send_message(message.chat.id, "لا توجد رحلات مسجلة حالياً.", reply_markup=get_driver_markup())
        return
    
    text = "📋 قائمة الرحلات المتوفرة:\n"
    markup = telebot.types.InlineKeyboardMarkup()
    for idx, trip in enumerate(trips, 1):
        text += f"{idx}. من {trip.get('origin')} إلى {trip.get('destination')} | {trip.get('distance')} | {trip.get('price')}\n"
        markup.add(
            telebot.types.InlineKeyboardButton(f"🟩 إنهاء {idx}", callback_data=f"trip_finish_{idx-1}"),
            telebot.types.InlineKeyboardButton(f"🟥 حذف {idx}", callback_data=f"trip_delete_{idx-1}")
        )
    
    bot.send_message(message.chat.id, text, reply_markup=markup)

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
            bot.send_message(chat_id, f"🟩 تم إنهاء الرحلة رقم {idx + 1} وإضافتها للأرباح اليومية!")
        else:
            save_data(data)
            bot.send_message(chat_id, f"🟥 تم حذف الرحلة رقم {idx + 1} دون إضافتها للأرباح.")
    else:
        bot.send_message(chat_id, "❌ هذه الرحلة غير موجودة أو تم حذفها مسبقاً.")
    bot.answer_callback_query(call.id)
    show_trips(call.message)

# --- إدارة الأرباح اليومية ---
@bot.message_handler(func=lambda message: message.text == "💰 الأرباح اليومية")
def show_daily_earnings(message):
    if user_states.get(message.chat.id) != "logged_in":
        bot.send_message(message.chat.id, "الرجاء تسجيل الدخول أولاً من واجهة الناقل.")
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
def callback_delete_earning_prompt(call):
    chat_id = call.message.chat.id
    target_date = call.data.replace("earn_del_", "")
    user_states[chat_id] = f"confirm_del_earn_{target_date}"
    bot.send_message(chat_id, f"🔒 لحذف أرباح يوم {target_date}، يرجى إدخال الرقم السري في المحادثة:")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, "").startswith("confirm_del_earn_"))
def execute_delete_earning(message):
    chat_id = message.chat.id
    if message.text == "010203":
        target_date = user_states[chat_id].replace("confirm_del_earn_", "")
        data = load_data()
        if target_date in data.get("earnings", {}):
            data["earnings"].pop(target_date)
            save_data(data)
            bot.send_message(chat_id, f"✅ تم حذف أرباح يوم {target_date} بنجاح.", reply_markup=get_driver_markup())
        else:
            bot.send_message(chat_id, "❌ التاريخ غير موجود.", reply_markup=get_driver_markup())
        user_states[chat_id] = "logged_in"
    else:
        bot.send_message(chat_id, "❌ الرقم السري خطأ. تم إلغاء العملية.", reply_markup=get_driver_markup())
        user_states[chat_id] = "logged_in"

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
def reset_earnings_prompt(message):
    if user_states.get(message.chat.id) != "logged_in":
        bot.send_message(message.chat.id, "الرجاء تسجيل الدخول أولاً من واجهة الناقل.")
        return
    user_states[message.chat.id] = "confirm_reset_earnings"
    bot.send_message(message.chat.id, "🔒 لتصفير جميع الأرباح اليومية، يرجى إدخال الرقم السري:")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "confirm_reset_earnings")
def execute_reset_earnings(message):
    chat_id = message.chat.id
    if message.text == "010203":
        data = load_data()
        data["earnings"] = {}
        save_data(data)
        bot.send_message(chat_id, "🗑️ تم تصفير جميع الأرباح اليومية بنجاح.", reply_markup=get_driver_markup())
        user_states[message.chat.id] = "logged_in"
    else:
        bot.send_message(chat_id, "❌ الرقم السري غير صحيح. تم إلغاء التصفير.", reply_markup=get_driver_markup())
        user_states[message.chat.id] = "logged_in"

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

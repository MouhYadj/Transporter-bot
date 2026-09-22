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

# إعدادات الاتصال بـ GitHub لحفظ البيانات بشكل دائم
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

# دالة لحساب السعر تلقائياً بناءً على جدول التسعيرة
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

@bot.message_handler(func=lambda message: message.text == "📦 إنشاء رحلة جديدة")
def create_trip_start(message):
    if user_states.get(message.chat.id) != "logged_in":
        bot.send_message(message.chat.id, "الرجاء تسجيل الدخول أولاً.")
        return
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("سطيف", "العلمة", "اوريسيا", "عين ولمان", "بوغنداس", "عين الحجر")
    bot.send_message(message.chat.id, "📍 اختر أو اكتب مكان الانطلاق في المحادثة:", reply_markup=markup)
    user_states[message.chat.id] = "choosing_origin"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_origin")
def set_origin(message):
    user_temp_trip[message.chat.id] = {"origin": message.text}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("سطيف", "العلمة", "اوريسيا", "عين ولمان", "بوغنداس", "عين الحجر")
    bot.send_message(message.chat.id, "📍 اختر أو اكتب مكان الوصول (الوجهة):", reply_markup=markup)
    user_states[message.chat.id] = "choosing_destination"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_destination")
def set_destination(message):
    user_temp_trip[message.chat.id]["destination"] = message.text
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("نعم (اعتمد 50 كم)", "إدخال مسافة أخرى")
    bot.send_message(message.chat.id, "📏 المسافة المعتمدة هي 50 كم.\nهل تريد اعتمادها أم إدخال مسافة أخرى بالكيلومتر؟", reply_markup=markup)
    user_states[message.chat.id] = "choosing_distance"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_distance")
def set_distance(message):
    if "50" in message.text:
        distance_val = 50.0
    else:
        try:
            distance_val = float(message.text.replace("كم", "").strip())
        except ValueError:
            bot.send_message(message.chat.id, "الرجاء إدخال رقم صحيح للمسافة بالكيلومتر:")
            return

    user_temp_trip[message.chat.id]["distance"] = f"{distance_val} كم"
    price = calculate_price(distance_val)
    user_temp_trip[message.chat.id]["price_val"] = price
    user_temp_trip[message.chat.id]["price"] = f"{price} DA"

    ask_date(message.chat.id)

def ask_date(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("2025", "2026", "2027")
    bot.send_message(chat_id, "📅 اختر سنة الانطلاق:", reply_markup=markup)
    user_states[chat_id] = "choosing_year"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_year")
def set_year(message):
    user_temp_trip[message.chat.id]["year"] = message.text
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    months = ["جانفي (01)", "فيفري (02)", "مارس (03)", "أفريل (04)", "ماي (05)", "جوان (06)", "جويليا (07)", "أوت (08)", "سبتمبر (09)", "أكتوبر (10)", "نوفمبر (11)", "ديسمبر (12)"]
    markup.add(*months)
    bot.send_message(message.chat.id, "📆 اختر الشهر:", reply_markup=markup)
    user_states[message.chat.id] = "choosing_month"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_month")
def set_month(message):
    user_temp_trip[message.chat.id]["month"] = message.text.split()[1].replace("(", "").replace(")", "")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=7)
    days = [str(i) for i in range(1, 32)]
    markup.add(*days)
    bot.send_message(message.chat.id, "📆 اختر يوم الانطلاق (من 1 إلى 30):", reply_markup=markup)
    user_states[message.chat.id] = "choosing_day"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_day")
def set_day(message):
    user_temp_trip[message.chat.id]["day"] = message.text.zfill(2)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("صباحاً (AM)", "مساءً (PM)")
    bot.send_message(message.chat.id, "⏰ الفترة المختارة:", reply_markup=markup)
    user_states[message.chat.id] = "choosing_period"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_period")
def set_period(message):
    user_temp_trip[message.chat.id]["period"] = message.text
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    hours = [f"{i:02d}" for i in range(1, 13)]
    markup.add(*hours)
    bot.send_message(message.chat.id, "🕐 اختر الساعة:", reply_markup=markup)
    user_states[message.chat.id] = "choosing_hour"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_hour")
def set_hour(message):
    user_temp_trip[message.chat.id]["hour"] = message.text
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    minutes = ["00", "10", "20", "30", "40", "50"]
    markup.add(*minutes)
    bot.send_message(message.chat.id, "⏱️ اختر الدقائق:", reply_markup=markup)
    user_states[message.chat.id] = "choosing_minute"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_minute")
def set_minute(message):
    trip = user_temp_trip[message.chat.id]
    trip["minute"] = message.text
    
    data = load_data()
    data["trips"].append(trip)
    save_data(data)
    
    bot.send_message(message.chat.id, f"✅ تم حفظ الرحلة بنجاح في قائمة الرحلات المتوفرة:\n- من {trip['origin']} إلى {trip['destination']}\n- المسافة: {trip['distance']}\n- السعر: {trip['price']}", reply_markup=get_driver_markup())
    user_states[message.chat.id] = "logged_in"
    user_temp_trip.pop(message.chat.id, None)

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
    for idx, trip in enumerate(trips, 1):
        text += f"{idx}. من {trip.get('origin')} إلى {trip.get('destination')} | المسافة: {trip.get('distance')} | السعر: {trip.get('price')}\n"
    
    text += "\nالرجاء كتابة رقم الرحلة المتبوعة بالإجراء في المحادثة (مثال:\n`انهاء 1` لإنهاء الرحلة وإضافتها للأرباح، أو\n`حذف 1` لحذفها مباشرة دون أرباح):"
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_driver_markup())
    user_states[message.chat.id] = "managing_trips"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "managing_trips")
def handle_trip_command(message):
    if message.text == "🏠 الرئيسية" or message.text in ["📦 إنشاء رحلة جديدة", "📋 الرحلات المتوفرة", "💰 الأرباح اليومية", "📊 الأرباح الشهرية", "📈 الأرباح السنوية", "🗑️ تصفير الأرباح اليومية"]:
        return # السماح بالانتقال للأزرار الرئيسية
        
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ صيغة غير صحيحة. اكتب مثلاً: `انهاء 1` أو `حذف 1`", parse_mode="Markdown")
            return
            
        action = parts[0].strip()
        idx = int(parts[1].strip()) - 1
        
        data = load_data()
        trips = data.get("trips", [])
        
        if 0 <= idx < len(trips):
            trip = trips.pop(idx)
            
            if action in ["انهاء", "🟩", "إنهآء"]:
                date_key = f"{trip.get('year')}-{trip.get('month')}-{trip.get('day')}"
                if "earnings" not in data:
                    data["earnings"] = {}
                current_earning = data["earnings"].get(date_key, 0)
                price_val = trip.get("price_val", 0)
                data["earnings"][date_key] = current_earning + price_val
                
                save_data(data)
                bot.send_message(message.chat.id, f"🟩 تم إنهاء الرحلة رقم {idx + 1} بنجاح وإضافتها إلى الأرباح اليومية!", reply_markup=get_driver_markup())
            elif action in ["حذف", "🟥"]:
                save_data(data)
                bot.send_message(message.chat.id, f"🟥 تم حذف الرحلة رقم {idx + 1} مباشرة دون إضافتها للأرباح.", reply_markup=get_driver_markup())
            else:
                bot.send_message(message.chat.id, "❌ إجراء غير معروف. استخدم `انهاء [الرقم]` أو `حذف [الرقم]`")
                trips.insert(idx, trip) # اعادة الرحلة في حال خطأ بالأمر
                return
            user_states[message.chat.id] = "logged_in"
        else:
            bot.send_message(message.chat.id, "❌ رقم الرحلة غير موجود في القائمة.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ في تنفيذ الطلب. تأكد من الكتابة بشكل صحيح (مثال: `انهاء 1`).")

@bot.message_handler(func=lambda message: message.text == "💰 الأرباح اليومية")
def show_daily_earnings(message):
    if user_states.get(message.chat.id) != "logged_in":
        bot.send_message(message.chat.id, "الرجاء تسجيل الدخول أولاً.")
        return
        
    data = load_data()
    earnings = data.get("earnings", {})
    if not earnings:
        bot.send_message(message.chat.id, "لا توجد أرباح مسجلة بعد.", reply_markup=get_driver_markup())
        return
    
    text = "💰 تفاصيل الأرباح اليومية:\n"
    for idx, (date, amount) in enumerate(earnings.items(), 1):
        text += f"{idx}. 📅 يوم {date} ⟵ المجموع: {amount} DA\n"
        
    text += "\nللحذف، اكتب في المحادثة `حذف يوم [الرقم]` (مثال: `حذف يوم 1`) أو اضغط على الأزرار الثابتة بالأسفل."
    bot.send_message(message.chat.id, text, reply_markup=get_driver_markup())
    user_states[message.chat.id] = "managing_daily_earnings"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "managing_daily_earnings" and message.text.startswith("حذف يوم"))
def delete_daily_earning(message):
    try:
        part = message.text.replace("حذف يوم", "").strip()
        idx = int(part) - 1
        
        data = load_data()
        earnings_keys = list(data.get("earnings", {}).keys())
        
        if 0 <= idx < len(earnings_keys):
            target_date = earnings_keys[idx]
            data["earnings"].pop(target_date, None)
            save_data(data)
            bot.send_message(message.chat.id, f"✅ تم حذف أرباح يوم {target_date} بنجاح.", reply_markup=get_driver_markup())
        else:
            bot.send_message(message.chat.id, "❌ رقم اليوم غير صحيح.", reply_markup=get_driver_markup())
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ. اكتب الأمر هكذا: `حذف يوم 1`", reply_markup=get_driver_markup())
        
    user_states[message.chat.id] = "logged_in"

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

# إعداد سيرفر الويب لاستمرار عمل البوت على Render
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

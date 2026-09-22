from flask import Flask
from threading import Thread
import os
import telebot
from telebot import types
import json
import calendar
import requests
import base64

# خادم الويب الوهمي لترضى منصة Render (Web Service)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# إعدادات بوت تيليجرام
TOKEN = '8362647244:AAES_D9iqy-X-Tc0_FlcRh8nSdmmjg5_JLM'
bot = telebot.TeleBot(TOKEN)

# إعدادات الاتصال بـ GitHub لحفظ البيانات بشكل دائم
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO')
DATA_FILE = 'driver_data.json'

def load_data():
    if GITHUB_TOKEN and GITHUB_REPO:
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                file_info = response.json()
                file_content = base64.b64decode(file_info['content']).decode('utf-8')
                return json.loads(file_content)
        except Exception as e:
            print(f"Error loading from GitHub: {e}")
            
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
            
    return {'logged_in': False, 'trips': []}

def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(driver_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving local data: {e}")

    if GITHUB_TOKEN and GITHUB_REPO:
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_FILE}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            
            get_resp = requests.get(url, headers=headers)
            sha = get_resp.json().get('sha') if get_resp.status_code == 200 else None
            
            json_str = json.dumps(driver_data, ensure_ascii=False, indent=4)
            encoded_content = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            
            data_payload = {
                "message": "Update driver data automatically",
                "content": encoded_content,
            }
            if sha:
                data_payload["sha"] = sha
                
            requests.put(url, headers=headers, json=data_payload)
        except Exception as e:
            print(f"Error saving to GitHub: {e}")

driver_data = load_data()
user_states = {}
temp_driver_trip = {}

distance_table = {
    "اوريسيا": 15,
    "عين أرنات": 12,
    "العلمة": 28,
    "عين ولمان": 35,
    "بوعنداس": 50,
    "العامرة": 10,
    "سطيف": 0
}

POPULAR_PLACES = ["سطيف", "العلمة", "اوريسيا", "عين ولمان", "بوعنداس"]

def calculate_price(d):
    if d < 2: return 200
    elif d < 4: return 250
    elif d < 6: return 300
    elif d < 8: return 350
    elif d < 10: return 400
    elif d < 12: return 450
    elif d < 14: return 500
    elif d < 16: return 550
    elif d < 18: return 600
    elif d < 20: return 650
    elif d < 22: return 700
    elif d < 24: return 750
    elif d < 26: return 800
    elif d < 30: return 900
    elif d < 34: return 1000
    elif d < 36: return 1100
    else:
        return 1100 + int((d - 36) / 2 * 0.99) * 100

def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_customer = types.KeyboardButton('👤 واجهة الزبون')
    btn_driver = types.KeyboardButton('🚚 واجهة الناقل')
    markup.add(btn_customer, btn_driver)
    
    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت ترانسبورتر سطيف لنقل البضائع.\n"
        "الرجاء اختيار الواجهة للبدء:",
        reply_markup=markup
    )

@bot.message_handler(commands=['start'])
def command_start(message):
    send_welcome(message)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    global driver_data
    chat_id = message.chat.id
    text = message.text

    if text in ['/start', 'بداية', 'البدء', 'مرحباً', 'Hi', 'Hello']:
        send_welcome(message)
        return

    if text == '👤 واجهة الزبون':
        user_states[chat_id] = 'waiting_for_destination'
        bot.send_message(
            chat_id,
            "مكان الانطلاق ثابت: **سطيف**.\n"
            "الوجهة: كتابة مكان الوصول (مثال: اوريسيا، العلمة...):",
            parse_mode="Markdown"
        )
        
    elif user_states.get(chat_id) == 'waiting_for_destination':
        destination = text.strip()
        if destination in distance_table:
            distance = distance_table[destination]
            price = calculate_price(distance)
            user_states[chat_id] = None
            
            bot.send_message(
                chat_id,
                f"📍 **نتيجة الحساب للزبون:**\n"
                f"• الانطلاق: سطيف\n"
                f"• الوصول: {destination}\n"
                f"• المسافة: {distance} كم\n"
                f"• المقدر: **{price} DA**",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(chat_id, "❌ الوجهة غير صالحة! حاول مجدداً بكتابة وجهة صحيحة.")

    elif text == '🚚 واجهة الناقل':
        user_states[chat_id] = 'waiting_for_password'
        bot.send_message(chat_id, "🔒 لوحة الناقل محمية.\nالرجاء إدخال كلمة المرور للوصول:")
        
    elif user_states.get(chat_id) == 'waiting_for_password':
        if text.strip() == '010203':
            user_states[chat_id] = None
            driver_data = load_data()
            driver_data['logged_in'] = True
            save_data()
            show_driver_menu(chat_id)
        else:
            bot.send_message(chat_id, "❌ كلمة المرور غير صحيحة، حاول مجدداً.")

    elif text == '🔄 تصفير الأرباح اليومية':
        if not driver_data['logged_in']: return
        user_states[chat_id] = 'confirm_reset_daily'
        bot.send_message(chat_id, "⚠️ **تحذير:** تصفير الأرباح اليومية يتطلب إدخال كلمة المرور:", parse_mode="Markdown")

    elif user_states.get(chat_id) == 'confirm_reset_daily':
        if text.strip() == '010203':
            driver_data['trips'] = [t for t in driver_data['trips'] if t['status'] != 'منتهية']
            save_data()
            user_states[chat_id] = None
            bot.send_message(chat_id, "✅ تم تصفير الأرباح اليومية بنجاح.")
            show_driver_menu(chat_id)
        else:
            bot.send_message(chat_id, "❌ كلمة المرور غير صحيحة. تم إلغاء التصفير.")
            user_states[chat_id] = None
            show_driver_menu(chat_id)

    elif text == '🔄 تصفير الأرباح الشهرية':
        if not driver_data['logged_in']: return
        user_states[chat_id] = 'confirm_reset_monthly'
        bot.send_message(chat_id, "⚠️ **تحذير:** تصفير الأرباح الشهرية يتطلب إدخال كلمة المرور:", parse_mode="Markdown")

    elif user_states.get(chat_id) == 'confirm_reset_monthly':
        if text.strip() == '010203':
            driver_data['trips'] = [t for t in driver_data['trips'] if t['status'] != 'منتهية']
            save_data()
            user_states[chat_id] = None
            bot.send_message(chat_id, "✅ تم تصفير الأرباح الشهرية بنجاح.")
            show_driver_menu(chat_id)
        else:
            bot.send_message(chat_id, "❌ كلمة المرور غير صحيحة. تم إلغاء التصفير.")
            user_states[chat_id] = None
            show_driver_menu(chat_id)

    elif text == '➕ إنشاء رحلة جديدة':
        if not driver_data['logged_in']:
            bot.send_message(chat_id, "⚠️ يجب تسجيل الدخول أولاً.")
            return
        temp_driver_trip[chat_id] = {}
        prompt_place_selection(chat_id, 'origin', "📍 **اختر مكان الانطلاق:**")

    elif user_states.get(chat_id) == 'custom_origin_input':
        temp_driver_trip[chat_id]['origin'] = text.strip()
        prompt_place_selection(chat_id, 'dest', "🏁 **اختر مكان الوصول (الوجهة):**")

    elif user_states.get(chat_id) == 'custom_dest_input':
        destination = text.strip()
        temp_driver_trip[chat_id]['destination'] = destination
        ask_for_distance(chat_id, destination)

    elif user_states.get(chat_id) == 'entering_custom_distance':
        try:
            distance = float(text.strip())
            temp_driver_trip[chat_id]['distance'] = distance
            prompt_year_selection(chat_id)
        except ValueError:
            bot.send_message(chat_id, "❌ الرجاء إدخال رقم صحيح للمسافة.")

    elif text == '📋 الرحلات المتوفرة':
        driver_data = load_data()
        active_trips = [t for t in driver_data['trips'] if t['status'] == 'غير منتهية']
        if not active_trips:
            bot.send_message(chat_id, "ℹ️ لا توجد رحلات غير منتهية حالياً.")
        else:
            markup = types.InlineKeyboardMarkup()
            for trip in active_trips:
                markup.add(
                    types.InlineKeyboardButton(f"🏁 إنهاء (#{trip['id']}: {trip['origin']}➔{trip['destination']} - {trip['price']}DA)", callback_data=f"finish_{trip['id']}"),
                    types.InlineKeyboardButton(f"❌ حذف (#{trip['id']})", callback_data=f"delete_{trip['id']}")
                )
            bot.send_message(chat_id, "📦 **الرحلات غير المنتهية:**", reply_markup=markup, parse_mode="Markdown")

    elif text == '📊 الأرباح اليومية':
        driver_data = load_data()
        finished_trips = [t for t in driver_data['trips'] if t['status'] == 'منتهية']
        if not finished_trips:
            bot.send_message(chat_id, "ℹ️ لا توجد أرباح مسجلة من رحلات منتهية بعد.")
        else:
            daily_totals = {}
            for t in finished_trips:
                day = t['date']
                if day not in daily_totals:
                    daily_totals[day] = []
                daily_totals[day].append(t)
            
            sorted_days = sorted(daily_totals.keys())
            
            response_text = "📊 **تفاصيل الأرباح اليومية (ترتيب زمني):**\n\n"
            for day in sorted_days:
                trips = daily_totals[day]
                day_total = sum(trip['price'] for trip in trips)
                response_text += f"📅 **اليوم:** {day}\n"
                response_text += f"💰 **المجموع اليومي:** {day_total} DA\n"
                response_text += "🚗 **تفاصيل الرحلات:**\n"
                for index, trip in enumerate(trips, 1):
                    response_text += f"  {index}. من {trip['origin']} إلى {trip['destination']} | المسافة: {trip['distance']} كم | السعر: {trip['price']} DA\n"
                response_text += "\n" + "─"*20 + "\n\n"
            bot.send_message(chat_id, response_text, parse_mode="Markdown")

    elif text == '📈 الأرباح الشهرية':
        driver_data = load_data()
        finished_trips = [t for t in driver_data['trips'] if t['status'] == 'منتهية']
        if not finished_trips:
            bot.send_message(chat_id, "ℹ️ لا توجد أرباح مسجلة للشهور بعد.")
        else:
            monthly_data = {}
            for t in finished_trips:
                month_key = t['date'][:7]
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'total': 0, 'days': {}}
                
                monthly_data[month_key]['total'] += t['price']
                day = t['date']
                monthly_data[month_key]['days'][day] = monthly_data[month_key]['days'].get(day, 0) + t['price']

            sorted_months = sorted(monthly_data.keys())

            response_text = "📈 **ملخص الأرباح الشهرية (ترتيب زمني):**\n\n"
            for m_key in sorted_months:
                m_val = monthly_data[m_key]
                response_text += f"🗓️ **شهر ({m_key}):**\n"
                response_text += f"💰 **مجموع أرباح الشهر:** **{m_val['total']} DA**\n"
                response_text += "📅 **التفاصيل حسب الأيام:**\n"
                sorted_days_in_month = sorted(m_val['days'].keys())
                for day in sorted_days_in_month:
                    d_total = m_val['days'][day]
                    response_text += f"  • يوم {day}: {d_total} DA\n"
                response_text += "\n" + "═"*20 + "\n\n"
            
            bot.send_message(chat_id, response_text, parse_mode="Markdown")

    elif text == '💰 الأرباح السنوية':
        driver_data = load_data()
        finished_trips = [t for t in driver_data['trips'] if t['status'] == 'منتهية']
        if not finished_trips:
            bot.send_message(chat_id, "ℹ️ لا توجد أرباح مسجلة للسنوات بعد.")
        else:
            yearly_data = {}
            for t in finished_trips:
                year_key = t['date'][:4]
                yearly_data[year_key] = yearly_data.get(year_key, 0) + t['price']

            sorted_years = sorted(yearly_data.keys())

            response_text = "💰 **ملخص الأرباح السنوية (ترتيب تصاعدي):**\n\n"
            for y_key in sorted_years:
                y_total = yearly_data[y_key]
                response_text += f"📅 سنة **{y_key}**: **{y_total} DA**\n"
            
            bot.send_message(chat_id, response_text, parse_mode="Markdown")

    elif text == 'الرئيسية':
        user_states[chat_id] = None
        show_driver_menu(chat_id) if driver_data.get('logged_in') else send_welcome(message)

    else:
        bot.send_message(chat_id, "⚠️ الرجاء اختيار أحد الأزرار الموجودة في الأسفل.")

def prompt_place_selection(chat_id, place_type, title_text):
    if place_type == 'origin':
        user_states[chat_id] = 'selecting_origin'
    else:
        user_states[chat_id] = 'selecting_dest'
        
    markup = types.InlineKeyboardMarkup()
    for place in POPULAR_PLACES:
        markup.add(types.InlineKeyboardButton(place, callback_data=f"place_{place_type}_{place}"))
    markup.add(types.InlineKeyboardButton("✏️ مكان آخر (كتابة يدوية)", callback_data=f"place_{place_type}_custom"))
    
    bot.send_message(chat_id, title_text, reply_markup=markup, parse_mode="Markdown")

def ask_for_distance(chat_id, destination):
    suggested_distance = distance_table.get(destination)
    if suggested_distance is not None and suggested_distance > 0:
        user_states[chat_id] = 'confirming_suggested_distance'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"✅ نعم، اعتمد ({suggested_distance} كم)", callback_data=f"dist_accept_{suggested_distance}"))
        markup.add(types.InlineKeyboardButton("✏️ لا، كتابة مسافة أخرى", callback_data="dist_custom"))
        bot.send_message(chat_id, f"📏 المسافة المقدرة لهذه الوجهة من الجدول هي **{suggested_distance} كم**.\nهل تريد اعتمادها أم إدخال مسافة أخرى؟", reply_markup=markup, parse_mode="Markdown")
    else:
        user_states[chat_id] = 'entering_custom_distance'
        bot.send_message(chat_id, "📏 الرجاء إدخال **المسافة (بالكيلومتر)** يدوياً:")

def prompt_year_selection(chat_id):
    user_states[chat_id] = 'selecting_year'
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("2025", callback_data="year_2025"),
        types.InlineKeyboardButton("2026", callback_data="year_2026"),
        types.InlineKeyboardButton("2027", callback_data="year_2027")
    )
    bot.send_message(chat_id, "📅 **اختر سنة الانطلاق:**", reply_markup=markup, parse_mode="Markdown")

def prompt_month_selection(chat_id, year):
    user_states[chat_id] = 'selecting_month'
    temp_driver_trip[chat_id]['year'] = year
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("جانفي (01)", callback_data="month_01"),
        types.InlineKeyboardButton("فيفري (02)", callback_data="month_02"),
        types.InlineKeyboardButton("مارس (03)", callback_data="month_03"),
        types.InlineKeyboardButton("أفريل (04)", callback_data="month_04")
    )
    markup.add(
        types.InlineKeyboardButton("ماي (05)", callback_data="month_05"),
        types.InlineKeyboardButton("جوان (06)", callback_data="month_06"),
        types.InlineKeyboardButton("جويلية (07)", callback_data="month_07"),
        types.InlineKeyboardButton("أوت (08)", callback_data="month_08")
    )
    markup.add(
        types.InlineKeyboardButton("سبتمبر (09)", callback_data="month_09"),
        types.InlineKeyboardButton("أكتوبر (10)", callback_data="month_10"),
        types.InlineKeyboardButton("نوفمبر (11)", callback_data="month_11"),
        types.InlineKeyboardButton("ديسمبر (12)", callback_data="month_12")
    )
    bot.send_message(chat_id, f"📅 **اختر شهر الانطلاق (السنة: {year}):**", reply_markup=markup, parse_mode="Markdown")

def prompt_day_selection(chat_id, month):
    user_states[chat_id] = 'selecting_day'
    temp_driver_trip[chat_id]['month'] = month
    year = int(temp_driver_trip[chat_id]['year'])
    month_int = int(month)
    
    if month_int == 2:
        last_day = 29
    else:
        _, last_day = calendar.monthrange(year, month_int)
    
    markup = types.InlineKeyboardMarkup(row_width=7)
    day_buttons = [types.InlineKeyboardButton(str(day), callback_data=f"day_{str(day).zfill(2)}") for day in range(1, last_day + 1)]
    markup.add(*day_buttons)
    bot.send_message(chat_id, f"📅 **اختر يوم الانطلاق (من 1 إلى {last_day}):**", reply_markup=markup, parse_mode="Markdown")

def prompt_period_selection(chat_id, day):
    user_states[chat_id] = 'selecting_period'
    temp_driver_trip[chat_id]['day'] = day
    full_date = f"{temp_driver_trip[chat_id]['year']}-{temp_driver_trip[chat_id]['month']}-{day}"
    temp_driver_trip[chat_id]['date'] = full_date
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🌅 صباحاً (AM)", callback_data="period_AM"),
        types.InlineKeyboardButton("🌇 مساءً (PM)", callback_data="period_PM")
    )
    bot.send_message(chat_id, "⏰ **اختر الفترة أولاً:**", reply_markup=markup, parse_mode="Markdown")

def prompt_hour_selection(chat_id, period):
    user_states[chat_id] = 'selecting_hour'
    temp_driver_trip[chat_id]['period'] = period
    
    markup = types.InlineKeyboardMarkup(row_width=4)
    hour_buttons = [types.InlineKeyboardButton(f"{h:02d}", callback_data=f"hour_{h:02d}") for h in range(1, 13)]
    markup.add(*hour_buttons)
    bot.send_message(chat_id, f"⏰ **اختر الساعة (فترة {period}):**", reply_markup=markup, parse_mode="Markdown")

def prompt_minute_selection(chat_id, hour):
    user_states[chat_id] = 'selecting_minute'
    temp_driver_trip[chat_id]['hour'] = hour
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    minutes = ["00", "10", "20", "30", "40", "50"]
    min_buttons = [types.InlineKeyboardButton(m, callback_data=f"min_{m}") for m in minutes]
    markup.add(*min_buttons)
    bot.send_message(chat_id, "⏱️ **اختر الدقائق:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global driver_data
    chat_id = call.message.chat.id
    data = call.data
    
    if data.startswith('place_'):
        parts = data.split('_')
        place_type = parts[1]
        place_val = parts[2]
        
        if place_val == 'custom':
            if place_type == 'origin':
                user_states[chat_id] = 'custom_origin_input'
                bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="✏️ يرجى كتابة مكان الانطلاق يدوياً:")
            else:
                user_states[chat_id] = 'custom_dest_input'
                bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="✏️ يرجى كتابة مكان الوصول يدوياً:")
        else:
            if place_type == 'origin':
                temp_driver_trip[chat_id] = {'origin': place_val}
                bot.answer_callback_query(call.id, f"تم اختيار الانطلاق: {place_val}")
                bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"✅ مكان الانطلاق: {place_val}")
                prompt_place_selection(chat_id, 'dest', "🏁 **اختر مكان الوصول (الوجهة):**")
            else:
                destination = place_val
                temp_driver_trip[chat_id]['destination'] = destination
                bot.answer_callback_query(call.id, f"تم اختيار الوصول: {destination}")
                bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"✅ مكان الوصول: {destination}")
                ask_for_distance(chat_id, destination)

    elif data.startswith('dist_accept_'):
        dist = float(data.split('_')[2])
        temp_driver_trip[chat_id]['distance'] = dist
        bot.answer_callback_query(call.id, f"تم اعتماد المسافة: {dist} كم")
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"✅ المسافة المعتمدة: {dist} كم")
        prompt_year_selection(chat_id)
        
    elif data == 'dist_custom':
        user_states[chat_id] = 'entering_custom_distance'
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="✏️ الرجاء إدخال **المسافة (بالكيلومتر)** يدوياً في رسالة:")

    elif data.startswith('year_'):
        year = data.split('_')[1]
        bot.answer_callback_query(call.id, f"السنة: {year}")
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"✅ السنة المختارة: {year}")
        prompt_month_selection(chat_id, year)

    elif data.startswith('month_'):
        month = data.split('_')[1]
        bot.answer_callback_query(call.id, f"الشهر: {month}")
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"✅ الشهر المختار: {month}")
        prompt_day_selection(chat_id, month)

    elif data.startswith('day_'):
        day = data.split('_')[1]
        bot.answer_callback_query(call.id, f"اليوم: {day}")
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"✅ اليوم المختار: {day}")
        prompt_period_selection(chat_id, day)

    elif data.startswith('period_'):
        period = data.split('_')[1]
        bot.answer_callback_query(call.id, f"الفترة: {period}")
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"✅ الفترة المختارة: {period}")
        prompt_hour_selection(chat_id, period)

    elif data.startswith('hour_'):
        hour = data.split('_')[1]
        bot.answer_callback_query(call.id, f"الساعة: {hour}")
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"✅ الساعة المختارة: {hour}")
        prompt_minute_selection(chat_id, hour)

    elif data.startswith('min_'):
        minute = data.split('_')[1]
        trip_info = temp_driver_trip.get(chat_id)
        time_str = f"{trip_info['hour']}:{minute} {trip_info['period']}"
        trip_info['time'] = time_str
        
        bot.answer_callback_query(call.id, f"الوقت: {time_str}")
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=f"✅ وقت الانطلاق المختار: {time_str}")
        finalize_trip_creation(chat_id)

    elif data.startswith('finish_') or data.startswith('delete_'):
        driver_data = load_data()
        parts = data.split('_')
        action = parts[0]
        trip_id = int(parts[1])
        
        trip = next((t for t in driver_data['trips'] if t['id'] == trip_id), None)
        if not trip:
            bot.answer_callback_query(call.id, "الرحلة غير موجودة أو تم التعامل معها مسبقاً.")
            return
            
        if action == 'finish':
            trip['status'] = 'منتهية'
            save_data()
            earned = trip['price']
            bot.answer_callback_query(call.id, "تم إنهاء الرحلة بنجاح!")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"✅ **تم إنهاء الرحلة #{trip_id} بنجاح وإضافتها لسجل الأرباح:**\n"
                     f"• المسار: {trip['origin']} ➔ {trip['destination']}\n"
                     f"• المسافة: {trip['distance']} كم\n"
                     f"• الموعد: {trip['date']} على الساعة {trip['time']}\n"
                     f"• المبلغ المضاف: {earned} DA",
                parse_mode="Markdown"
            )
        elif action == 'delete':
            driver_data['trips'].remove(trip)
            save_data()
            bot.answer_callback_query(call.id, "تم حذف الرحلة.")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"🗑️ **تم حذف الرحلة #{trip_id} بنجاح.**",
                parse_mode="Markdown"
            )

def finalize_trip_creation(chat_id):
    global driver_data
    driver_data = load_data()
    trip_info = temp_driver_trip.get(chat_id)
    if not trip_info:
        return
        
    dist = trip_info['distance']
    price = calculate_price(dist)
    
    new_trip = {
        'id': len(driver_data['trips']) + 1,
        'origin': trip_info['origin'],
        'destination': trip_info['destination'],
        'distance': dist,
        'date': trip_info['date'],
        'time': trip_info['time'],
        'price': price,
        'status': 'غير منتهية'
    }
    driver_data['trips'].append(new_trip)
    save_data()
    user_states[chat_id] = None
    
    bot.send_message(
        chat_id,
        f"✅ **تم إنشاء الرحلة بنجاح!**\n"
        f"• رقم الرحلة: #{new_trip['id']}\n"
        f"• المسار: {new_trip['origin']} ➔ {new_trip['destination']}\n"
        f"• المسافة: {new_trip['distance']} كم\n"
        f"• الموعد: يوم {new_trip['date']} على الساعة {new_trip['time']}\n"
        f"• السعر المحدد: **{price} DA**",
        parse_mode="Markdown"
    )
    show_driver_menu(chat_id)

def show_driver_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('➕ إنشاء رحلة جديدة'),
        types.KeyboardButton('📋 الرحلات المتوفرة')
    )
    markup.add(
        types.KeyboardButton('📊 الأرباح اليومية'),
        types.KeyboardButton('📈 الأرباح الشهرية')
    )
    markup.add(
        types.KeyboardButton('💰 الأرباح السنوية'),
        types.KeyboardButton('🔄 تصفير الأرباح اليومية')
    )
    markup.add(
        types.KeyboardButton('🔄 تصفير الأرباح الشهرية'),
        types.KeyboardButton('الرئيسية')
    )
    
    bot.send_message(
        chat_id,
        "🚚 **لوحة تحكم الناقل:**\nالرجاء اختيار إحدى الخدمات:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# إلغاء أي Webhook قديم لتفادي خطأ 409 وتضارب الاتصال بشكل نهائي
try:
    bot.remove_webhook()
except Exception as e:
    print(f"Error removing webhook: {e}")

print("البوت يعمل الآن...")
bot.infinity_polling()

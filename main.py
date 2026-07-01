import sqlite3
import telebot
from telebot import types
import requests

TELEGRAM_TOKEN = "8673445877:AAHqzQrt2tNeOETRTKxJXj7ak4qF9naLSFA"
SMAILPRO_API_KEY = "2e77c6695f94c9784452388e9b9dc3f7463e19e16ed05f4125dc838e058c0798"
ADMIN_ID = 7865006773
ADMIN_USERNAME = "nmqsk001"

PRICE_PER_MAIL = 500
MIN_DEPOSIT = 10000
ITEMS_PER_PAGE = 5  
SMAILPRO_API_URL = "https://sonjj.com"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def init_db():
    conn = sqlite3.connect("smailpro_bot.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        balance INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        amount INTEGER,
                        status TEXT DEFAULT 'PENDING',
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS rented_mails (
                        rent_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        email TEXT,
                        mail_id TEXT,
                        status TEXT DEFAULT 'ACTIVE',
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id, username=""):
    conn = sqlite3.connect("smailpro_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, 0)", (user_id, username))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    conn.close()
    return user

def update_balance(user_id, amount):
    conn = sqlite3.connect("smailpro_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📧 Thuê 1 Mail (500đ)", "📦 Thuê Số Lượng")
    markup.row("💰 Nạp Tiền", "📋 Lịch Sử / Khôi Phục")
    markup.row("👤 Tài Khoản")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = get_user(message.from_user.id, message.from_user.username)
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton("💬 Nhắn Tin Trực Tiếp Với Admin", url=f"https://t.me{ADMIN_USERNAME}"))
    bot.send_message(
        message.chat.id, 
        f"👋 Chào mừng bạn!\n💵 Số dư: {user[2]:,} VNĐ", 
        reply_markup=main_menu()
    )
    bot.send_message(message.chat.id, "📌 Hỗ trợ & Nạp tiền:", reply_markup=inline_markup)

@bot.message_handler(func=lambda message: message.text == "👤 Tài Khoản")
def account_info(message):
    user = get_user(message.from_user.id, message.from_user.username)
    text = f"👤 **TÀI KHOẢN:**\n\n🆔 ID: `{user[0]}`\n🏷️ Username: @{user[1] if user[1] else 'Không có'}\n💵 Số dư: **{user[2]:,} VNĐ**"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💰 Nạp Tiền")
def deposit_request(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💵 10k", callback_data="dep_10000"),
        types.InlineKeyboardButton("💵 20k", callback_data="dep_20000"),
        types.InlineKeyboardButton("💵 50k", callback_data="dep_50000"),
        types.InlineKeyboardButton("💵 100k", callback_data="dep_100000"),
        types.InlineKeyboardButton("💵 200k", callback_data="dep_200000"),
        types.InlineKeyboardButton("✏️ Tự nhập số khác", callback_data="dep_custom")
    )
    bot.send_message(
        message.chat.id, 
        f"💰 **NẠP TIỀN**\n\n🔹 Tối thiểu: {MIN_DEPOSIT:,}đ.\n🔹 Chọn mệnh giá hoặc tự nhập số tiền.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def process_deposit_amount(message):
    try:
        amount = int(message.text)
        if amount < MIN_DEPOSIT:
            bot.send_message(message.chat.id, f"❌ Tối thiểu là {MIN_DEPOSIT:,}đ. Vui lòng thử lại.")
            return
        send_deposit_to_admin(message, message.from_user.id, message.from_user.username, amount)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Vui lòng nhập số hợp lệ.")

def send_deposit_to_admin(message, user_id, username, amount):
    conn = sqlite3.connect("smailpro_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (user_id, amount) VALUES (?, ?)", (user_id, amount))
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()

    qr_url = f"https://vietqr.io{amount}&addInfo=NAP{tx_id}&accountName=NGUYEN%20MANH%20QUYNH"
    caption = f"CN\n\n🏛 Ngân hàng: Techcombank\n🔢 STK: `1097779819`\n👤 Chủ TK: NGUYEN MANH QUYNH\n💵 Số tiền: **{amount:,}đ**\n🔤 Nội dung: **NAP{tx_id}**\n\n⚠️ Quét mã QR hoặc nhập đúng nội dung chuyển khoản."
    
    bot.send_photo(message.chat.id, qr_url, caption=caption, parse_mode="Markdown")

    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Duyệt", callback_data=f"approve_{tx_id}"),
        types.InlineKeyboardButton("❌ Hủy", callback_data=f"reject_{tx_id}")
    )
    bot.send_message(
        ADMIN_ID, 
        f"💰 **YÊU CẦU NẠP TIỀN**\n🆔 Mã GD: {tx_id}\n👤 Người nạp: @{username} (`{user_id}`)\n💵 Số tiền: {amount:,}đ", 
        reply_markup=admin_markup,
        parse_mode="Markdown"
    )

def call_smailpro_api_gmail_premium():
    headers = {"Authorization": f"Bearer {SMAILPRO_API_KEY}", "Accept": "application/json"}
    params = {"domain": "gmail.com", "type": "premium"}
    try:
        response = requests.get(f"{SMAILPRO_API_URL}/get-email", headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {"success": True, "email": data.get("email"), "mail_id": data.get("mail_id")}
        return {"success": False, "error": f"Lỗi HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@bot.message_handler(func=lambda message: message.text == "📧 Thuê 1 Mail (500đ)")
def rent_one_mail(message):
    user = get_user(message.from_user.id, message.from_user.username)
    if user[2] < PRICE_PER_MAIL:
        bot.send_message(message.chat.id, f"❌ Không đủ số dư ({user[2]:,}đ). Giá thuê là {PRICE_PER_MAIL}đ.")
        return

    bot.send_message(message.chat.id, "⏳ Đang khởi tạo Gmail Premium...")
    result = call_smailpro_api_gmail_premium()

    if result["success"]:
        email = result["email"]
        mail_id = result["mail_id"]

        update_balance(message.from_user.id, -PRICE_PER_MAIL)
        
        conn = sqlite3.connect("smailpro_bot.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rented_mails (user_id, email, mail_id) VALUES (?, ?, ?)", (message.from_user.id, email, mail_id))
        rent_id = cursor.lastrowid
        conn.commit()
        conn.close()

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Lấy Mã OTP / Code", callback_data=f"getcode_{rent_id}"))
        bot.send_message(message.chat.id, f"🎉 Thành công!\n📧 **Email:** `{email}`\n💸 Trừ: {PRICE_PER_MAIL}đ", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ Thất bại: {result['error']}.")

@bot.message_handler(func=lambda message: message.text == "📦 Thuê Số Lượng")
def bulk_rent_request(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📦 5 Mail (2.5k)", callback_data="bulk_5"),
        types.InlineKeyboardButton("📦 10 Mail (5k)", callback_data="bulk_10"),
        types.InlineKeyboardButton("📦 20 Mail (10k)", callback_data="bulk_20"),
        types.InlineKeyboardButton("📦 50 Mail (25k)", callback_data="bulk_50"),
        types.InlineKeyboardButton("✏️ Nhập số lượng khác", callback_data="bulk_custom")
    )
    bot.send_message(message.chat.id, "📦 **THUÊ SỐ LƯỢNG**\n🔹 Đơn giá: `500đ / 1 Mail Gmail Premium`", reply_markup=markup, parse_mode="Markdown")

def process_bulk_rent_custom(message):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            bot.send_message(message.chat.id, "❌ Số lượng phải lớn hơn 0.")
            return
        execute_bulk_rent(message, message.from_user.id, message.from_user.username, quantity)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Vui lòng nhập số nguyên hợp lệ.")

def execute_bulk_rent(message, user_id, username, quantity):
    user = get_user(user_id, username)
    total_cost = quantity * PRICE_PER_MAIL
    if user[2] < total_cost:
        bot.send_message(message.chat.id, f"❌ Không đủ số dư! Cần {total_cost:,}đ để thuê {quantity} mail. Hiện có {user[2]:,}đ.")
        return

    bot.send_message(message.chat.id, f"⏳ Đang khởi tạo {quantity} Gmail Premium...")
    success_mails = []

    for _ in range(quantity):
        result = call_smailpro_api_gmail_premium()
        if result["success"]:
            email = result["email"]
            mail_id = result["mail_id"]
            
            conn = sqlite3.connect("smailpro_bot.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO rented_mails (user_id, email, mail_id) VALUES (?, ?, ?)", (user_id, email, mail_id))
            rent_id = cursor.lastrowid
            conn.commit()
            conn.close()
            success_mails.append((rent_id, email))
        else:
            break  

    actual_success = len(success_mails)
    if actual_success > 0:
        actual_cost = actual_success * PRICE_PER_MAIL
        update_balance(user_id, -actual_cost)
        
        result_text = f"🎉 **Thành công ({actual_success}/{quantity}) Mail!**\n💸 Trừ: {actual_cost:,}đ\n\nDanh sách:\n"
        markup = types.InlineKeyboardMarkup()
        for rent_id, email in success_mails:
            result_text += f"🔹 ID {rent_id}: `{email}`\n"
            markup.add(types.InlineKeyboardButton(f"Check Code ID {rent_id}", callback_data=f"getcode_{rent_id}"))
        bot.send_message(message.chat.id, result_text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ Lỗi hệ thống API, không thể khởi tạo mail.")

@bot.message_handler(func=lambda message: message.text == "📋 Lịch Sử / Khôi Phục")
def rent_history(message):
    send_history_page(message.chat.id, message.from_user.id, page=1)

def send_history_page(chat_id, user_id, page=1, edit_message_id=None):
    conn = sqlite3.connect("smailpro_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rented_mails WHERE user_id = ?", (user_id,))
    total_items = cursor.fetchone()[0]
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    if total_items == 0:
        bot.send_message(chat_id, "📭 Chưa có lịch sử thuê mail.")
        conn.close()
        return

    offset = (page - 1) * ITEMS_PER_PAGE
    cursor.execute("SELECT rent_id, email FROM rented_mails WHERE user_id = ? ORDER BY rent_id DESC LIMIT ? OFFSET ?", (user_id, ITEMS_PER_PAGE, offset))
    rows = cursor.fetchall()
    conn.close()

    markup = types.InlineKeyboardMarkup()
    text = f"📋 **LỊCH SỬ THUÊ (Trang {page}/{total_pages})**\n\n"
    for row in rows:
        text += f"🔹 ID {row[0]}: `{row[1]}`\n"
        markup.add(types.InlineKeyboardButton(f"📧 Check Mail ID: {row[0]}", callback_data=f"getcode_{row[0]}"))

    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton("◀️ Trước", callback_data=f"page_{page-1}"))
    nav_buttons.append(types.InlineKeyboardButton("❓ Hướng dẫn", callback_data="help_history"))
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton("Sau ▶️", callback_data=f"page_{page+1}"))
    markup.row(*nav_buttons)

    if edit_message_id:
        try:
            bot.edit_message_text(text, chat_id, edit_message_id, reply_markup=markup, parse_mode="Markdown")
        except Exception:
            pass
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith("page_"):
        next_page = int(call.data.split("_")[1])
        send_history_page(call.message.chat.id, call.from_user.id, page=next_page, edit_message_id=call.message.message_id)
        bot.answer_callback_query(call.id)

    elif call.data == "help_history":
        help_text = "📖 HƯỚNG DẪN KHÔI PHỤC MAIL:\n\n1. Chọn nút 'Check Mail ID' cần kiểm tra.\n2. Hệ thống quét hòm thư để lấy OTP mới nhất.\n3. Khôi phục hoàn toàn miễn phí."
        bot.answer_callback_query(call.id, text=help_text, show_alert=True)

    elif call.data.startswith("dep_"):
        amount_type = call.data.split("_")[1]
        if amount_type == "custom":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id, f"💵 Nhập số tiền muốn nạp (Tối thiểu {MIN_DEPOSIT:,}đ):")
            bot.register_next_step_handler(msg, process_deposit_amount)
        else:
            bot.answer_callback_query(call.id)
            send_deposit_to_admin(call.message, call.from_user.id, call.from_user.username, int(amount_type))

    elif call.data.startswith("bulk_"):
        bulk_type = call.data.split("_")[1]
        if bulk_type == "custom":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id, "✏️ Nhập số lượng hòm thư muốn mua:")
            bot.register_next_step_handler(msg, process_bulk_rent_custom)
        else:
            bot.answer_callback_query(call.id)
            execute_bulk_rent(call.message, call.from_user.id, call.from_user.username, int(bulk_type))

    elif call.data.startswith("approve_") or call.data.startswith("reject_"):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Lệnh chỉ dành cho Admin!", show_alert=True)
            return

        action, tx_id = call.data.split("_")
        conn = sqlite3.connect("smailpro_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, amount, status FROM transactions WHERE tx_id = ?", (tx_id,))
        tx = cursor.fetchone()

        if not tx or tx[2] != 'PENDING':
            bot.answer_callback_query(call.id, "⚠️ Lệnh đã xử lý trước đó.")
            conn.close()
            return

        user_id, amount, _ = tx
        if action == "approve":
            cursor.execute("UPDATE transactions SET status = 'APPROVED' WHERE tx_id = ?", (tx_id,))
            conn.commit()
            update_balance(user_id, amount)
            bot.edit_message_text(f"✅ Đã duyệt cộng {amount:,}đ cho giao dịch {tx_id}.", call.message.chat.id, call.message.message_id)
            bot.send_message(user_id, f"🎉 Đã được cộng {amount:,}đ vào tài khoản thành công!")
        else:
            cursor.execute("UPDATE transactions SET status = 'REJECTED' WHERE tx_id = ?", (tx_id,))
            conn.commit()
            bot.edit_message_text(f"❌ Đã hủy lệnh giao dịch {tx_id}.", call.message.chat.id, call.message.message_id)
            bot.send_message(user_id, f"❌ Lệnh nạp tiền mã {tx_id} đã bị từ chối.")
        conn.close()

    elif call.data.startswith("getcode_"):
        rent_id = call.data.split("_")[1]
        conn = sqlite3.connect("smailpro_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT mail_id, email FROM rented_mails WHERE rent_id = ?", (rent_id,))
        mail_data = cursor.fetchone()
        conn.close()

        if mail_data:
            mail_id, email = mail_data
            bot.answer_callback_query(call.id, text=f"⏳ Đang check {email}...")
            
            headers = {"Authorization": f"Bearer {SMAILPRO_API_KEY}"}
            try:
                response = requests.get(f"{SMAILPRO_API_URL}/get-messages?mail_id={mail_id}", headers=headers, timeout=10)
                messages = response.json()
                
                if response.status_code == 200 and messages:
                    latest_msg = messages[0] if isinstance(messages, list) else messages
                    subject = latest_msg.get("subject", "Không tiêu đề")
                    body = latest_msg.get("body", "Trống")
                    bot.send_message(call.message.chat.id, f"📩 **HỘP THƯ ĐẾN:** `{email}`\n📌 **Tiêu đề:** {subject}\n📝 **Nội dung:**\n\n`{body}`", parse_mode="Markdown")
                else:
                    bot.send_message(call.message.chat.id, f"📭 Hòm thư `{email}` hiện chưa có thư mới. Thử lại sau ít giây.")
            except Exception:
                bot.send_message(call.message.chat.id, "❌ Lỗi kết nối mạng khi tải tin nhắn.")
        else:
            bot.answer_callback_query(call.id, text="❌ Không tồn tại dữ liệu mail!", show_alert=True)

bot.polling(none_stop=True)

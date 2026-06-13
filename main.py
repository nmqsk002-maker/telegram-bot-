import os
import threading
import telebot
from flask import Flask, request

# LẤY THÔNG SỐ BẢO MẬT TỪ CẤU HÌNH RENDER
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

DATA_FILE = "user_data_v2.json"
CHEAT_FILE = "anti_cheat.json"

def load_json(filename):
    import json
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def save_json(filename, data):
    import json
    with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

user_db = load_json(DATA_FILE)
cheat_db = load_json(CHEAT_FILE)

@app.route('/verify/<uid>/<ref_id>')
def verify_user(uid, ref_id):
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown Device')
    device_fingerprint = str(hash(user_agent))
    
    is_cheat = False
    reason = ""
    
    if user_ip in cheat_db and cheat_db[user_ip] != uid:
        is_cheat = True
        reason = f"Trùng địa chỉ IP mạng với tài khoản ID: {cheat_db[user_ip]}"
    elif device_fingerprint in cheat_db and cheat_db[device_fingerprint] != uid:
        is_cheat = True
        reason = f"Trùng thiết bị máy/trình duyệt với tài khoản ID: {cheat_db[device_fingerprint]}"
        
    if is_cheat:
        try:
            bot.send_message(int(ADMIN_ID), f"⚠️ **CẢNH BÁO GIAN LẬN (CHEAT):**\nUser ID `{uid}` vừa kích hoạt link của Người mời `{ref_id}`.\n❌ **Lý do chặn:** {reason}\n🌐 IP: `{user_ip}`", parse_mode='Markdown')
            bot.send_message(int(uid), "❌ Hệ thống phát hiện thiết bị hoặc mạng của bạn đã tham gia chương trình này trước đây.")
        except: pass
        return "<h3>❌ Xác thực thất bại: Phát hiện trùng lặp thiết bị hoặc địa chỉ IP mạng (Gian lận)!</h3>", 400

    cheat_db[user_ip] = uid
    cheat_db[device_fingerprint] = uid
    save_json(CHEAT_FILE, cheat_db)
    
    if uid not in user_db:
        user_db[uid] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": ref_id}
    
    if ref_id in user_db and ref_id != uid:
        user_db[ref_id]["balance"] += 1000
        save_json(DATA_FILE, user_db)
        try:
            bot.send_message(int(ref_id), f"🎉 Bạn được cộng **+1.000đ** vì đã mời thành công thành viên mới thực tế!\n🌐 IP người mới: `{user_ip}`", parse_mode='Markdown')
        except: pass

    try:
        bot.send_message(int(uid), "✅ Xác thực thành công! Hãy gõ lệnh /vi để bắt đầu sử dụng bot.")
    except: pass
    return "<h3>✅ Xác thực thành công! Bạn có thể quay lại Telegram được rồi.</h3>", 200

@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = str(message.from_user.id)
    uname = message.from_user.first_name
    args = message.text.split()
    
    if uid not in user_db:
        user_db[uid] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": None}
        save_json(DATA_FILE, user_db)
        
    if len(args) > 1 and user_db[uid]["invited_by"] is None:
        ref_id = args[1]
        if ref_id != uid and ref_id in user_db:
            server_url = "https://THAY_LINK_WEB_CỦA_BẠN_VÀO_ĐÂY.onrender.com" 
            verify_link = f"{server_url}/verify/{uid}/{ref_id}"
            
            msg = (
                f"👋 Chào mừng **{uname}**!\n\n"
                f"🔒 Để tránh tài khoản ảo gian lận, vui lòng bấm vào liên kết này để hoàn tất xác thực thiết bị máy thực tế:\n{verify_link}\n\n"
                f"_(Sau khi bạn bấm xác thực xong, người mời bạn mới nhận được tiền)_"
            )
            bot.reply_to(message, msg)
            return

    welcome_text = f"👋 Xin chào **{uname}**!\n\n👉 /link : Lấy Link mời độc quyền\n👉 /vi : Kiểm tra Số dư & Ngân hàng\n👉 /nganhang [Tên NH + Số TK] : Liên kết ngân hàng\n👉 /rut : Yêu cầu rút tiền"
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['link'])
def get_invite_link(message):
    bot_info = bot.get_me()
    invite_url = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    bot.reply_to(message, f"🔗 **LINK MỜI CỦA BẠN:**\n`{invite_url}`", parse_mode='Markdown')

@bot.message_handler(commands=['vi'])
def check_wallet(message):
    uid = str(message.from_user.id)
    balance = user_db[uid]["balance"] if uid in user_db else 0
    bank = user_db[uid]["bank"] if uid in user_db else "Chưa liên kết"
    bot.reply_to(message, f"💳 **VÍ CỦA BẠN**\n💰 Số dư: {balance:,}đ\n🏦 Ngân hàng: {bank}")

@bot.message_handler(commands=['nganhang'])
def link_bank(message):
    uid = str(message.from_user.id)
    bank_info = message.text.replace('/nganhang', '').strip()
    if not bank_info:
        bot.reply_to(message, "⚠️ Sai cú pháp! Gõ ví dụ: `/nganhang MB Bank - 0987654321`")
        return
    user_db[uid]["bank"] = bank_info
    save_json(DATA_FILE, user_db)
    bot.reply_to(message, f"✅ Đã lưu ngân hàng: {bank_info}")

@bot.message_handler(commands=['rut'])
def request_withdraw(message):
    uid = str(message.from_user.id)
    if uid not in user_db or user_db[uid]["balance"] < 10000:
        bot.reply_to(message, "❌ Bạn không đủ số dư tối thiểu (10.000đ) để rút.")
        return
    if user_db[uid]["bank"] == "Chưa liên kết":
        bot.reply_to(message, "⚠️ Hãy gõ lệnh `/nganhang` trước khi rút tiền.")
        return
    
    amount = user_db[uid]["balance"]
    bank = user_db[uid]["bank"]
    user_db[uid]["balance"] = 0
    save_json(DATA_FILE, user_db)
    bot.reply_to(message, f"💸 Đã gửi lệnh rút {amount:,}đ lên hệ thống admin.")
    try:
        bot.send_message(int(ADMIN_ID), f"🚨 **YÊU CẦU RÚT TIỀN:**\n👤 User ID: `{uid}`\n💰 Tiền: {amount:,}đ\n🏦 Tài khoản: {bank}", parse_mode='Markdown')
    except: pass

def run_web():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    threading.Thread(target=run_web).start()
    print("=== SYSTEM ANTI-CHEAT ONLINE... ===")
    bot.infinity_polling()

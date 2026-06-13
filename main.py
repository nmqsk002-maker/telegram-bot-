import os
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# 🔐 CẤU HÌNH BIẾN MÔI TRƯỜNG (LẤY TỪ RENDER)
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

DATA_FILE = "user_data_v3.json"
CHEAT_FILE = "anti_cheat_v3.json"

# ⚙️ CẤU HÌNH THÔNG TIN NHÓM CỦA BẠN (HÃY SỬA 2 DÒNG NÀY THEO ĐÚNG NHÓM CỦA BẠN)
CHAT_GROUP_ID = "-1003898772559"        # Thay bằng ID nhóm của bạn (Có dấu trừ, ví dụ: -100123456789)
LINK_NHOM_CHINH_THUC = "https://t.me/baoappfreekonap"  # Thay bằng link nhóm của bạn

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

# 🌐 TRANG WEB QUÉT THIẾT BỊ MÁY (ĐÃ LOẠI BỎ CHECK IP MẠNG)
@app.route('/verify/<uid>/<ref_id>')
def verify_user(uid, ref_id):
    user_agent = request.headers.get('User-Agent', 'Unknown Device')
    device_fingerprint = str(hash(user_agent)) # Định danh máy bằng thông số thiết bị
    
    # 1. KIỂM TRA THÀNH VIÊN ĐÃ THỰC SỰ VÀO NHÓM CHƯA
    try:
        member_status = bot.get_chat_member(chat_id=int(CHAT_GROUP_ID), user_id=int(uid)).status
        if member_status in ['left', 'kicked']:
            return "<h3>❌ Thất bại: Bạn chưa bấm tham gia vào Nhóm chính thức của chúng tôi! Hãy vào nhóm trước rồi bấm lại link này.</h3>", 400
    except Exception as e:
        # Nếu chưa cấu hình chuẩn ID nhóm, tạm thời bỏ qua để tránh lỗi
        pass

    # 2. CHỈ KIỂM TRA TRÙNG THIẾT BỊ MÁY (ANTI-CHEAT DEVICE)
    if device_fingerprint in cheat_db and cheat_db[device_fingerprint] != uid:
        try:
            bot.send_message(int(ADMIN_ID), f"⚠️ **PHÁT HIỆN GIAN LẬN THIẾT BỊ:**\n👤 User ID: `{uid}` cố tình tạo nick ảo.\n❌ **Lý do:** Trùng thiết bị máy/trình duyệt với tài khoản ID cũ: `{cheat_db[device_fingerprint]}`", parse_mode='Markdown')
            bot.send_message(int(uid), "❌ **Xác thực thất bại:** Hệ thống phát hiện thiết bị này đã được sử dụng để nhận thưởng trước đó.")
        except: pass
        return "<h3>❌ Xác thực thất bại: Một thiết bị chỉ được tính thưởng một lần duy nhất!</h3>", 400

    # LƯU THIẾT BỊ VÀO BỘ NHỚ CHỐNG CHEAT
    cheat_db[device_fingerprint] = uid
    save_json(CHEAT_FILE, cheat_db)
    
    # TIẾN HÀNH CỘNG TIỀN NẾU HỢP LỆ
    if uid not in user_db:
        user_db[uid] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": ref_id}
    
    if ref_id in user_db and ref_id != uid:
        user_db[ref_id]["balance"] += 1000
        save_json(DATA_FILE, user_db)
        try:
            bot.send_message(int(ref_id), f"🎉 **Chúc mừng bạn!**\n🎁 Bạn vừa được cộng **+1.000đ** vào ví nhờ mời thành công thành viên thực tế gia nhập nhóm!", parse_mode='Markdown')
        except: pass

    try:
        bot.send_message(int(uid), "✅ **Xác thực thành công!** Bạn đã hoàn tất quy trình. Hãy gõ lệnh /vi để kiểm tra ví cá nhân của mình nhé.")
    except: pass
    return "<h3>✅ Xác thực thành công! Hệ thống ghi nhận bạn là người dùng thật. Hãy quay lại Telegram.</h3>", 200


# 📥 LỆNH /START KHI THÀNH VIÊN NHẤN VÀO LINK MỜI
@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = str(message.from_user.id)
    uname = message.from_user.first_name
    args = message.text.split()
    
    if uid not in user_db:
        user_db[uid] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": None}
        save_json(DATA_FILE, user_db)
        
    # Trường hợp đi qua link mời của người khác
    if len(args) > 1 and user_db[uid]["invited_by"] is None:
        ref_id = args[1]
        if ref_id != uid and ref_id in user_db:
            user_db[uid]["invited_by"] = ref_id
            save_json(DATA_FILE, user_db)
            
            # Tự động lấy tên miền Render từ cấu hình cũ của bạn
            server_url = "https://bot-kiem-tra-ip.onrender.com" 
            verify_link = f"{server_url}/verify/{uid}/{ref_id}"
            
            # THIẾT KẾ NÚT BẤM XỊN SÒ THEO QUY TRÌNH 2 BƯỚC
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("1️⃣ Bước 1: Tham Gia Nhóm Chính Thức 👥", url=LINK_NHOM_CHINH_THUC))
            markup.row(InlineKeyboardButton("2️⃣ Bước 2: Bấm Xác Minh Máy Thật 🔒", url=verify_link))
            
            welcome_invite = (
                f"👋 **Chào mừng {uname} đã đến với ngày hội nhận thưởng!**\n\n"
                f"Để hoàn tất quy trình nhận thưởng và giúp người mời bạn nhận được **1.000đ**, bạn vui lòng thực hiện đúng **2 bước** dưới đây bằng cách bấm vào các nút tương ứng:\n\n"
                f"⚠️ *Lưu ý: Bạn bắt buộc phải vào nhóm và một thiết bị điện thoại chỉ được tính một lần duy nhất.*"
            )
            bot.send_message(message.chat.id, welcome_invite, reply_markup=markup, parse_mode='Markdown')
            return

    # GIAO DIỆN CHÍNH
    show_main_menu(message.chat.id, uname)

def show_main_menu(chat_id, name):
    main_text = (
        f"👑 **HỆ THỐNG KIẾM TIỀN CHÍNH THỨC V2** 👑\n\n"
        f"Chào mừng **{name}** đã quay trở lại! Dưới đây là bảng điều khiển chức năng cá nhân của bạn. Hãy bấm vào các nút menu bên dưới để thao tác nhanh chóng:\n\n"
        f"💰 **Chính sách:** Nhận ngay **1.000đ** cho mỗi thành viên thực tế được bạn mời tham gia vào nhóm qua link độc quyền."
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔗 Lấy Link Mời Kiếm Tiền", callback_data="menu_link"))
    markup.row(InlineKeyboardButton("💳 Kiểm Tra Số Dư Ví", callback_data="menu_vi"), InlineKeyboardButton("🏦 Liên Kết Ngân Hàng", callback_data="menu_nh"))
    markup.row(InlineKeyboardButton("💸 Rút Tiền Về Tài Khoản", callback_data="menu_rut"))
    bot.send_message(chat_id, main_text, reply_markup=markup, parse_mode='Markdown')


# 🕹️ XỬ LÝ SỰ KIỆN KHI NGƯỜI DÙNG BẤM CÁC NÚT MENU NỔI
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    uid = str(call.from_user.id)
    if uid not in user_db:
        user_db[uid] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": None}
    
    if call.data == "menu_link":
        bot_info = bot.get_me()
        invite_url = f"https://t.me/{bot_info.username}?start={uid}"
        text = (
            f"🔗 **LINK MỜI ĐỘC QUYỀN CỦA BẠN:**\n`{invite_url}`\n\n"
            f"📥 **Cách làm:** Bạn đè ngón tay vào link trên để copy, sau đó đem đi chia sẻ lên các hội nhóm. Khi có người bấm vào link, làm theo hướng dẫn vào nhóm + xác minh máy thành công, bạn sẽ nhận được **1.000đ** ngay lập tức!"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        
    elif call.data == "menu_vi":
        balance = user_db[uid]["balance"]
        bank = user_db[uid]["bank"]
        text = (
            f"💳 **THÔNG TIN TÀI KHOẢN VÍ**\n\n"
            f"💰 **Số dư hiện tại:** `{balance:,}đ`\n"
            f"🏦 **Ngân hàng liên kết:** `{bank}`\n\n"
            f"_(Hạn mức rút tiền tối thiểu của hệ thống là 10.000đ)_"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        
    elif call.data == "menu_nh":
        text = (
            f"🏦 **HƯỚNG DẪN LIÊN KẾT NGÂN HÀNG**\n\n"
            f"Vui lòng gõ tin nhắn theo đúng cú pháp ví dụ sau để hệ thống lưu thông tin nhận tiền của bạn:\n\n"
            f"`/nganhang MB Bank - 0333444555 - NGUYEN VAN A`"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        
    elif call.data == "menu_rut":
        if user_db[uid]["balance"] < 10000:
            bot.send_message(call.message.chat.id, "❌ **Rút tiền thất bại:** Số dư trong ví của bạn phải đạt tối thiểu từ **10.000đ** trở lên.")
            return
        if user_db[uid]["bank"] == "Chưa liên kết":
            bot.send_message(call.message.chat.id, "⚠️ **Thông báo:** Bạn chưa liên kết ngân hàng nhận tiền. Hãy bấm nút **Liên Kết Ngân Hàng** trước.")
            return
            
        amount = user_db[uid]["balance"]
        bank = user_db[uid]["bank"]
        user_db[uid]["balance"] = 0
        save_json(DATA_FILE, user_db)
        
        bot.send_message(call.message.chat.id, f"✅ **Gửi lệnh rút tiền thành công!** Hệ thống đã trừ `{amount:,}đ` trong ví của bạn và chuyển tiếp tới lệnh phê duyệt của Admin. Vui lòng chờ tiền về tài khoản ngân hàng.")
        try:
            bot.send_message(int(ADMIN_ID), f"🚨 **YÊU CẦU RÚT TIỀN MỚI:**\n👤 Người rút (ID): `{uid}`\n💰 Số tiền yêu cầu: `{amount:,}đ`\n🏦 Tài khoản nhận: `{bank}`", parse_mode='Markdown')
        except: pass


# 📝 CÚ PHÁP LỆNH DÀNH CHO /NGANHANG
@bot.message_handler(commands=['nganhang'])
def link_bank(message):
    uid = str(message.from_user.id)
    bank_info = message.text.replace('/nganhang', '').strip()
    if not bank_info:
        bot.reply_to(message, "⚠️ **Sai cú pháp!** Vui lòng gõ ví dụ: `/nganhang MB Bank - 0123456789 - NGUYEN VAN A`")
        return
    if uid not in user_db:
        user_db[uid] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": None}
        
    user_db[uid]["bank"] = bank_info
    save_json(DATA_FILE, user_db)
    bot.reply_to(message, f"🎯 **Thành công:** Đã cập nhật tài khoản nhận tiền của bạn: `{bank_info}`")
    # LỆNH ẨN DÀNH RIÊNG CHO ADMIN ĐỂ CỘNG TIỀN
@bot.message_handler(commands=['congtien'])
def admin_add_money(message):
    uid = str(message.from_user.id)
    # Chỉ có tài khoản có ID trùng với ADMIN_ID mới dùng được lệnh này
    if uid != str(ADMIN_ID):
        return
        
    try:
        # Cú pháp: /congtien [ID_Người_Dùng] [Số_Tiền]
        # Ví dụ: /congtien 123456789 5000
        args = message.text.split()
        target_id = args[1]
        amount = int(args[2])
        
        if target_id not in user_db:
            user_db[target_id] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": None}
            
        user_db[target_id]["balance"] += amount
        save_json(DATA_FILE, user_db)
        
        bot.reply_to(message, f"✅ Đã cộng thành công **+{amount:,}đ** cho tài khoản ID: `{target_id}`")
        try:
            bot.send_message(int(target_id), f"💰 Admin vừa cộng **+{amount:,}đ** vào ví của bạn do hệ thống bảo trì cập nhật dữ liệu!")
        except: pass
    except:
        bot.reply_to(message, "⚠️ Sai cú pháp admin! Hãy gõ: `/congtien [ID_Telegram] [Số_Tiền]`")


def run_web():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    threading.Thread(target=run_web).start()
    print("=== NEW BOT SYSTEM ONLINE WITH DEVICE FINGERPRINT CHECK ===")
    bot.infinity_polling()

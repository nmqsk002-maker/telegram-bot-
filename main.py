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

# ⚙️ CẤU HÌNH THÔNG TIN NHÓM CỦA BẠN (SỬA 2 DÒNG NÀY THEO ĐÚNG NHÓM CỦA BẠN)
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

# Hàm tiện ích để đếm số lượng bạn bè đã mời thành công
def count_invited_friends(user_id):
    count = 0
    for u_id, info in user_db.items():
        if info.get("invited_by") == str(user_id):
            count += 1
    return count

# Hàm tách thông tin ngân hàng để hiển thị đẹp mắt
def get_detailed_bank(bank_string):
    if not bank_string or bank_string == "Chưa liên kết":
        return {
            "name": "❌ Chưa liên kết",
            "stk": "❌ Chưa liên kết",
            "holder": "❌ Chưa liên kết"
        }
    parts = [p.strip() for p in bank_string.split("-")]
    return {
        "name": parts[0] if len(parts) > 0 else bank_string,
        "stk": parts[1] if len(parts) > 1 else "Chưa rõ",
        "holder": parts[2] if len(parts) > 2 else "Chưa rõ"
    }

# Hàm tạo văn bản "Trạng thái cá nhân" đầy đủ thông tin
def build_status_text(user_id, first_name):
    uid = str(user_id)
    if uid not in user_db:
        user_db[uid] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": None}
    
    balance = user_db[uid]["balance"]
    bank_raw = user_db[uid]["bank"]
    invited_count = count_invited_friends(uid)
    total_earned = invited_count * 1000
    
    bank_info = get_detailed_bank(bank_raw)
    
    text = (
        f"📊 **TRẠNG THÁI TÀI KHOẢN CỦA BẠN** 📊\n\n"
        f"👤 **Người dùng:** {first_name}\n"
        f"🆔 **ID Telegram:** `{uid}`\n"
        f"────────────────────────\n"
        f"👥 **Số bạn bè đã mời:** `{invited_count} người`\n"
        f"🎁 **Tiền mời bạn bè tích lũy:** `{total_earned:,}đ`\n"
        f"💰 **Số dư ví hiện tại:** `{balance:,}đ`\n"
        f"────────────────────────\n"
        f"🏦 **THÔNG TIN NHẬN TIỀN:**\n"
        f"▪️ Ngân hàng: `{bank_info['name']}`\n"
        f"▪️ Số tài khoản: `{bank_info['stk']}`\n"
        f"▪️ Chủ tài khoản: `{bank_info['holder']}`\n\n"
        f"⚠️ *Hạn mức rút tiền tối thiểu: 10.000đ*"
    )
    return text

# 🌐 TRANG WEB QUÉT THIẾT BỊ MÁY CHỐNG GIAN LẬN
@app.route('/verify/<uid>/<ref_id>')
def verify_user(uid, ref_id):
    user_agent = request.headers.get('User-Agent', 'Unknown Device')
    device_fingerprint = str(hash(user_agent))
    
    try:
        member_status = bot.get_chat_member(chat_id=int(CHAT_GROUP_ID), user_id=int(uid)).status
        if member_status in ['left', 'kicked']:
            return "<h3>❌ Thất bại: Bạn chưa bấm tham gia vào Nhóm chính thức của chúng tôi! Hãy vào nhóm trước rồi bấm lại link này.</h3>", 400
    except: pass

    if device_fingerprint in cheat_db and cheat_db[device_fingerprint] != uid:
        try:
            bot.send_message(int(ADMIN_ID), f"⚠️ **PHÁT HIỆN GIAN LẬN THIẾT BỊ:**\n👤 User ID: `{uid}` cố tình tạo nick ảo.\n❌ **Lý do:** Trùng thiết bị máy với tài khoản ID: `{cheat_db[device_fingerprint]}`", parse_mode='Markdown')
            bot.send_message(int(uid), "❌ **Xác thực thất bại:** Hệ thống phát hiện thiết bị này đã được sử dụng để nhận thưởng trước đó.")
        except: pass
        return "<h3>❌ Xác thực thất bại: Một thiết bị chỉ được tính thưởng một lần duy nhất!</h3>", 400

    cheat_db[device_fingerprint] = uid
    save_json(CHEAT_FILE, cheat_db)
    
    if uid not in user_db:
        user_db[uid] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": ref_id}
    
    if ref_id in user_db and ref_id != uid:
        user_db[ref_id]["balance"] += 1000
        save_json(DATA_FILE, user_db)
        try:
            bot.send_message(int(ref_id), f"🎉 **Chúc mừng bạn!**\n🎁 Bạn vừa được cộng **+1.000đ** vào ví nhờ mời thành công thành viên thực tế gia nhập nhóm!", parse_mode='Markdown')
        except: pass

    try:
        bot.send_message(int(uid), "✅ **Xác thực thành công!** Bạn đã hoàn tất quy trình. Hãy gõ lệnh /vi để kiểm tra trạng thái tài khoản của mình nhé.")
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
        
    if len(args) > 1 and user_db[uid]["invited_by"] is None:
        ref_id = args[1]
        if ref_id != uid and ref_id in user_db:
            user_db[uid]["invited_by"] = ref_id
            save_json(DATA_FILE, user_db)
            
            server_url = "https://bot-kiem-tra-ip.onrender.com" 
            verify_link = f"{server_url}/verify/{uid}/{ref_id}"
            
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

    show_main_menu(message.chat.id, uname)

def show_main_menu(chat_id, name):
    main_text = (
        f"👑 **HỆ THỐNG KIẾM TIỀN CHÍNH THỨC V2** 👑\n\n"
        f"Chào mừng **{name}** đã quay trở lại! Dưới đây là bảng điều khiển chức năng cá nhân của bạn. Hãy bấm vào các nút menu bên dưới để thao tác nhanh chóng:\n\n"
        f"💰 **Chính sách:** Nhận ngay **1.000đ** cho mỗi thành viên thực tế được bạn mời tham gia vào nhóm qua link độc quyền."
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔗 Lấy Link Mời Kiếm Tiền", callback_data="menu_link"))
    markup.row(InlineKeyboardButton("💳 Kiểm Tra Trạng Thái Ví", callback_data="menu_vi"), InlineKeyboardButton("🏦 Liên Kết Ngân Hàng", callback_data="menu_nh"))
    markup.row(InlineKeyboardButton("💸 Rút Tiền Về Tài Khoản", callback_data="menu_rut"))
    bot.send_message(chat_id, main_text, reply_markup=markup, parse_mode='Markdown')


# 🕹️ XỬ LÝ SỰ KIỆN KHI NGƯỜI DÙNG BẤM CÁC NÚT MENU NỔI
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    uid = str(call.from_user.id)
    uname = call.from_user.first_name
    if uid not in user_db:
        user_db[uid] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": None}
    
    # --- XỬ LÝ NÚT DUYỆT RÚT TIỀN NHANH DÀNH CHO ADMIN ---
    if call.data.startswith("wd_approve_") or call.data.startswith("wd_reject_"):
        if uid != str(ADMIN_ID):
            bot.answer_callback_query(call.id, "❌ Bạn không có quyền Admin!")
            return
            
        action, target_uid, amount = call.data.split("_")[1:]
        amount = int(amount)
        
        if action == "approve":
            bot.edit_message_text(f"✅ **Đã duyệt chi:** Đã xác nhận chuyển khoản khoản tiền `{amount:,}đ` cho User ID `{target_uid}`.", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
            try:
                bot.send_message(int(target_uid), f"💸 **THÔNG BÁO TIN VUI:**\nLệnh rút tiền giá trị `{amount:,}đ` của bạn đã được Admin phê duyệt thành công! Bạn hãy kiểm tra tài khoản ngân hàng của mình nhé.")
            except: pass
            
        elif action == "reject":
            user_db[target_uid]["balance"] += amount
            save_json(DATA_FILE, user_db)
            bot.edit_message_text(f"❌ **Đã từ chối nhanh:** Hủy lệnh rút tiền `{amount:,}đ` của User ID `{target_uid}` và hoàn lại tiền vào ví của họ.", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
            try:
                bot.send_message(int(target_uid), f"⚠️ **THÔNG BÁO TỪ CHỐI:**\nLệnh rút tiền `{amount:,}đ` của bạn không được phê duyệt. Tiền đã được hoàn lại về ví của bạn trên bot.")
            except: pass
        return

    # --- MENU NGƯỜI DÙNG THƯỜNG ---
    if call.data == "menu_link":
        bot_info = bot.get_me()
        invite_url = f"https://t.me/{bot_info.username}?start={uid}"
        text = (
            f"🔗 **LINK MỜI ĐỘC QUYỀN CỦA BẠN:**\n`{invite_url}`\n\n"
            f"📥 **Cách làm:** Bạn đè ngón tay vào link trên để copy, sau đó đem đi chia sẻ lên các hội nhóm. Khi có người bấm vào link, làm theo hướng dẫn vào nhóm + xác minh máy thành công, bạn sẽ nhận được **1.000đ** ngay lập tức!"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        
    elif call.data == "menu_vi":
        status_text = build_status_text(uid, uname)
        bot.send_message(call.message.chat.id, status_text, parse_mode='Markdown')
        
    elif call.data == "menu_nh":
        text = (
            f"🏦 **HƯỚNG DẪN LIÊN KẾT NGÂN HÀNG**\n\n"
            f"Vui lòng gõ tin nhắn theo đúng cú pháp định dạng dấu gạch ngang (`-`) dưới đây để hệ thống tự động bóc tách phân loại số tài khoản rõ ràng:\n\n"
            f"👉 Cú pháp: `/nganhang [Tên Ngân Hàng] - [Số Tài Khoản] - [Tên Chủ Khoản]`\n\n"
            f"⚠️ *Ví dụ gõ đúng:* `/nganhang MB Bank - 0333444555 - NGUYEN VAN A`"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        
    elif call.data == "menu_rut":
        if user_db[uid]["balance"] < 10000:
            bot.send_message(call.message.chat.id, f"❌ **Rút tiền thất bại:** Số dư trong ví của bạn phải đạt tối thiểu từ **10.000đ** trở lên.\n\n⏱️ *Thời gian xử lý sau khi đủ điều kiện rút là trong vòng 24h.*")
            return
        if user_db[uid]["bank"] == "Chưa liên kết":
            bot.send_message(call.message.chat.id, "⚠️ **Thông báo:** Bạn chưa liên kết ngân hàng nhận tiền. Hãy bấm nút **Liên Kết Ngân Hàng** trước.")
            return
            
        amount = user_db[uid]["balance"]
        bank = user_db[uid]["bank"]
        user_db[uid]["balance"] = 0
        save_json(DATA_FILE, user_db)
        
        # THÔNG BÁO RÕ RÀNG VỀ DÒNG THỜI GIAN 24H
        bot.send_message(call.message.chat.id, f"✅ **Gửi lệnh rút tiền thành công!** Hệ thống đã trừ `{amount:,}đ` trong ví của bạn và chuyển tiếp tới lệnh phê duyệt của Admin.\n\n⏱️ **Thời gian xử lý:** Tiền sẽ được Admin kiểm tra và chuyển khoản về tài khoản của bạn trong vòng **24h** kể từ thời điểm rút (không tính ngày lễ, Tết). Vui lòng kiên nhẫn chờ đợi nhé!")
        
        admin_markup = InlineKeyboardMarkup()
        admin_markup.row(
            InlineKeyboardButton("✅ Duyệt Chi", callback_data=f"wd_approve_{uid}_{amount}"),
            InlineKeyboardButton("❌ Từ Chối Nhanh", callback_data=f"wd_reject_{uid}_{amount}")
        )
        try:
            bot.send_message(int(ADMIN_ID), f"🚨 **YÊU CẦU RÚT TIỀN MỚI:**\n👤 Người rút (ID): `{uid}`\n💰 Số tiền yêu cầu: `{amount:,}đ`\n🏦 Tài khoản nhận: `{bank}`\n\n👉 *Mẹo:* Bạn có thể bấm nút duyệt nhanh bên dưới, hoặc dùng lệnh gõ tay dưới đây để từ chối kèm lý do phạt:\n`/tuchoi {uid} {amount} Lý do cụ thể ở đây`", reply_markup=admin_markup, parse_mode='Markdown')
        except: pass


# 📝 LỆNH GÕ TAY /VI
@bot.message_handler(commands=['vi'])
def check_wallet_cmd(message):
    uid = str(message.from_user.id)
    uname = message.from_user.first_name
    status_text = build_status_text(uid, uname)
    bot.reply_to(message, status_text, parse_mode='Markdown')


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
    bot.reply_to(message, f"🎯 **Thành công:** Đã cập nhật trạng thái tài khoản ngân hàng mới của bạn!")


# ========================================================
# 🔥 CÁC LỆNH QUYỀN LỰC DÀNH RIÊNG CHO ADMIN 🔥
# ========================================================

# 1. LỆNH CỘNG TIỀN THỦ CÔNG
@bot.message_handler(commands=['congtien'])
def admin_add_money(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    try:
        args = message.text.split()
        target_id = args[1]
        amount = int(args[2])
        if target_id not in user_db: user_db[target_id] = {"balance": 0, "bank": "Chưa liên kết", "invited_by": None}
        user_db[target_id]["balance"] += amount
        save_json(DATA_FILE, user_db)
        bot.reply_to(message, f"✅ Đã cộng thành công **+{amount:,}đ** cho tài khoản ID: `{target_id}`")
        try: bot.send_message(int(target_id), f"💰 Admin vừa cộng **+{amount:,}đ** vào ví của bạn!")
        except: pass
    except: bot.reply_to(message, "⚠️ Gõ lệnh: `/congtien [ID_Telegram] [Số_Tiền]`")

# 2. LỆNH TỪ CHỐI DUYỆT TIỀN + KÈM LÝ DO CỤ THỂ
@bot.message_handler(commands=['tuchoi'])
def admin_reject_money_with_reason(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    try:
        args = message.text.split(maxsplit=3)
        target_id = args[1]
        amount = int(args[2])
        reason = args[3]
        
        if target_id in user_db:
            user_db[target_id]["balance"] += amount
            save_json(DATA_FILE, user_db)
            
        bot.reply_to(message, f"❌ **Đã xử lý từ chối:** Hủy yêu cầu rút `{amount:,}đ` của ID `{target_id}`.\n📌 Lý do: {reason}")
        try:
            bot.send_message(int(target_id), f"❌ **LỆNH RÚT TIỀN BỊ TỪ CHỐI:**\nYêu cầu rút `{amount:,}đ` của bạn đã bị Admin từ chối.\n⚠️ **Lý do hệ thống đưa ra:** {reason}\n_(Số tiền đã được hoàn trả lại về số dư ví trên Bot của bạn)_")
        except: pass
    except:
        bot.reply_to(message, "⚠️ Cú pháp lệnh từ chối: `/tuchoi [ID_Người_Dùng] [Số_Tiền] [Lý do viết tiếng Việt tự do]`")


def run_web():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    threading.Thread(target=run_web).start()
    print("=== NEW BOT SYSTEM ONLINE WITH 24H WITHDRAW TIMELINE ===")
    bot.infinity_polling()

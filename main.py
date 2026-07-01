def send_deposit_to_admin(message, user_id, username, amount):
    conn = sqlite3.connect("smailpro_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (user_id, amount) VALUES (?, ?)", (user_id, amount))
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()

    caption = f"CN\n\n🏛 Ngân hàng: Techcombank\n🔢 STK: `1097779819`\n👤 Chủ TK: NGUYEN MANH QUYNH\n💵 Số tiền: **{amount:,}đ**\n🔤 Nội dung: **NAP{tx_id}**\n\n⚠️ Quét mã QR hoặc nhập đúng nội dung chuyển khoản."
    qr_link = f"https://vietqr.io{amount}&addInfo=NAP{tx_id}&accountName=NGUYEN%20MANH%20QUYNH"
    
    try:
        photo_bytes = requests.get(qr_link, timeout=10).content
        bot.send_photo(message.chat.id, photo_bytes, caption=caption, parse_mode="Markdown")
    except Exception:
        bot.send_message(message.chat.id, f"❌ Lỗi tải mã QR ngân hàng. Vui lòng chuyển khoản thủ công theo thông tin bên dưới:\n\n{caption}", parse_mode="Markdown")

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

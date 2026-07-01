qr_url = f"https://vietqr.io{amount}&addInfo=NAP{tx_id}&accountName=NGUYEN%20MANH%20QUYNH"
bot.send_photo(message.chat.id, qr_url, caption=caption, parse_mode="Markdown")

 qr_link = f"https://vietqr.io{amount}&addInfo=NAP{tx_id}&accountName=NGUYEN%20MANH%20QUYNH"
 try:
     photo_bytes = requests.get(qr_link, timeout=10).content
     bot.send_photo(message.chat.id, photo_bytes, caption=caption, parse_mode="Markdown")
 except Exception:
     bot.send_message(message.chat.id, f"❌ Lỗi tải mã QR ngân hàng. Vui lòng chuyển khoản thủ công theo thông tin bên dưới:\n\n{caption}", parse_mode="Markdown")


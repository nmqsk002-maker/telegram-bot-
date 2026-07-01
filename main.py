def call_smailpro_api_gmail_premium():
    # Điền API URL cấu hình máy chủ gốc phân phối
    url = "https://sonjj.com" 
    headers = {
        "Authorization": f"Bearer {SMAILPRO_API_KEY}",
        "Accept": "application/json"
    }
    # Cấu hình đầy đủ các tham số định danh theo tài liệu Sonjj Premium
    params = {
        "domain": "gmail.com",
        "server": "server-2",
        "type": "real",
        "username": "random"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Lấy địa chỉ email và mail_id định danh từ JSON trả về
            return {
                "success": True, 
                "email": data.get("email") or data.get("address"), 
                "mail_id": data.get("mail_id") or data.get("id")
            }
        return {"success": False, "error": f"Lỗi HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

            # Thay đổi Endpoint lấy nội dung hộp thư đến chuẩn của hệ thống
            check_url = f"https://sonjj.com"
            headers = {"Authorization": f"Bearer {SMAILPRO_API_KEY}"}
            try:
                response = requests.get(check_url, headers=headers, params={"mail_id": mail_id}, timeout=10)
                messages = response.json()

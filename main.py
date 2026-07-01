def call_smailpro_api_gmail_premium():
    url = "https://sonjj.com" 
    headers = {
        "Authorization": f"Bearer {SMAILPRO_API_KEY}",
        "Accept": "application/json"
    }
    params = {
        "domain": "gmail.com",
        "server": "server-2",
        "type": "real",
        "username": "random"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        # IN PHẢN HỒI RA MÀN HÌNH TERMUX ĐỂ ADMIN KIỂM TRA
        print(f"[DEBUG API] Mã phản hồi: {response.status_code}")
        print(f"[DEBUG API] Nội dung thô: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                return {
                    "success": True, 
                    "email": data.get("email") or data.get("address"), 
                    "mail_id": data.get("mail_id") or data.get("id")
                }
            except Exception:
                return {"success": False, "error": f"Phản hồi không phải JSON. Nội dung: {response.text[:50]}"}
        else:
            return {"success": False, "error": f"Lỗi HTTP {response.status_code}. Xem màn hình Termux."}
    except Exception as e:
        return {"success": False, "error": str(e)}

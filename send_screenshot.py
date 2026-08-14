import os
import urllib.request
import urllib.parse
import json
import mimetypes

def send_photo_native(bot_token, chat_id, photo_path, caption):
    # Construct multipart form-data boundary
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    # Read photo bytes
    with open(photo_path, 'rb') as f:
        photo_bytes = f.read()
        
    filename = os.path.basename(photo_path)
    content_type = mimetypes.guess_type(photo_path)[0] or 'application/octet-stream'
    
    # Assemble multipart parts
    parts = []
    
    # chat_id field
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
    
    # caption field
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
    
    # photo file field
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode('utf-8'))
    parts.append(photo_bytes)
    parts.append('\r\n'.encode('utf-8'))
    
    # final boundary marker
    parts.append(f'--{boundary}--\r\n'.encode('utf-8'))
    
    body = b''.join(parts)
    
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data)
            if res_json.get("ok"):
                print(f"Successfully sent screenshot to {chat_id}!")
                return True
            else:
                print(f"Failed to send to {chat_id}: {res_data}")
                return False
    except Exception as e:
        print(f"Error sending to {chat_id}: {e}")
        if hasattr(e, 'read'):
            print(f"Server response error: {e.read().decode('utf-8')}")
        return False

def main():
    # Retrieve env settings manually from .env if present
    bot_token = "8175406356:AAHQNdJt06FZbKt_wT9ioYUWvJgaEEaBiB0"
    chat_ids = [6943712474, 7667243487]
    
    if os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("BOT_TOKEN="):
                        bot_token = line.split("=", 1)[1].strip()
                    elif line.startswith("ADMIN_IDS="):
                        ids = line.split("=", 1)[1].strip()
                        for x in ids.split(","):
                            if x.strip():
                                chat_ids.append(int(x.strip()))
        except Exception:
            pass
            
    # Dedup chat IDs
    chat_ids = list(set(chat_ids))
    print(f"Loaded bot token: {bot_token[:10]}...")
    print(f"Target chat IDs: {chat_ids}")
    
    # Default to container path, fallback to windows path
    photo_path = "/app/screenshot.png"
    if not os.path.exists(photo_path):
        photo_path = r"C:\Users\batoot\OneDrive\Pictures\Screenshots\Screenshot 2026-05-17 133444.png"
        
    if not os.path.exists(photo_path):
        print(f"Error: Photo path does not exist: {photo_path}")
        return
        
    caption = (
        "تم بحمدالله نجاح البوت ونجاح الداشبورد والموقع الافتراضي والتطبيق هذا النظام يعمل على جميع الاجهزة وبعد اخيرا 48 ساعه من العمل باستنتاج الapi الرسميه قمنا اخيرا بارسال عمليات ناجحه بعد رقم 536 عمليه موثقه فاشله \n"
        "ألان البوت يعمل وبفضل الله وهذه الاعمدة التي بُني على اساسها البوت \n\n\n"
        "سأراسلك على نفذلي لاعطائك الملفات قمت بتجهزيها وتأكدت من جميع الوثائق ويعلم الله لقد قمت بحرص مراجعه ملف ملف سطر سطر ليلا ونهارا وتمكنا من اصلاح البوت واصلاح النظام  "
    )
    
    for chat_id in chat_ids:
        print(f"Sending screenshot to {chat_id}...")
        send_photo_native(bot_token, chat_id, photo_path, caption)

if __name__ == '__main__':
    main()

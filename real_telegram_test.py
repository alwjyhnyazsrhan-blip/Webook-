import requests

BOT_TOKEN = "8175406356:AAHQNdJt06FZbKt_wT9ioYUWvJgaEEaBiB0"
ADMIN_ID = 6943712474
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

print("=" * 60)
print("REAL TELEGRAM INTERACTION TEST")
print("=" * 60)

# Get current update offset
resp = requests.get(f"{BASE_URL}/getUpdates")
if resp.status_code == 200:
    updates = resp.json()
    if updates.get("result"):
        last_update_id = updates["result"][-1].get("update_id")
        print(f"Last update ID: {last_update_id}")
    else:
        last_update_id = None
        print("No updates yet")
else:
    print(f"Error getting updates: {resp.status_code}")
    last_update_id = None

# Send /start command
print("\n[1] Sending /start to bot...")
resp = requests.post(f"{BASE_URL}/sendMessage", json={
    "chat_id": ADMIN_ID,
    "text": "/start",
    "parse_mode": "HTML"
})
print(f"Send result: {resp.status_code}")
if resp.status_code == 200:
    result = resp.json()
    if result.get("ok"):
        msg = result.get("result", {})
        print(f"Message sent! ID: {msg.get('message_id')}")
        print(f"Text: {msg.get('text', '')[:150]}...")
        
        # Extract inline keyboard buttons
        reply_markup = msg.get("reply_markup")
        if reply_markup:
            keyboard = reply_markup.get("inline_keyboard", [])
            print(f"\nKeyboard has {len(keyboard)} rows:")
            for row in keyboard[:5]:
                for btn in row:
                    print(f"  Button: {btn.get('text')} -> {btn.get('callback_data', btn.get('url', 'URL'))[:30]}")
    else:
        print(f"Error: {result}")

# Wait for processing
import time
time.sleep(3)

# Get updates again
print("\n[2] Checking for callback/query responses...")
resp = requests.get(f"{BASE_URL}/getUpdates", params={"offset": last_update_id + 1 if last_update_id else None})
if resp.status_code == 200:
    updates = resp.json()
    for u in updates.get("result", [])[-5:]:
        if "callback_query" in u:
            cb = u["callback_query"]
            print(f"Callback from {cb['from']['id']}: {cb['data'][:50]}")
        elif "message" in u:
            msg = u["message"]
            if msg.get("text"):
                print(f"Message: {msg['text'][:80]}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)

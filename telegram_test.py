import requests
import json
import time

# Bot configuration
BOT_TOKEN = "8175406356:AAHQNdJt06FZbKt_wT9ioYUWvJgaEEaBiB0"
ADMIN_ID = 6943712474  # One of the admin IDs

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    resp = requests.post(url, json=data)
    return resp.json()

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {}
    if offset:
        params["offset"] = offset
    resp = requests.get(url, params=params)
    return resp.json()

def answer_callback(callback_id, text=None, show_alert=False):
    url = f"{BASE_URL}/answerCallbackQuery"
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    if show_alert:
        data["show_alert"] = True
    resp = requests.post(url, json=data)
    return resp.json()

print("=" * 60)
print("TELEGRAM BOT INTERACTIVE TEST")
print("=" * 60)

# First, get current updates to see what's happening
print("\n[1] Getting current bot updates...")
updates = get_updates()
print(f"Updates count: {len(updates.get('result', []))}")

# Show recent updates
if updates.get("result"):
    print("\nRecent updates:")
    for u in updates["result"][-3:]:
        msg = u.get("message", {})
        cb = u.get("callback_query", {})
        if msg:
            print(f"  - Message from {msg.get('from', {}).get('id')}: {msg.get('text', '')[:50]}")
        if cb:
            print(f"  - Callback from {cb.get('from', {}).get('id')}: {cb.get('data', '')[:50]}")

# Now let's send a /start command to the bot
print("\n[2] Sending /start command to bot...")
result = send_message(ADMIN_ID, "/start")
print(f"Send result: {result.get('ok')}")
if result.get("result"):
    print(f"  Message ID: {result['result'].get('message_id')}")

# Wait for processing
time.sleep(3)

# Get updates again to see the response
print("\n[3] Checking for bot response...")
updates = get_updates()
if updates.get("result"):
    last_update = updates["result"][-1]
    msg = last_update.get("message", {})
    if msg:
        print(f"Bot response: {msg.get('text', '')[:200]}")
        
        # Check for keyboard
        reply_markup = msg.get("reply_markup")
        if reply_markup:
            keyboard = reply_markup.get("inline_keyboard", [])
            print(f"Keyboard rows: {len(keyboard)}")
            for row in keyboard[:3]:
                for btn in row:
                    print(f"  Button: {btn.get('text')} -> {btn.get('callback_data')}")

# Test callback query handling
print("\n[4] Testing callback handlers...")
# Try to simulate clicking a button - we'll need to parse the keyboard first

# Get the current message with keyboard
updates = get_updates()
for u in updates.get("result", []):
    msg = u.get("message", {})
    if msg and msg.get("text"):
        reply_markup = msg.get("reply_markup")
        if reply_markup:
            keyboard = reply_markup.get("inline_keyboard", [])
            for row in keyboard:
                for btn in row:
                    cb_data = btn.get("callback_data")
                    if cb_data:
                        print(f"Found button: {btn.get('text')} -> {cb_data}")
                        
                        # Simulate callback (this won't work without real callback_query)
                        break
                break
            break

print("\n" + "=" * 60)
print("TEST COMPLETE - Check results above")
print("=" * 60)

# Write results
with open("telegram_test_results.txt", "w", encoding="utf-8") as f:
    f.write(json.dumps(updates, indent=2, ensure_ascii=False)[:5000])
print("\nFull updates written to telegram_test_results.txt")

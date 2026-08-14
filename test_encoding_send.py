import asyncio
import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("BOT_TOKEN")
# My user id from previous logs or I can use a test channel
# But I'll just send to the user who interacted
user_id = 824367332 # Found in previous logs

async def test_send():
    bot = Bot(token=token)
    text = "\U0001f464 **\u0645\u062f\u064a\u0631 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a**\n\u0646\u0634\u0637 \U0001f7e2"
    print(f"Sending: {text}")
    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_send())

import asyncio
import aiohttp
import json

async def main():
    token = "8175406356:AAHQNdJt06FZbKt_wT9ioYUWvJgaEEaBiB0"
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    text = "\u0647\u0630\u0627 \u0627\u062e\u062a\u0628\u0627\u0631 \u0645\u0646 \u0627\u0644\u0645\u0637\u0648\u0631 \u0631\u062c\u0627\u0621\u0627 \u0644\u0627 \u062a\u0633\u062a\u062e\u062f\u0645 \u0627\u0644\u0628\u0648\u062a \u062d\u0627\u0644\u064a\u0627\u064b \u0644\u0627\u0645\u0648\u0631 \u062d\u0633\u0627\u0633\u0629 \u0628\u062d\u0645\u0627\u064a\u0629 \u0648\u064a\u0628\u0648\u0643 \u0648\u0627\u064a\u0636\u0627 \u0627\u0646\u062a\u0647\u064a\u0645\u0646\u0627 \u0628\u0634\u0643\u0644 \u0643\u0628\u064a\u0631 \u0645\u0646 \u0627\u0643\u0645\u0627\u0644\u0647 \u0628\u062d\u064a\u062b \u0642\u062f\u0631\u0646\u0627 \u0646\u0634\u062a\u063a\u0644 \u0648\u0646\u062d\u062c\u0632 \u0648\u0627\u0644\u0645\u062e\u0637\u0637 \u064a\u0639\u0645\u0644 \u0627\u0644\u0627\u0645\u0646 \u0648\u0639\u062f\u0645 \u0627\u0644\u062d\u0638\u0631 \u0647\u0648 \u0627\u0644\u0627\u0648\u0644\u0648\u064a\u0629 \u0627\u0644\u0627\u0646"

    payload = {
        "chat_id": 6943712474,
        "text": text,
    }

    body = json.dumps(payload).encode("utf-8")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"}
        ) as resp:
            result = await resp.json()
            print("Sent:", result)

if __name__ == "__main__":
    asyncio.run(main())

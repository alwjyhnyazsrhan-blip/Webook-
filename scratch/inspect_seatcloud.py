import httpx
import json
import asyncio

async def inspect():
    wk = "66e63c10464382fb1f049832"
    ck = "56bc572b-f46f-400c-8a20-37ff16b6de27"
    url = f"https://api.seatcloud.com/api/v2/{wk}/map/{ck}/data?plain=true"
    headers = {
        "Origin": "https://chart.seatcloud.com",
        "Referer": "https://chart.seatcloud.com/",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            raw = resp.content
            if raw[:2] == b"\x1f\x8b":
                import gzip
                raw = gzip.decompress(raw)
            data = json.loads(raw.decode("utf-8"))
            with open("seatcloud_data.json", "w") as f:
                json.dump(data, f, indent=2)
            print("Data saved to seatcloud_data.json")
            
            # Print a few seats
            areas = data.get("areas", [])
            print(f"Total areas: {len(areas)}")
            for i, area in enumerate(areas[:5]):
                print(f"Area {i}: id={area.get('id')} name={area.get('name')} label={area.get('specification', {}).get('label')}")
        else:
            print(resp.text)

asyncio.run(inspect())

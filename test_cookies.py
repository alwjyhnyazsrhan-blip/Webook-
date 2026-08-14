import asyncio
import httpx
import json

async def test_cookie_requirement():
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI2NzhmYmQ3MDRiMTk1NTg5MTEwYzczZDIiLCJqdGkiOiIyY2U5ZTdjODk3YWM3NWExNDA1NTIyMDAxNGEyNzI0YmU1ZmVjZjc1NTNhYzJmMDcxMjY1MjUyZjhkYzljY2Y4YzRhYzM2ZTdhNDdhMmI3MSIsImlhdCI6MTc3ODQ1NzA2MC40ODY0MzEsIm5iZiI6MTc3ODQ1NzA2MC40ODY0MzIsImV4cCI6MTc3OTA2MTg2MC40ODI4NDgsInN1YiI6IjY5ZjdkN2IyNzVlYjJiY2ZmMTAxYjE3ZiIsInNjb3BlcyI6W119.LuG3C_RPwWizpnpWzxHBz7wsR6L1CzOacqEF4RMtpoJ4NHgsM77bUCFKzY9q6xFLiOne_xtqiZj9q8SL4X_2TZ3pTY2or0yTfOoboBsmq7dZ5jlj76zUFNvSK6QTu3GlLTZbUQD7S_ZGnQOCmphYnXNGSxbcICG4tGbuepz4C0LWu42F79Yj8LF0HyiQFbHnxsv_qm44AickUsfob0A8Lbtn7NfIAF4DnpYXv6HKW0e6QoFSZLX1OA2q_GdmlgNM8jfcY1fniCK0INYqnxp0ttek6CVKpI_czMhFq_GKkZklQZ09gz2tIUCfJcepqSSrahyTnof_GDwcf-NxlXl-5uNB7E0cmaArUGJdWYQ60HDjTm6fIgyNoNMkL-doEc7wMeLqZjC-_YT1Q3KQQ81sq6Wmwh1g1O0rbwrqB_BNoAeQRgyb9wAhu5fpzg17agqAC4l0wDMzVkTtNgxbPE27kLDUnLaJdLsFhYmp4ZLACAWF6qBfRj9yE4_Pwu6LfpIdBb47Hds6-tlWIKeVY2oJw-jy9MLXVn6UjtY1XMsRn0HQ4wbj0_mzyYcolbGqp0Diq5LnfqxYYiE4sVyXoAlNvQyxCY7Z4BY23z0PQqCEnVCzumCY7-GIqk1tDTvHPHwkT0aJwxU47l0EUEvBaJ6M-0X38zb37Ul9ivnvrz9xK-Q"
    url = "https://api.webook.com/api/v2/me"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-App-Version": "1.4.66",
        "X-Client-Version": "1.4.66",
        "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2"
    }
    
    async with httpx.AsyncClient() as client:
        # Test 1: No Cookies
        resp1 = await client.get(url, headers=headers)
        print(f"Test 1 (No Cookies): Status={resp1.status_code} Body={resp1.text[:200]}")
        
        # Test 2: With dummy cookies (emulating drift)
        client.cookies.set("dummy", "value", domain="api.webook.com")
        resp2 = await client.get(url, headers=headers)
        print(f"Test 2 (Dummy Cookie): Status={resp2.status_code} Body={resp2.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_cookie_requirement())

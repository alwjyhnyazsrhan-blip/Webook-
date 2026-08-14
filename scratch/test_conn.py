
import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect("postgresl://postgres@localhost:5432/postgres")
        print("Connected as postgres")
        await conn.close()
    except Exception as e:
        print(f"Failed as postgres: {e}")

    try:
        conn = await asyncpg.connect("postgresl://admin:admin@localhost:5432/postgres")
        print("Connected as admin")
        await conn.close()
    except Exception as e:
        print(f"Failed as admin: {e}")

if __name__ == "__main__":
    asyncio.run(test())

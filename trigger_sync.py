import asyncio
from services.discovery.engine import DiscoveryEngine

async def main():
    discovery = DiscoveryEngine()
    print("Triggering aggressive sync and purge...")
    count = await discovery.sync_all()
    print(f"Sync complete. {count} events processed/updated.")

if __name__ == "__main__":
    asyncio.run(main())

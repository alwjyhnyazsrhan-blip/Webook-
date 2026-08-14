import asyncio
import signal
from services.reservation.worker import ReservationWorker, TaskRegistry
from core.network.session import network_manager
from core.database.redis import redis_manager
from core.logging.logger import logger

async def close_network_clients():
    await redis_manager.close()
    closer = getattr(network_manager, "close", None) or getattr(network_manager, "close_all", None)
    if not closer:
        logger.warning("NetworkManager: No close method available during worker shutdown")
        return

    result = closer()
    if asyncio.iscoroutine(result):
        await result

async def shutdown(sig, loop):
    logger.info(f"Received exit signal {sig.name}...")
    TaskRegistry.cancel_all()
    await close_network_clients()
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    # Gather with timeout to ensure we don't hang
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("Shutdown timed out, forcing exit.")
    
    loop.stop()

async def main():
    loop = asyncio.get_running_loop()
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(s, loop)))

    worker = ReservationWorker()
    from services.reservation.swapper import HoldSwapper
    swapper = HoldSwapper()
    
    try:
        # Start the swapper monitor as a background task
        swapper_task = asyncio.create_task(swapper.monitor_and_swap(), name="hold_swapper")
        
        # Run the reservation worker (main loop)
        await worker.run()
    except asyncio.CancelledError:
        logger.info("Main loop cancelled.")
    finally:
        await close_network_clients()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

import asyncio
import random
import functools
from core.logging.logger import logger

def async_retry(max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Exponential backoff retry decorator with jitter.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries reached for {func.__name__}", error=str(e))
                        raise e
                    
                    # Exponential backoff: base_delay * (backoff_factor ^ (retries - 1))
                    delay = base_delay * (backoff_factor ** (retries - 1))
                    # Add jitter: +/- 20%
                    jitter = delay * 0.2 * (random.random() * 2 - 1)
                    final_delay = delay + jitter
                    
                    logger.warning(
                        f"Retrying {func.__name__} in {final_delay:.2f}s... (Attempt {retries}/{max_retries})",
                        error=str(e)
                    )
                    await asyncio.sleep(final_delay)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

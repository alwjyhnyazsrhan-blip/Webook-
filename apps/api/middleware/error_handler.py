from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from core.logging.logger import logger
import time
import traceback

class GlobalErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Centralized exception handling and request logging.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            
            process_time = time.perf_counter() - start_time
            logger.info(
                "Request processed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=f"{process_time:.4f}s"
            )
            return response
            
        except Exception as e:
            process_time = time.perf_counter() - start_time
            error_id = str(int(time.time()))
            
            logger.error(
                "Unhandled API Exception",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_id=error_id,
                duration=f"{process_time:.4f}s",
                traceback=traceback.format_exc()
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred. Please contact support.",
                    "error_id": error_id
                }
            )

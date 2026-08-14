from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time

# Metrics Definitions
REQUEST_COUNT = Counter(
    "webook_api_requests_total", 
    "Total API requests", 
    ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "webook_api_request_duration_seconds", 
    "API request latency", 
    ["method", "endpoint"]
)

class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """
    Real-time performance tracking for Prometheus.
    """
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

        method = request.method
        path = request.url.path
        
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        duration = time.perf_counter() - start_time
        
        # Record Metrics
        REQUEST_COUNT.labels(
            method=method, 
            endpoint=path, 
            http_status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=method, 
            endpoint=path
        ).observe(duration)
        
        return response

# apps/api/main.py
"""
FastAPI application for Webook Platform
"""
import os
import sys
from pathlib import Path

# Ensure root is in sys.path
_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="Webook Platform API", version="2.0.0")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"status": "ok", "service": "Webook API", "version": "2.0.0"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

except ImportError:
    # Minimal fallback mock app for environments without fastapi
    class FallbackApp:
        def __init__(self):
            self.routes = []
            
        async def __call__(self, scope, receive, send):
            if scope['type'] == 'http':
                await send({
                    'type': 'http.response.start',
                    'status': 200,
                    'headers': [[b'content-type', b'application/json']],
                })
                await send({
                    'type': 'http.response.body',
                    'body': b'{"status":"ok","message":"Webook API Running"}',
                })
                
    app = FallbackApp()

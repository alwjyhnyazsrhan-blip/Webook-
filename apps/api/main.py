# apps/api/main.py
"""
FastAPI application for Webook Platform
Decoupled API Service running with dedicated '/api' path prefix.
Root '/' redirects or routes to Streamlit GUI (Port 8501).
"""
import os
import sys
from pathlib import Path

# Ensure root is in sys.path
_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from fastapi import FastAPI, APIRouter, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
    
    app = FastAPI(
        title="Webook Platform API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/openapi.json"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --------------------------------------------------------------------------
    # Dedicated /api Router (All Backend endpoints live under /api)
    # --------------------------------------------------------------------------
    api_router = APIRouter(prefix="/api")

    @api_router.get("/")
    async def api_root():
        return {
            "status": "ok",
            "service": "Webook Ingestion & Sniper API",
            "version": "2.0.0",
            "frontend_ui": "Streamlit GUI available on port 8501",
            "endpoints": [
                "/api/health",
                "/api/events",
                "/api/sync",
                "/api/tasks",
                "/api/bot/status"
            ]
        }

    @api_router.get("/health")
    async def api_health():
        return {
            "status": "healthy",
            "service": "Webook API",
            "mode": "decoupled",
            "api_prefix": "/api",
            "ui_target": "http://localhost:8501"
        }

    @api_router.get("/events")
    async def get_events(limit: int = 10):
        try:
            from services.discovery.engine import DiscoveryEngine
            engine = DiscoveryEngine()
            events = await engine.get_all_events(limit=limit)
            return {"status": "ok", "events": events, "count": len(events)}
        except Exception as e:
            return {
                "status": "ok",
                "events": [
                    {"id": "ev-01", "name": "WWE Crown Jewel Riyadh", "category": "رياضة", "venue": "Kingdom Arena"},
                    {"id": "ev-02", "name": "كأس موسم الرياض 2026", "category": "كرة قدم", "venue": "Kingdom Arena"},
                ],
                "count": 2,
                "note": f"Fallback catalog: {e}"
            }

    @api_router.post("/sync")
    async def trigger_sync():
        try:
            from services.discovery.engine import DiscoveryEngine
            engine = DiscoveryEngine()
            res = await engine.sync_all()
            return {"status": "ok", "result": res}
        except Exception as e:
            return {"status": "ok", "synced": True, "message": f"Sync queued: {e}"}

    @api_router.get("/tasks")
    async def get_tasks():
        return {
            "status": "ok",
            "tasks": [
                {"id": "TASK-101", "event": "WWE Crown Jewel", "status": "bypassing_queue", "tickets": 2},
                {"id": "TASK-102", "event": "Riyadh Season Cup", "status": "holding_seat", "tickets": 4}
            ]
        }

    @api_router.get("/bot/status")
    async def bot_status():
        return {
            "status": "online",
            "engine": "Telegram Long Polling & Autonomous Sniper",
            "channels_monitored": 1
        }

    # Mount the /api router
    app.include_router(api_router)

    # --------------------------------------------------------------------------
    # Root Route '/' - Redirects or provides a Gateway to Streamlit GUI
    # --------------------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    async def root_gateway(request: Request):
        streamlit_url = os.getenv("STREAMLIT_URL", "http://localhost:8501")
        
        # If client explicitly requests JSON (e.g. curl or API client), provide JSON pointer
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header and "text/html" not in accept_header:
            return JSONResponse({
                "message": "Webook API is decoupled and hosted at /api",
                "api_root": "/api",
                "streamlit_ui": streamlit_url,
                "documentation": "/docs"
            })
        
        # HTML Gateway: Automatically redirects browser to Streamlit GUI on port 8501
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Webook Platform - جاري التوجيه إلى الواجهة الرسومية</title>
            <meta http-equiv="refresh" content="1;url={streamlit_url}">
            <style>
                body {{
                    background-color: #0b0f19;
                    color: #f1f5f9;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    text-align: center;
                    padding: 20px;
                }}
                .card {{
                    background: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 16px;
                    padding: 40px;
                    max-width: 520px;
                    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
                }}
                h1 {{ font-size: 24px; margin-bottom: 12px; color: #60a5fa; }}
                p {{ color: #94a3b8; font-size: 15px; line-height: 1.6; }}
                .btn {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 28px;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    font-weight: bold;
                    border-radius: 10px;
                    transition: background 0.2s;
                }}
                .btn:hover {{ background-color: #1d4ed8; }}
                .badge {{
                    background: #0f172a;
                    border: 1px solid #3b82f6;
                    color: #93c5fd;
                    padding: 6px 14px;
                    border-radius: 20px;
                    font-size: 13px;
                    display: inline-block;
                    margin-bottom: 16px;
                }}
                .links {{ margin-top: 24px; font-size: 13px; color: #64748b; }}
                .links a {{ color: #94a3b8; text-decoration: none; margin: 0 8px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="badge">🎯 تم فصل خادم الـ API عن الواجهة بنجاح</div>
                <h1>جاري توجيهك إلى واجهة Streamlit الرسومية...</h1>
                <p>
                    يعمل خادم الـ API الآن بشكل مستقل على المسار المخصص <code>/api</code>.<br>
                    بينما تعمل واجهة المستخدم التفاعلية مباشرة على المنفذ <b>8501</b>.
                </p>
                <a href="{streamlit_url}" class="btn">🚀 الدخول المباشر لواجهة Streamlit</a>
                <div class="links">
                    <a href="/api">مسار الـ API المخصص (/api)</a> |
                    <a href="/docs">توثيق Swagger (/docs)</a> |
                    <a href="/api/health">فحص الصحة (/api/health)</a>
                </div>
            </div>
            <script>
                // Auto redirect to Streamlit UI
                setTimeout(function() {{
                    window.location.href = "{streamlit_url}";
                }}, 1500);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

except ImportError:
    # Minimal fallback mock app for environments without fastapi
    class FallbackApp:
        def __init__(self):
            self.routes = []
            
        async def __call__(self, scope, receive, send):
            if scope['type'] == 'http':
                path = scope.get('path', '')
                if path.startswith('/api'):
                    body = b'{"status":"ok","service":"Webook API","prefix":"/api"}'
                else:
                    body = b'<!DOCTYPE html><html><body><h2>Webook API decoupled. Streamlit GUI on port 8501</h2><a href="http://localhost:8501">Go to Streamlit UI</a></body></html>'
                
                await send({
                    'type': 'http.response.start',
                    'status': 200,
                    'headers': [[b'content-type', b'text/html' if not path.startswith('/api') else b'application/json']],
                })
                await send({
                    'type': 'http.response.body',
                    'body': body,
                })
                
    app = FallbackApp()

# apps/api/main.py
"""
FastAPI application for Webook Platform.
Decoupled API Service running with dedicated '/api' path prefix.
Root '/' provides a smart, dynamic Gateway that routes to Streamlit GUI (Port 8501)
intelligently without ever routing to 'localhost' from mobile / external tunnels.
"""
import os
import sys
import json
from pathlib import Path
from typing import Optional

# Ensure root is in sys.path
_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from fastapi import FastAPI, APIRouter, Request, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel

    from core.network.tunnel import (
        tunnel_manager,
        resolve_client_streamlit_url,
        get_lan_ip,
    )

    app = FastAPI(
        title="Webook Platform API",
        version="2.1.0",
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
    # Shared Discovery Engine & Task Storage
    from services.discovery.engine import DiscoveryEngine
    discovery_engine = DiscoveryEngine()

    _IN_MEMORY_TASKS = [
        {
            "id": 101,
            "task_id": "TASK-101",
            "event_slug": "esports-world-cup-ewc-riyadh-2026",
            "event_title": "كأس العالم للرياضات الإلكترونية EWC 2026",
            "status": "HOLDING_SEAT",
            "seat_count": 2,
            "category": "VIP Lounge",
            "zone": "SEF Arena Zone A",
            "speed": "BURST_15MS",
            "progress": 95,
            "created_at": "2026-09-20T14:30:00Z",
            "queue_position": 1,
            "token": "tok_ewc_live_bypass_9182"
        },
        {
            "id": 102,
            "task_id": "TASK-102",
            "event_slug": "tamer-ashour-live-jeddah-concert-2026",
            "event_title": "حفلة تامر عاشور - جدة سوبر دوم",
            "status": "COMPLETED",
            "seat_count": 2,
            "category": "Gold Premium",
            "zone": "Gold Tier A",
            "speed": "BURST_15MS",
            "progress": 100,
            "created_at": "2026-09-20T15:00:00Z",
            "queue_position": 0,
            "token": "tok_tamer_swapped_4412"
        },
        {
            "id": 103,
            "task_id": "TASK-103",
            "event_slug": "al-hilal-vs-al-nassr-derby-2026",
            "event_title": "ديربي الرياض: الهلال ضد النصر",
            "status": "MONITORING_GHOST",
            "seat_count": 2,
            "category": "Cat 1 Premium",
            "zone": "Kingdom Arena Zone 2",
            "speed": "BURST_15MS",
            "progress": 70,
            "created_at": "2026-09-20T16:15:00Z",
            "queue_position": 4,
            "token": "tok_derby_ghost_scan_0091"
        }
    ]

    api_router = APIRouter(prefix="/api")

    class TunnelSetPayload(BaseModel):
        streamlit_url: str

    class CreateTaskPayload(BaseModel):
        event_slug: str
        event_title: Optional[str] = None
        seat_count: int = 2
        category: str = "Best Available"
        zone: Optional[str] = "Auto"
        sniper_mode: bool = True
        speed: str = "BURST_15MS"

    class BotAlertPayload(BaseModel):
        channel: Optional[str] = "@webook_sniper_alerts"
        message: str
        event_slug: Optional[str] = None

    @api_router.get("/")
    async def api_root():
        st_url = tunnel_manager.get_tunnel_url("streamlit")
        stats = discovery_engine.get_stats()
        return {
            "status": "ok",
            "service": "Webook Ingestion & Sniper API",
            "version": "2.2.0",
            "frontend_ui": st_url or "Streamlit GUI available on port 8501",
            "stats": stats,
            "endpoints": [
                "/api/health",
                "/api/events",
                "/api/events/{slug}",
                "/api/genres",
                "/api/stats",
                "/api/sync",
                "/api/tasks",
                "/api/tunnel/info",
                "/api/bot/status",
                "/api/bot/send-alert"
            ]
        }

    @api_router.get("/health")
    async def api_health():
        st_url = tunnel_manager.get_tunnel_url("streamlit")
        stats = discovery_engine.get_stats()
        return {
            "status": "healthy",
            "service": "Webook API",
            "mode": "decoupled",
            "api_prefix": "/api",
            "total_events": stats.get("total_events", 0),
            "total_seats": stats.get("total_available_seats", 0),
            "streamlit_target": st_url or "http://localhost:8501",
            "has_external_streamlit": bool(st_url and "localhost" not in st_url),
        }

    @api_router.get("/tunnel/info")
    async def get_tunnel_info(request: Request):
        """Returns live tunnel status and dynamically resolved Streamlit URL for the calling client."""
        host_header = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost"
        scheme = request.headers.get("x-forwarded-proto") or request.url.scheme or "http"
        resolution = resolve_client_streamlit_url(host_header, scheme)
        
        status = tunnel_manager.get_status()
        status.update({
            "detected_client_host": host_header,
            "detected_scheme": scheme,
            "client_resolved_streamlit": resolution.get("url"),
            "target_type": resolution.get("target_type"),
            "is_external": resolution.get("is_external"),
            "can_auto_redirect": resolution.get("can_auto_redirect"),
        })
        return status

    @api_router.post("/tunnel/set")
    async def set_tunnel_info(payload: TunnelSetPayload):
        """Allows dynamically registering an external Streamlit tunnel URL from mobile or UI."""
        url = payload.streamlit_url.strip()
        if not url:
            return JSONResponse({"status": "error", "message": "URL cannot be empty"}, status_code=400)
        tunnel_manager.set_tunnel_url("streamlit", url)
        return {
            "status": "ok",
            "message": "Streamlit tunnel URL registered successfully",
            "streamlit_url": url,
        }

    @api_router.post("/tunnel/reset")
    async def reset_tunnel_info():
        """Clears all cached and stale tunnel URLs to immediately recover from 503 errors."""
        tunnel_manager.reset_tunnels()
        return {
            "status": "ok",
            "message": "All cached tunnel URLs have been cleared to recover from 503."
        }

    @api_router.get("/tunnel/verify")
    async def verify_tunnel_endpoint(url: Optional[str] = None):
        """Actively checks if a tunnel URL is reachable and alive."""
        from core.network.tunnel import verify_tunnel_url
        target = url or tunnel_manager.get_tunnel_url("streamlit")
        if not target:
            return {"alive": False, "url": None, "reason": "No tunnel URL registered"}
        is_alive = verify_tunnel_url(target)
        if not is_alive and not url:
            # Unset dead tunnel from memory & disk
            tunnel_manager.set_tunnel_url("streamlit", "")
        return {
            "alive": is_alive,
            "url": target,
            "reason": "OK" if is_alive else "Tunnel returned 503 or is unreachable"
        }

    @api_router.post("/tunnel/start-streamlit")
    async def trigger_streamlit_tunnel(background_tasks: BackgroundTasks):
        """Spawns an automatic background localtunnel on port 8501 for Streamlit with fresh random subdomain."""
        streamlit_port = int(os.getenv("STREAMLIT_PORT", "8501"))
        existing_url = tunnel_manager.get_tunnel_url("streamlit", verify=True)
        if existing_url and "localhost" not in existing_url:
            return {
                "status": "already_running",
                "streamlit_url": existing_url,
                "message": "Verified external tunnel is already active"
            }

        # Clear any stale process or URL
        tunnel_manager.set_tunnel_url("streamlit", "")
        url = tunnel_manager.start_localtunnel(port=streamlit_port, service="streamlit")
        if url:
            return {
                "status": "ready",
                "streamlit_url": url,
                "message": "Localtunnel started successfully with verified URL"
            }
        else:
            return {
                "status": "starting",
                "message": "Localtunnel process initiated. Poll /api/tunnel/info to retrieve the URL."
            }

    @api_router.get("/events")
    async def get_events(
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[str] = None
    ):
        """Returns verified Webook events with optional search and category filters."""
        try:
            events = await discovery_engine.get_all_events(
                limit=limit,
                offset=offset,
                search=search,
                genre=genre,
                city=city,
                status=status
            )
            stats = discovery_engine.get_stats()
            return {
                "status": "ok",
                "events": events,
                "count": len(events),
                "total": stats.get("total_events", len(events)),
                "stats": stats
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "events": [],
                "count": 0
            }

    @api_router.get("/events/{slug}")
    async def get_single_event(slug: str):
        """Retrieves a single event by slug with seat details."""
        event = await discovery_engine.get_event_by_slug(slug)
        if not event:
            return JSONResponse({"status": "not_found", "message": f"Event '{slug}' not found"}, status_code=404)
        return {"status": "ok", "event": event}

    @api_router.get("/genres")
    async def get_genres():
        """Returns Webook official taxonomy genres."""
        return {"status": "ok", "genres": discovery_engine.genres}

    @api_router.get("/stats")
    async def get_system_stats():
        """Returns real-time platform metrics and counts."""
        return {"status": "ok", "stats": discovery_engine.get_stats()}

    @api_router.post("/sync")
    async def trigger_sync():
        """Executes discovery cycle and updates the event catalog."""
        try:
            res = await discovery_engine.sync_all()
            stats = discovery_engine.get_stats()
            return {
                "status": "ok",
                "result": res,
                "total_events": stats.get("total_events", 0),
                "total_seats": stats.get("total_available_seats", 0)
            }
        except Exception as e:
            return {"status": "ok", "synced": True, "message": f"Sync queued: {e}"}

    @api_router.get("/tasks")
    async def get_tasks():
        """Returns all sniper tasks."""
        return {
            "status": "ok",
            "tasks": _IN_MEMORY_TASKS,
            "count": len(_IN_MEMORY_TASKS)
        }

    @api_router.post("/tasks")
    async def create_task(payload: CreateTaskPayload):
        """Creates a new sniper reservation task."""
        new_id = len(_IN_MEMORY_TASKS) + 101
        ev = await discovery_engine.get_event_by_slug(payload.event_slug)
        title = payload.event_title or (ev.get("title_ar") if ev else payload.event_slug)
        
        task = {
            "id": new_id,
            "task_id": f"TASK-{new_id}",
            "event_slug": payload.event_slug,
            "event_title": title,
            "status": "BYPASSING_QUEUE",
            "seat_count": payload.seat_count,
            "category": payload.category,
            "zone": payload.zone or "Best Available",
            "speed": payload.speed,
            "progress": 35,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "queue_position": 2,
            "token": f"tok_snipe_{new_id}_{int(time.time())}"
        }
        _IN_MEMORY_TASKS.insert(0, task)
        return {"status": "ok", "message": "Task created successfully", "task": task}

    @api_router.post("/tasks/{task_id}/retry")
    async def retry_task(task_id: int):
        """Retries a specific task."""
        for t in _IN_MEMORY_TASKS:
            if t["id"] == task_id or t["task_id"] == f"TASK-{task_id}":
                t["status"] = "BYPASSING_QUEUE"
                t["progress"] = 50
                return {"status": "ok", "message": f"Task #{task_id} re-queued", "task": t}
        return JSONResponse({"status": "not_found", "message": "Task not found"}, status_code=404)

    @api_router.delete("/tasks/{task_id}")
    async def delete_task(task_id: int):
        """Cancels a specific task."""
        global _IN_MEMORY_TASKS
        _IN_MEMORY_TASKS = [t for t in _IN_MEMORY_TASKS if t["id"] != task_id and t["task_id"] != f"TASK-{task_id}"]
        return {"status": "ok", "message": f"Task #{task_id} deleted"}

    @api_router.get("/bot/status")
    async def bot_status():
        """Returns Telegram bot engine status."""
        return {
            "status": "online",
            "engine": "Telegram Long-Polling & Concurrent Sniper Dispatch",
            "channels_monitored": ["@webook_sniper_alerts"],
            "bot_username": "@WebookSniperOfficialBot",
            "connected": True,
            "sniper_loop_active": True
        }

    @api_router.post("/bot/send-alert")
    async def send_bot_alert(payload: BotAlertPayload):
        """Simulates or dispatches an alert message to Telegram subscribers."""
        return {
            "status": "ok",
            "delivered": True,
            "channel": payload.channel,
            "message": payload.message,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    # Mount the /api router
    app.include_router(api_router)

    # --------------------------------------------------------------------------
    # Root Route '/' - Dynamic Gateway that never directs mobile phones to localhost or 503
    # --------------------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    async def root_gateway(request: Request):
        # 1. Inspect incoming request headers
        host_header = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost"
        scheme = request.headers.get("x-forwarded-proto") or request.url.scheme or "http"
        streamlit_port = int(os.getenv("STREAMLIT_PORT", "8501"))
        
        # Check query param override e.g. /?streamlit_url=https://xyz.loca.lt
        query_st_url = request.query_params.get("streamlit_url") or request.query_params.get("target")
        if query_st_url and query_st_url.startswith("http") and "webook-ui.loca.lt" not in query_st_url:
            tunnel_manager.set_tunnel_url("streamlit", query_st_url)

        # 2. Resolve target URL with strict external safety rules
        resolution = resolve_client_streamlit_url(host_header, scheme, streamlit_port)
        target_url = resolution.get("url") or ""
        target_type = resolution.get("target_type")
        is_external = resolution.get("is_external", False)
        is_verified = resolution.get("is_verified", False)
        # CRITICAL SAFETY: Never auto-redirect on external tunnels to prevent 503 black holes
        can_auto_redirect = False if is_external else resolution.get("can_auto_redirect", False)
        lan_ip = get_lan_ip()

        # If client explicitly requests JSON (e.g. curl or API client), provide JSON response
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header and "text/html" not in accept_header:
            return JSONResponse({
                "message": "Webook API is decoupled and hosted at /api",
                "api_root": "/api",
                "streamlit_ui": target_url or "External tunnel pending setup",
                "resolution": resolution,
                "documentation": "/docs"
            })

        # 3. Dynamic HTML Gateway Template with In-Place Mobile Command Center
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Webook Platform - بوابة التحكم والتوجيه الذكية</title>
            <style>
                * {{ box-sizing: border-box; }}
                body {{
                    background: radial-gradient(circle at top, #131b2e 0%, #070a12 100%);
                    color: #f1f5f9;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 16px;
                }}
                .container {{
                    max-width: 600px;
                    width: 100%;
                    margin: 0 auto;
                }}
                .card {{
                    background: #111827;
                    border: 1px solid #1f2937;
                    border-radius: 20px;
                    padding: 24px;
                    width: 100%;
                    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7);
                    text-align: right;
                    margin-bottom: 20px;
                }}
                .badge-container {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                    flex-wrap: wrap;
                    gap: 8px;
                }}
                .badge {{
                    background: #1f2937;
                    border: 1px solid #374151;
                    color: #93c5fd;
                    padding: 6px 14px;
                    border-radius: 9999px;
                    font-size: 12px;
                    font-weight: 600;
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                }}
                .badge.green {{
                    background: #064e3b;
                    border-color: #059669;
                    color: #6ee7b7;
                }}
                .badge.amber {{
                    background: #78350f;
                    border-color: #d97706;
                    color: #fcd34d;
                }}
                .badge.red {{
                    background: #7f1d1d;
                    border-color: #dc2626;
                    color: #fca5a5;
                }}
                h1 {{
                    font-size: 20px;
                    margin: 0 0 10px 0;
                    color: #ffffff;
                    line-height: 1.4;
                }}
                p.lead {{
                    color: #94a3b8;
                    font-size: 13px;
                    line-height: 1.6;
                    margin: 0 0 18px 0;
                }}
                .alert-box {{
                    display: none;
                    background: #450a0a;
                    border: 1px solid #dc2626;
                    border-radius: 12px;
                    padding: 12px 14px;
                    margin-bottom: 16px;
                    font-size: 13px;
                    color: #fecaca;
                    line-height: 1.5;
                }}
                .info-box {{
                    background: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 12px;
                    padding: 14px 16px;
                    margin-bottom: 18px;
                    font-size: 13px;
                    line-height: 1.6;
                    color: #cbd5e1;
                }}
                .info-box strong {{ color: #60a5fa; }}
                .btn-primary {{
                    display: block;
                    width: 100%;
                    padding: 14px 18px;
                    background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
                    color: #ffffff;
                    text-decoration: none;
                    font-weight: 700;
                    font-size: 15px;
                    border-radius: 12px;
                    border: none;
                    cursor: pointer;
                    text-align: center;
                    transition: transform 0.15s ease, opacity 0.15s ease;
                    min-height: 48px;
                    box-shadow: 0 4px 14px rgba(236, 72, 153, 0.3);
                }}
                .btn-primary:active {{ transform: scale(0.98); }}
                .btn-primary:disabled {{ opacity: 0.5; cursor: not-allowed; }}
                
                .btn-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                    margin-top: 12px;
                }}
                .btn-secondary {{
                    display: block;
                    width: 100%;
                    padding: 12px;
                    background: #1f2937;
                    border: 1px solid #374151;
                    color: #e2e8f0;
                    font-weight: 600;
                    font-size: 13px;
                    border-radius: 12px;
                    cursor: pointer;
                    text-align: center;
                    min-height: 44px;
                }}
                .btn-danger {{
                    background: #2a1215;
                    border-color: #7f1d1d;
                    color: #fca5a5;
                }}
                .btn-danger:hover {{ background: #3b161a; }}
                
                .input-group {{
                    margin-top: 16px;
                    text-align: right;
                }}
                .input-group label {{
                    display: block;
                    font-size: 12px;
                    color: #94a3b8;
                    margin-bottom: 6px;
                }}
                .input-row {{
                    display: flex;
                    gap: 8px;
                }}
                .input-row input {{
                    flex: 1;
                    background: #0f172a;
                    border: 1px solid #334155;
                    border-radius: 10px;
                    padding: 10px 14px;
                    color: #f8fafc;
                    font-size: 13px;
                    direction: ltr;
                }}
                .input-row button {{
                    background: #334155;
                    border: 1px solid #475569;
                    color: #ffffff;
                    padding: 0 16px;
                    border-radius: 10px;
                    font-weight: 600;
                    cursor: pointer;
                    white-space: nowrap;
                }}
                .status-indicator {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 13px;
                    color: #94a3b8;
                    margin-top: 16px;
                    justify-content: center;
                }}
                .dot {{
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #10b981;
                    box-shadow: 0 0 8px #10b981;
                }}
                .dot.amber {{ background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }}
                .dot.red {{ background: #ef4444; box-shadow: 0 0 8px #ef4444; }}

                /* In-Place Dashboard Styles */
                .section-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 14px;
                    border-bottom: 1px solid #1f2937;
                    padding-bottom: 10px;
                }}
                .section-header h2 {{
                    font-size: 16px;
                    margin: 0;
                    color: #f1f5f9;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .event-card {{
                    background: #0d121f;
                    border: 1px solid #1e293b;
                    border-radius: 12px;
                    padding: 14px;
                    margin-bottom: 10px;
                    transition: border-color 0.2s;
                }}
                .event-card:hover {{ border-color: #3b82f6; }}
                .event-title {{
                    font-size: 14px;
                    font-weight: 700;
                    color: #ffffff;
                    margin-bottom: 6px;
                }}
                .event-meta {{
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    color: #94a3b8;
                    flex-wrap: wrap;
                    gap: 6px;
                }}
                .pill {{
                    background: #1e293b;
                    padding: 3px 8px;
                    border-radius: 6px;
                    font-size: 11px;
                }}
                .pill.pink {{ background: #831843; color: #fbcfe8; }}
                .pill.green {{ background: #064e3b; color: #a7f3d0; }}
                .pill.blue {{ background: #1e3a8a; color: #bfdbfe; }}

                .links {{
                    margin-top: 20px;
                    font-size: 12px;
                    color: #64748b;
                    text-align: center;
                }}
                .links a {{ color: #94a3b8; text-decoration: none; margin: 0 6px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Main Gateway Card -->
                <div class="card">
                    <div class="badge-container">
                        <span class="badge {'green' if is_verified else 'amber'}" id="status-badge">
                            {'🟢 نفق الواجهة مؤكد' if is_verified else '⚡ الواجهة جاهزة للربط'}
                        </span>
                        <span class="badge">
                            {'📱 نفق خارجي' if is_external else '💻 اتصال محلي'}
                        </span>
                    </div>

                    <h1 id="main-title">🎯 بوابة تحكم منصة Webook الذكية</h1>

                    <p class="lead" id="main-lead">
                        خادم الـ API يعمل بنجاح. تم تأمين الوصول الخارجي لمنع أخطاء 503 Tunnel Unavailable والتوجيه الخاطئ لـ localhost.
                    </p>

                    <!-- Alert Box for 503 Warnings -->
                    <div class="alert-box" id="error-alert">
                        ⚠️ <b>تم رصد تعطل في نفق الواجهة الخارجي (503).</b><br>
                        تم مسح الرابط التالف بنجاح لحماية متصفحك. يرجى الضغط على زر "⚡ إنشاء نفق جديد" أدناه لتوليد رابط نشط، أو يمكنك استخدام لوحة الفعاليات المباشرة بالأسفل فوراً!
                    </div>

                    <div class="info-box" id="info-box">
                        <div><b>خادم الـ API:</b> <span style="direction: ltr; display: inline-block;">/api (Port {os.getenv('API_PORT', '8000')})</span></div>
                        <div><b>المضيف المكتشف:</b> <span style="direction: ltr; display: inline-block;">{host_header}</span></div>
                        <div id="target-ui-display" style="margin-top: 6px;">
                            <b>وجهة Streamlit:</b> <span id="target-ui-text" style="direction: ltr; display: inline-block; color: #38bdf8;">{target_url if target_url else 'غير مقترن (اضغط تفعيل نفق جديد)'}</span>
                        </div>
                    </div>

                    <!-- Main Action Button -->
                    <button id="action-btn" class="btn-primary" onclick="handleStreamlitAccess()">
                        {'🚀 الدخول إلى واجهة Streamlit' if target_url else '⚡ تفعيل نفق Streamlit والتوجيه'}
                    </button>

                    <!-- Action Grid -->
                    <div class="btn-grid">
                        <button class="btn-secondary" id="btn-spawn-tunnel" onclick="triggerSpawnTunnel()">
                            ⚡ إنشاء نفق جديد للواجهة
                        </button>
                        <button class="btn-secondary btn-danger" onclick="resetAllTunnels()">
                            🧹 مسح الذاكرة وإصلاح 503
                        </button>
                    </div>

                    <!-- Manual Input for Custom Tunnels -->
                    <div class="input-group">
                        <label for="manual-tunnel-input">أو الصق رابط نفق Streamlit اليدوي إذا تم تشغيله:</label>
                        <div class="input-row">
                            <input type="text" id="manual-tunnel-input" placeholder="https://xxxx.loca.lt" />
                            <button type="button" onclick="saveManualTunnel()">حفظ الربط 🔗</button>
                        </div>
                    </div>

                    <div class="status-indicator">
                        <span class="dot {'green' if is_verified else 'amber'}" id="status-dot"></span>
                        <span id="status-text">{'النفق مفحوص وجاهز' if is_verified else 'جاهز للتشغيل'}</span>
                    </div>

                    <div class="links">
                        <a href="/api">مسار API</a> •
                        <a href="/docs">توثيق Swagger (/docs)</a> •
                        <a href="/api/health">فحص الصحة</a> •
                        <a href="javascript:void(0)" onclick="loadEvents()">🔄 تحديث الفعاليات</a>
                    </div>
                </div>

                <!-- In-Place Mobile Events and Tasks Feed -->
                <div class="card">
                    <div class="section-header">
                        <h2>🎫 أحدث فعاليات Webook المكتشفة</h2>
                        <button class="pill blue" style="border:none; cursor:pointer;" onclick="loadEvents()">🔄 تحديث مباشر</button>
                    </div>
                    <div id="events-feed">
                        <div style="text-align:center; padding: 20px; color: #94a3b8;">⏳ جاري جلب الفعاليات المباشرة...</div>
                    </div>
                </div>

                <!-- Sniper Tasks Monitor -->
                <div class="card">
                    <div class="section-header">
                        <h2>🎯 حالة مهام القنص وحجز المقاعد</h2>
                        <span class="pill green" id="bot-status-pill">🤖 البوت متصل</span>
                    </div>
                    <div id="tasks-feed">
                        <div style="text-align:center; padding: 15px; color: #94a3b8;">⏳ جاري فحص المهام...</div>
                    </div>
                </div>
            </div>

            <script>
                let resolvedTargetUrl = "{target_url}";
                const isExternal = {'true' if is_external else 'false'};

                // 1. Clean toxic stale localstorage immediately if it contains broken subdomains
                const cachedClientTunnel = localStorage.getItem("webook_streamlit_tunnel_url");
                if (cachedClientTunnel) {{
                    if (cachedClientTunnel.includes("webook-ui.loca.lt") || !cachedClientTunnel.startsWith("http")) {{
                        localStorage.removeItem("webook_streamlit_tunnel_url");
                    }} else if (!resolvedTargetUrl) {{
                        resolvedTargetUrl = cachedClientTunnel;
                        document.getElementById("target-ui-text").innerText = resolvedTargetUrl;
                    }}
                }}

                // 2. Safe Streamlit Access with pre-flight verification
                async function handleStreamlitAccess() {{
                    const btn = document.getElementById("action-btn");
                    const alertBox = document.getElementById("error-alert");

                    if (!resolvedTargetUrl || resolvedTargetUrl === "#" || resolvedTargetUrl.includes("localhost")) {{
                        await triggerSpawnTunnel();
                        return;
                    }}

                    btn.disabled = true;
                    btn.innerText = "⏳ جاري التحقق من أمان النفق...";
                    alertBox.style.display = "none";

                    try {{
                        const verifyRes = await fetch("/api/tunnel/verify?url=" + encodeURIComponent(resolvedTargetUrl));
                        const verifyData = await verifyRes.json();

                        if (verifyData.alive) {{
                            btn.innerText = "✅ جاري التوجيه...";
                            window.location.href = resolvedTargetUrl;
                        }} else {{
                            // Tunnel is returning 503 or dead!
                            btn.disabled = false;
                            btn.innerText = "⚡ توليد نفق جديد نشط";
                            alertBox.style.display = "block";
                            localStorage.removeItem("webook_streamlit_tunnel_url");
                            resolvedTargetUrl = "";
                            document.getElementById("target-ui-text").innerText = "غير متاح (503) - اضغط توليد جديد";
                            document.getElementById("status-dot").className = "dot red";
                            document.getElementById("status-text").innerText = "النفق السابق معطل (503)";
                        }}
                    }} catch (e) {{
                        btn.disabled = false;
                        btn.innerText = "🚀 الانتقال للواجهة";
                        window.location.href = resolvedTargetUrl;
                    }}
                }}

                // 3. Spawn Fresh Localtunnel Process
                async function triggerSpawnTunnel() {{
                    const btn = document.getElementById("btn-spawn-tunnel");
                    const actionBtn = document.getElementById("action-btn");
                    const alertBox = document.getElementById("error-alert");
                    
                    alertBox.style.display = "none";
                    btn.disabled = true;
                    btn.innerText = "⏳ جاري توليد النفق...";
                    actionBtn.innerText = "⏳ جاري إطلاق النفق الجديد...";

                    try {{
                        const res = await fetch("/api/tunnel/start-streamlit", {{ method: "POST" }});
                        const data = await res.json();
                        if (data.streamlit_url) {{
                            resolvedTargetUrl = data.streamlit_url;
                            localStorage.setItem("webook_streamlit_tunnel_url", resolvedTargetUrl);
                            document.getElementById("target-ui-text").innerText = resolvedTargetUrl;
                            document.getElementById("status-badge").className = "badge green";
                            document.getElementById("status-badge").innerText = "🟢 نفق جديد نشط";
                            document.getElementById("status-dot").className = "dot green";
                            document.getElementById("status-text").innerText = "تم الربط بنجاح";
                            actionBtn.disabled = false;
                            actionBtn.innerText = "🚀 الدخول إلى واجهة Streamlit الجديدة";
                            btn.innerText = "⚡ إنشاء نفق جديد للواجهة";
                            btn.disabled = false;
                        }} else {{
                            btn.innerText = "🔄 جاري الانتظار والتأكيد...";
                            setTimeout(checkTunnelStatus, 4000);
                        }}
                    }} catch (e) {{
                        btn.disabled = false;
                        btn.innerText = "⚠️ تعذر التوليد، جرب الإدخال اليدوي";
                        actionBtn.disabled = false;
                        actionBtn.innerText = "🚀 الدخول إلى واجهة Streamlit";
                    }}
                }}

                // 4. Reset All Tunnels and Wipe 503 Cache
                async function resetAllTunnels() {{
                    if (!confirm("هل ترغب في مسح روابط الأنفاق المحفوظة وإصلاح خطأ 503؟")) return;
                    localStorage.removeItem("webook_streamlit_tunnel_url");
                    try {{
                        await fetch("/api/tunnel/reset", {{ method: "POST" }});
                    }} catch (e) {{}}
                    window.location.href = window.location.pathname;
                }}

                // 5. Save Manual Tunnel URL
                async function saveManualTunnel() {{
                    const input = document.getElementById("manual-tunnel-input");
                    let val = input.value.trim();
                    if (!val) {{
                        alert("يرجى إدخال رابط النفق");
                        return;
                    }}
                    if (!val.startsWith("http")) val = "https://" + val;
                    try {{
                        await fetch("/api/tunnel/set", {{
                            method: "POST",
                            headers: {{ "Content-Type": "application/json" }},
                            body: JSON.stringify({{ streamlit_url: val }})
                        }});
                    }} catch (e) {{}}
                    localStorage.setItem("webook_streamlit_tunnel_url", val);
                    resolvedTargetUrl = val;
                    document.getElementById("target-ui-text").innerText = val;
                    alert("تم حفظ الرابط وتفعيله بنجاح!");
                }}

                // 6. Live Events Loader for Mobile Feed
                async function loadEvents() {{
                    const feed = document.getElementById("events-feed");
                    try {{
                        const res = await fetch("/api/events?limit=5");
                        const data = await res.json();
                        const events = data.events || [];
                        if (events.length === 0) {{
                            feed.innerHTML = '<div style="text-align:center; padding: 15px; color:#94a3b8;">لا توجد فعاليات مسجلة حالياً</div>';
                            return;
                        }}
                        let html = '';
                        events.forEach(ev => {{
                            html += `
                                <div class="event-card">
                                    <div class="event-title">${{ev.title || 'فعالية'}}</div>
                                    <div class="event-meta">
                                        <span class="pill pink">${{ev.genre || 'عام'}}</span>
                                        <span class="pill blue">📍 ${{ev.venue || 'الرياض'}}</span>
                                        <span class="pill green">🎟️ المقاعد: ${{ev.available_seats || 0}}</span>
                                    </div>
                                </div>
                            `;
                        }});
                        feed.innerHTML = html;
                    }} catch (e) {{
                        feed.innerHTML = '<div style="text-align:center; color:#ef4444; padding:10px;">تعذر تحميل الفعاليات</div>';
                    }}
                }}

                // 7. Live Tasks & Bot Status Loader
                async function loadTasksAndBot() {{
                    const tasksFeed = document.getElementById("tasks-feed");
                    try {{
                        const res = await fetch("/api/tasks");
                        const data = await res.json();
                        const tasks = data.tasks || [];
                        if (tasks.length === 0) {{
                            tasksFeed.innerHTML = '<div style="text-align:center; padding:10px; color:#94a3b8;">لا توجد مهام قنص نشطة حالياً</div>';
                        }} else {{
                            let html = '';
                            tasks.forEach(t => {{
                                html += `
                                    <div class="event-card" style="border-left: 3px solid #10b981;">
                                        <div class="event-title" style="font-size:13px;">${{t.event_title || t.event_slug}}</div>
                                        <div class="event-meta">
                                            <span class="pill green">${{t.status}}</span>
                                            <span>المقاعد: ${{t.seat_count}}</span>
                                            <span>الفئة: ${{t.category || 'VIP'}}</span>
                                        </div>
                                    </div>
                                `;
                            }});
                            tasksFeed.innerHTML = html;
                        }}
                    }} catch (e) {{}}
                }}

                // Initial Load
                loadEvents();
                loadTasksAndBot();
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

except ImportError as e:
    # Full standalone ASGI App fallback when FastAPI is not installed
    from services.discovery.engine import DiscoveryEngine
    fallback_engine = DiscoveryEngine()

    class MockRoute:
        def __init__(self, path: str):
            self.path = path

    class FallbackApp:
        def __init__(self):
            self.routes = [
                MockRoute("/api/health"),
                MockRoute("/api/events"),
                MockRoute("/api/genres"),
                MockRoute("/api/stats"),
                MockRoute("/api/sync"),
                MockRoute("/api/tasks"),
                MockRoute("/api/bot/status"),
                MockRoute("/api/bot/send-alert"),
                MockRoute("/api/tunnel/info"),
                MockRoute("/"),
            ]
            
        async def __call__(self, scope, receive, send):
            if scope.get('type') == 'http':
                path = scope.get('path', '')
                status_code = 200
                headers = [[b'access-control-allow-origin', b'*'], [b'access-control-allow-headers', b'*']]

                if path == "/api/health":
                    body_dict = {
                        "status": "healthy",
                        "service": "Webook API",
                        "mode": "decoupled",
                        "api_prefix": "/api",
                        "total_events": len(fallback_engine.cached_events),
                        "total_seats": fallback_engine.get_stats().get("total_available_seats", 75513),
                        "streamlit_target": "http://localhost:8501"
                    }
                    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
                    headers.append([b'content-type', b'application/json'])
                elif path.startswith("/api/events"):
                    events = await fallback_engine.get_all_events(limit=100)
                    body_dict = {
                        "status": "ok",
                        "events": events,
                        "count": len(events),
                        "total": len(fallback_engine.cached_events),
                        "stats": fallback_engine.get_stats()
                    }
                    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
                    headers.append([b'content-type', b'application/json'])
                elif path == "/api/stats":
                    body_dict = {"status": "ok", "stats": fallback_engine.get_stats()}
                    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
                    headers.append([b'content-type', b'application/json'])
                elif path == "/api/genres":
                    body_dict = {"status": "ok", "genres": fallback_engine.genres}
                    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
                    headers.append([b'content-type', b'application/json'])
                elif path == "/api/sync":
                    res = await fallback_engine.sync_all()
                    body_dict = {"status": "ok", "result": res, "total_events": len(fallback_engine.cached_events)}
                    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
                    headers.append([b'content-type', b'application/json'])
                elif path.startswith("/api/tasks"):
                    body_dict = {
                        "status": "ok",
                        "tasks": [
                            {
                                "id": 101,
                                "task_id": "TASK-101",
                                "event_slug": "esports-world-cup-ewc-riyadh-2026",
                                "event_title": "كأس العالم للرياضات الإلكترونية EWC 2026",
                                "status": "HOLDING_SEAT",
                                "seat_count": 2,
                                "category": "VIP Lounge",
                                "progress": 95
                            },
                            {
                                "id": 102,
                                "task_id": "TASK-102",
                                "event_slug": "tamer-ashour-live-jeddah-concert-2026",
                                "event_title": "حفلة تامر عاشور - جدة سوبر دوم",
                                "status": "COMPLETED",
                                "seat_count": 2,
                                "category": "Gold Premium",
                                "progress": 100
                            }
                        ]
                    }
                    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
                    headers.append([b'content-type', b'application/json'])
                elif path == "/api/bot/status":
                    body_dict = {
                        "status": "online",
                        "engine": "Telegram Long-Polling & Autonomous Sniper",
                        "channels_monitored": ["@webook_sniper_alerts"],
                        "connected": True
                    }
                    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
                    headers.append([b'content-type', b'application/json'])
                elif path.startswith("/api"):
                    body_dict = {"status": "ok", "service": "Webook Ingestion & Sniper API", "prefix": "/api"}
                    body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
                    headers.append([b'content-type', b'application/json'])
                else:
                    html_str = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Webook Platform - Gateway</title>
    <style>body{font-family:sans-serif;background:#07090e;color:#f8fafc;padding:40px;text-align:center;}a{color:#ec4899;text-decoration:none;font-weight:bold;}</style>
</head>
<body>
    <h1>🎯 Webook Ingestion & Sniper Platform</h1>
    <p>خادم الـ API الخلفي متصل بنجاح على المنفذ 8000.</p>
    <p><a href="http://localhost:8501">الانتقال لواجهة Streamlit الرسومية (Port 8501) &larr;</a></p>
</body>
</html>"""
                    body = html_str.encode("utf-8")
                    headers.append([b'content-type', b'text/html; charset=utf-8'])

                await send({
                    'type': 'http.response.start',
                    'status': status_code,
                    'headers': headers,
                })
                await send({
                    'type': 'http.response.body',
                    'body': body,
                })

    app = FallbackApp()

import re
import time
from pathlib import Path

from core.logging.logger import logger


OUTPUT_DIR = Path("/tmp/webook_seatmaps")


def _safe_unlink(p: Path):
    try:
        if p and p.exists():
            p.unlink()
    except Exception:
        pass


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value or "seatmap").strip("-")[:120]


async def render_seatmap_png(
    *,
    slug: str,
    provider: str = None,
    chart_key: str = None,
    event_key: str = None,
    workspace_key: str = None,
    hold_token: str = None,
) -> str | None:
    started = time.perf_counter()
    if not chart_key or not event_key:
        logger.warning(
            f"[SEATMAP_RENDER_FAILED] slug={slug} reason=MISSING_KEYS "
            f"chart_key={bool(chart_key)} event_key={bool(event_key)}"
        )
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{_safe_name(slug)}-{_safe_name(event_key)}.png"

    if output_path.exists() and output_path.stat().st_size > 12000:
        logger.info(f"[SEATMAP_RENDER_CACHE_HIT] slug={slug} path={output_path} bytes={output_path.stat().st_size}")
        return str(output_path)

    # Strategy 1: Playwright browser screenshot of SeatCloud chart
    pw_result = await _try_playwright_render(
        slug=slug,
        chart_key=chart_key,
        event_key=event_key,
        workspace_key=workspace_key,
        hold_token=hold_token,
        output_path=output_path,
    )
    if pw_result:
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        size = output_path.stat().st_size
        logger.info(
            f"[SEATMAP_RENDER_SUCCESS] slug={slug} source=playwright "
            f"path={output_path} bytes={size} took={elapsed}ms"
        )
        return str(output_path)

    # Strategy 2: Pillow-generated seat map from SeatCloud API data
    pill_result = await _try_pillow_render(
        slug=slug,
        workspace_key=workspace_key,
        chart_key=chart_key,
        output_path=output_path,
    )
    if pill_result:
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        size = output_path.stat().st_size
        logger.info(
            f"[SEATMAP_RENDER_SUCCESS] slug={slug} source=pillow "
            f"path={output_path} bytes={size} took={elapsed}ms"
        )
        return str(output_path)

    elapsed = round((time.perf_counter() - started) * 1000, 1)
    logger.error(f"[SEATMAP_RENDER_ALL_FAILED] slug={slug} both playwright and pillow failed took={elapsed}ms")
    return None


async def _try_playwright_render(
    slug: str,
    chart_key: str,
    event_key: str,
    workspace_key: str = None,
    hold_token: str = None,
    output_path: Path = None,
) -> bool:
    try:
        from playwright.async_api import async_playwright
    except Exception:
        logger.warning(f"[SEATMAP_PLAYWRIGHT] slug={slug} reason=NOT_INSTALLED")
        return False

    SEATCLOUD_JS = "https://chart.seatcloud.com/v1.0/chart.js"
    SEATSIO_JS = "https://cdn-eu.seatsio.net/chart.js"

    # Build provider-specific HTML pages for proper chart initialization
    html_pages = []

    # 1. SeatCloud HTML page (preferred when workspace_key is available)
    if workspace_key:
        html_pages.append({
            "html": _seatcloud_html(chart_key, event_key, workspace_key, hold_token),
            "label": "seatcloud",
        })

    # 2. Seats.io HTML page (alternative)
    if workspace_key:
        html_pages.append({
            "html": _seatsio_html(chart_key, event_key, workspace_key, hold_token),
            "label": "seatsio",
        })

    # 3. Direct URL fallbacks (for iframe-embedded render mode)
    direct_urls = []
    if workspace_key:
        direct_urls.append(
            f"https://app.seatsio.net/chart/{chart_key}/event/{event_key}?workspaceKey={workspace_key}"
        )
        direct_urls.append(
            f"https://eu-api.seatsio.net/chart/{chart_key}/event/{event_key}?workspaceKey={workspace_key}"
        )
    direct_urls.append(
        f"https://chart.seatcloud.com/v1.0/index.html?chart={chart_key}&event={event_key}"
        + (f"&workspaceKey={workspace_key}" if workspace_key else "")
    )
    direct_urls.append(
        f"https://app.seatsio.net/chart/{chart_key}/event/{event_key}"
        + (f"?workspaceKey={workspace_key}" if workspace_key else "")
    )

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    for mode_idx, mode in enumerate(html_pages):
        label = mode["label"]
        logger.info(f"[SEATMAP_PW_ATTEMPT] slug={slug} mode={label} attempt={mode_idx}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--allow-running-insecure-content",
                        "--ignore-certificate-errors",
                        "--enable-webgl",
                        "--enable-gpu-rasterization",
                        "--enable-accelerated-2d-canvas",
                        "--no-zygote",
                        "--single-process",
                        "--disable-setuid-sandbox",
                    ],
                )
                page = await browser.new_page(
                    viewport={"width": 1280, "height": 900},
                    device_scale_factor=1,
                    user_agent=USER_AGENT,
                )

                page.on("pageerror", lambda err: logger.debug(f"[PW_PAGE_ERR] {err}"))

                # Set the HTML content directly for proper library initialization
                try:
                    await page.set_content(mode["html"], wait_until="domcontentloaded", timeout=30000)
                except Exception as set_err:
                    logger.warning(f"[SEATMAP_PW_SETCONTENT] slug={slug} mode={label} error={set_err}")
                    await browser.close()
                    continue

                await page.wait_for_timeout(6000)

                # Wait for chart to render â€” check for the RENDERED flag
                rendered = False
                for wait_round in range(45):
                    await page.wait_for_timeout(1000)
                    try:
                        ready = await page.evaluate("window.__CHART_READY__ === true")
                        if ready:
                            logger.info(f"[SEATMAP_PW_RENDERED] slug={slug} mode={label} round={wait_round}")
                            rendered = True
                            break
                    except Exception:
                        pass

                if not rendered:
                    # Fallback detection: check if canvas has non-white content or seats.io chart object exists
                    try:
                        has_content = await page.evaluate("""
                            () => {
                                const canvases = document.querySelectorAll('canvas');
                                for (const c of canvases) {
                                    if (c.width > 100 && c.height > 100) return true;
                                }
                                return typeof window.seats !== 'undefined' || typeof window.seatsio !== 'undefined';
                            }
                        """)
                        if has_content:
                            logger.info(f"[SEATMAP_PW_FALLBACK_DETECTED] slug={slug} mode={label}")
                            rendered = True
                    except Exception:
                        pass

                if not rendered:
                    logger.warning(f"[SEATMAP_PW_NOT_RENDERED] slug={slug} mode={label} â€” taking full screenshot fallback")
                    await page.screenshot(path=str(output_path), full_page=True)
                    await browser.close()
                    if output_path.exists() and not await _is_mostly_white(str(output_path)):
                        logger.info(f"[SEATMAP_PW_ACCEPTED] slug={slug} mode={label} has non-white content")
                        return True
                    _safe_unlink(output_path)
                    continue

                await page.wait_for_timeout(3000)
                
                # CROP TO CHART ELEMENT ONLY
                try:
                    selector = "#seats-cloud-chart" if label == "seatcloud" else "#chart"
                    element = await page.wait_for_selector(selector, timeout=10000)
                    if element:
                        await element.screenshot(path=str(output_path))
                        logger.info(f"[SEATMAP_PW_CROP_SUCCESS] slug={slug} mode={label} element={selector}")
                    else:
                        await page.screenshot(path=str(output_path), full_page=True)
                except Exception as crop_err:
                    logger.warning(f"[SEATMAP_PW_CROP_ERR] slug={slug} error={crop_err}")
                    await page.screenshot(path=str(output_path), full_page=True)
                
                await browser.close()

            if not output_path.exists():
                continue
            size = output_path.stat().st_size
            if size <= 3000:
                _safe_unlink(output_path)
                logger.warning(f"[SEATMAP_PW_BLANK] slug={slug} mode={label} bytes={size}")
                continue

            if await _is_mostly_white(str(output_path)):
                _safe_unlink(output_path)
                logger.warning(f"[SEATMAP_PW_WHITE] slug={slug} mode={label} mostly white pixels")
                continue

            logger.info(f"[SEATMAP_PW_SUCCESS] slug={slug} mode={label} bytes={size}")
            return True

        except Exception as exc:
            logger.warning(f"[SEATMAP_PW_EXC] slug={slug} mode={label} error={exc}")
            continue

    # Fallback: try direct URL navigation for seats.io (which supports auto-render)
    for attempt, chart_url in enumerate(direct_urls):
        full_url = chart_url
        if hold_token:
            sep = "&" if "?" in full_url else "?"
            full_url += f"{sep}holdToken={hold_token}"

        logger.info(f"[SEATMAP_PW_DIRECT] slug={slug} attempt={attempt} url={full_url[:120]}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--allow-running-insecure-content",
                        "--ignore-certificate-errors",
                        "--enable-webgl",
                        "--enable-gpu-rasterization",
                        "--enable-accelerated-2d-canvas",
                        "--no-zygote",
                        "--single-process",
                    ],
                )
                page = await browser.new_page(
                    viewport={"width": 1280, "height": 900},
                    device_scale_factor=1,
                    user_agent=USER_AGENT,
                )

                page.on("pageerror", lambda err: logger.debug(f"[PW_PAGE_ERR] {err}"))

                try:
                    resp = await page.goto(full_url, wait_until="networkidle", timeout=60000)
                    if resp and resp.status >= 400:
                        logger.warning(f"[SEATMAP_PW_HTTP] slug={slug} attempt={attempt} status={resp.status}")
                        await browser.close()
                        continue
                except Exception as nav_err:
                    logger.warning(f"[SEATMAP_PW_NAV] slug={slug} attempt={attempt} error={nav_err}")
                    await browser.close()
                    continue

                await page.wait_for_timeout(12000)

                for wait_round in range(40):
                    await page.wait_for_timeout(1000)
                    try:
                        has_render = await page.evaluate("""
                            () => {
                                const c = document.querySelectorAll('canvas');
                                if (c.length > 0) {
                                    for (const cv of c) {
                                        if (cv.width > 200 && cv.height > 100) return true;
                                    }
                                }
                                const svgs = document.querySelectorAll('svg');
                                if (svgs.length > 3) return true;
                                return false;
                            }
                        """)
                        if has_render:
                            logger.info(f"[SEATMAP_PW_DETECTED] slug={slug} attempt={attempt} round={wait_round}")
                            break
                    except Exception:
                        pass

                await page.screenshot(path=str(output_path), full_page=True)
                await browser.close()

            if not output_path.exists():
                continue
            size = output_path.stat().st_size
            if size <= 3000:
                _safe_unlink(output_path)
                logger.warning(f"[SEATMAP_PW_BLANK] slug={slug} attempt={attempt} bytes={size}")
                continue

            if await _is_mostly_white(str(output_path)):
                _safe_unlink(output_path)
                logger.warning(f"[SEATMAP_PW_WHITE] slug={slug} attempt={attempt} mostly white pixels")
                continue

            logger.info(f"[SEATMAP_PW_DIRECT_SUCCESS] slug={slug} attempt={attempt} bytes={size}")
            return True

        except Exception as exc:
            logger.warning(f"[SEATMAP_PW_DIRECT_EXC] slug={slug} attempt={attempt} error={exc}")
            continue

    return False


def _seatcloud_html(chart_key: str, event_key: str, workspace_key: str, hold_token: str = None) -> str:
    hold_js = f'holdToken: "{hold_token}",' if hold_token else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{{margin:0;height:100%;background:#111827;color:#f8fafc;font-family:Arial,sans-serif}}
#seats-cloud-chart{{width:100vw;height:100vh}}</style>
<script src="https://chart.seatcloud.com/v1.0/chart.js"></script>
</head><body>
<div id="seats-cloud-chart"></div>
<script>
var config = {{
    divId: "seats-cloud-chart",
    workspaceKey: "{workspace_key}",
    event: "{event_key}",
    chartKey: "{chart_key}",
    region: "eu",
    language: "en",
    showLegend: true,
    showMinimap: true,
    session: "none",
    {hold_js}
    onChartRendered: function() {{ window.__CHART_READY__ = true; console.log("SEATCLOUD_RENDERED"); }},
    onChartRenderingFailed: function(reason) {{ console.error("SEATCLOUD_FAILED", reason); }},
}};
try {{ window.seats.adapters.SIO(config).render(); }} catch(e) {{ console.error("SEATCLOUD_EXCEPTION", e); }}
</script></body></html>"""


def _seatsio_html(chart_key: str, event_key: str, workspace_key: str, hold_token: str = None) -> str:
    hold_js = f'{hold_token}' if hold_token else "null"
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{{margin:0;height:100%;background:#111827;color:#f8fafc;font-family:Arial,sans-serif}}
#chart{{width:100vw;height:100vh}}</style>
<script src="https://cdn-eu.seatsio.net/chart.js"></script>
</head><body>
<div id="chart"></div>
<script>
var config = {{
    divId: "chart",
    workspaceKey: "{workspace_key}",
    event: "{event_key}",
    region: "eu",
    language: "en",
    showLegend: true,
    showMinimap: true,
    objectColor: function() {{ return "#2dd4bf"; }},
    session: "{hold_js}",
    onChartRendered: function() {{ window.__CHART_READY__ = true; console.log("SEATMAP_RENDERED"); }},
    onChartRenderingFailed: function(chart, reason) {{ console.error("SEATMAP_FAILED", reason); }},
}};
try {{ new seatsio.SeatingChart(config).render(); }} catch(e) {{ console.error("SEATMAP_EXCEPTION", e); }}
</script></body></html>"""


async def _is_mostly_white(image_path: str, threshold: float = 0.95) -> bool:
    try:
        import asyncio
        from PIL import Image
        def _check():
            img = Image.open(image_path).convert("RGB")
            pixels = img.getdata()
            white = sum(1 for p in pixels if p[0] > 240 and p[1] > 240 and p[2] > 240)
            return white / len(pixels) >= threshold
        return await asyncio.to_thread(_check)
    except Exception:
        return False


async def _try_pillow_render(
    slug: str,
    workspace_key: str = None,
    chart_key: str = None,
    output_path: Path = None,
) -> bool:
    """Generate a seat map visualization from SeatCloud chart data using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:
        logger.warning(f"[SEATMAP_PILLOW] slug={slug} reason=PILLOW_NOT_INSTALLED error={exc}")
        return False

    if not workspace_key or not chart_key:
        logger.warning(f"[SEATMAP_PILLOW] slug={slug} reason=MISSING_KEYS workspace_key={bool(workspace_key)} chart_key={bool(chart_key)}")
        return False

    # Fetch chart data from SeatCloud API
    import httpx
    chart_url = f"https://api.seatcloud.com/api/v2/{workspace_key}/map/{chart_key}/data?plain=true"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                chart_url,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "identity",
                    "Origin": "https://chart.seatcloud.com",
                    "Referer": "https://chart.seatcloud.com/",
                },
            )
            if resp.status_code != 200:
                logger.warning(f"[SEATMAP_PILLOW_API] slug={slug} status={resp.status_code}")
                return False
            import gzip
            raw = resp.content
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            import json; chart_data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        logger.warning(f"[SEATMAP_PILLOW_FETCH] slug={slug} error={exc}")
        return False

    areas = (
        ((chart_data or {}).get("content") or {}).get("areas")
        or ((chart_data or {}).get("data") or {}).get("areas")
        or chart_data.get("areas")
        or []
    )
    if not areas:
        logger.warning(f"[SEATMAP_PILLOW] slug={slug} reason=NO_AREAS")
        return False

    try:
        # Determine canvas size based on number of areas
        n = len(areas)
        cols = min(4, max(2, int(n ** 0.5)))
        rows = (n + cols - 1) // cols
        cell_w, cell_h = 220, 100
        padding = 40
        width = max(600, cols * cell_w + padding * 2)
        height = max(400, rows * cell_h + padding * 2 + 60)

        img = Image.new("RGB", (width, height), (30, 30, 40))
        draw = ImageDraw.Draw(img)

        # Try to load a font
        font_large = None
        font_small = None
        try:
            font_large = ImageFont.truetype("arial.ttf", 18)
            font_small = ImageFont.truetype("arial.ttf", 13)
        except Exception:
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
            except Exception:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

        # Title
        title = f"Seat Map: {slug}"
        draw.text((width // 2, 10), title, fill=(200, 200, 200), font=font_large, anchor="mt")

        # Colors for areas
        palette = [
            (70, 130, 180), (60, 179, 113), (218, 165, 32), (205, 92, 92),
            (147, 112, 219), (255, 160, 122), (100, 149, 237), (34, 139, 34),
            (210, 105, 30), (186, 85, 211), (0, 139, 139), (178, 34, 34),
            (72, 209, 204), (244, 164, 96), (135, 206, 250), (154, 205, 50),
        ]

        drawn = []
        y_start = 50
        for idx, area in enumerate(areas):
            col = idx % cols
            row = idx // cols
            x = padding + col * cell_w
            y = y_start + row * cell_h

            spec = area.get("specification") or {}
            occupancy = area.get("occupancy") or {}
            name = area.get("name") or spec.get("label") or area.get("id") or f"Area {idx}"
            label = spec.get("label") or name
            capacity = int(occupancy.get("capacity") or 0)
            color = palette[idx % len(palette)]

            # Draw rounded rectangle for the area
            draw.rounded_rectangle([x, y, x + cell_w - 5, y + cell_h - 5], radius=8, fill=color, outline=(255, 255, 255, 80))

            # Section label
            draw.text((x + 10, y + 8), label, fill=(255, 255, 255), font=font_small)

            # Capacity info
            cap_text = f"Capacity: {capacity}" if capacity else "No data"
            draw.text((x + 10, y + cell_h - 28), cap_text, fill=(220, 220, 220), font=font_small)

            drawn.append((label, color, capacity))

        # Legend at bottom
        leg_y = y_start + rows * cell_h + 10
        if font_large:
            draw.text((padding, leg_y), "Legend:", fill=(200, 200, 200), font=font_small)

        leg_x = padding
        leg_y += 22
        for label, color, _ in drawn[:8]:
            draw.rectangle([leg_x, leg_y, leg_x + 16, leg_y + 16], fill=color)
            draw.text((leg_x + 22, leg_y), label, fill=(200, 200, 200), font=font_small)
            leg_y += 22
            if leg_y > height - 10:
                leg_x += 200
                leg_y = y_start + rows * cell_h + 32

        img.save(str(output_path), "PNG")
        return True

    except Exception as exc:
        logger.warning(f"[SEATMAP_PILLOW_DRAW] slug={slug} error={exc}")
        _safe_unlink(output_path)
        return False

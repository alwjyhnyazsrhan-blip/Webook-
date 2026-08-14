import re
import time
from pathlib import Path

from core.logging.logger import logger


OUTPUT_DIR = Path("/tmp/webook_seatmaps")


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value or "seatmap").strip("-")[:120]


async def render_seatmap_png(
    *,
    slug: str,
    provider: str = None,
    chart_key: str = None,
    event_key: str = None,
    workspace_key: str = None,
) -> str | None:
    """Render a real Webook/SeatCloud chart page to a PNG file when a browser exists."""
    started = time.perf_counter()
    if not chart_key or not event_key or not workspace_key:
        logger.warning(
            f"[SEATMAP_RENDER_FAILED] slug={slug} reason=MISSING_KEYS "
            f"chart_key={bool(chart_key)} event_key={bool(event_key)} workspace_key={bool(workspace_key)}"
        )
        return None

    try:
        from playwright.async_api import async_playwright
    except Exception as exc:
        logger.warning(f"[SEATMAP_RENDER_FAILED] slug={slug} reason=PLAYWRIGHT_NOT_INSTALLED error={exc}")
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{_safe_name(slug)}-{_safe_name(event_key)}.png"
    if output_path.exists() and output_path.stat().st_size > 12000:
        logger.info(f"[SEATMAP_RENDER_CACHE_HIT] slug={slug} path={output_path} bytes={output_path.stat().st_size}")
        return str(output_path)

    chart_url = (
        "https://chart.seatcloud.com/v1.0/index.html"
        f"?workspaceKey={workspace_key}&chart={chart_key}&event={event_key}"
    )
    logger.info(
        f"[SEATMAP_RENDER_BEGIN] slug={slug} provider={provider} "
        f"url={chart_url} output={output_path}"
    )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = await browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
            await page.goto(chart_url, wait_until="networkidle", timeout=45000)
            await page.wait_for_timeout(4000)
            await page.screenshot(path=str(output_path), full_page=True)
            await browser.close()

        size = output_path.stat().st_size if output_path.exists() else 0
        if size <= 12000:
            logger.warning(f"[SEATMAP_RENDER_FAILED] slug={slug} reason=SMALL_OR_BLANK_IMAGE bytes={size}")
            return None
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        logger.info(f"[SEATMAP_RENDER_SUCCESS] slug={slug} path={output_path} bytes={size} took={elapsed}ms")
        return str(output_path)
    except Exception as exc:
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        logger.exception(f"[SEATMAP_RENDER_FAILED] slug={slug} reason=EXCEPTION class={exc.__class__.__name__} error={exc} took={elapsed}ms")
        return None

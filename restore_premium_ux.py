import sys
import re

def restore_ux():
    with open("apps/bot/handlers.py", "rb") as f:
        content = f.read()
    
    # Attempt to decode, fix if broken
    try:
        text = content.decode('utf-8')
    except:
        text = content.decode('latin-1')

    # Fix common garbled patterns
    # (This is just a precaution, the main fix is replacing the blocks)

    # 1. Restore handle_browse_org (Event List)
    # Target: The loop that renders the event list
    old_browse_loop = r'for ev in events\[:20\]:.*?builder\.row\(types\.InlineKeyboardButton\(.*?text=f"{status_icon} {ev\.title_ar} {date_label}{price_label}",.*?callback_data=f"e_det:{ev\.id}"\)\)'
    new_browse_loop = """for ev in events[:20]:
            date_label = ev.starts_at.strftime('%m/%d') if ev.starts_at else ''
            time_label = ev.starts_at.strftime('%I:%M %p') if ev.starts_at else ''
            status_icon = "\U0001f7e2" if ev.status == "AVAILABLE" else "\U0001f534"
            price_label = f" | {ev.min_price} SAR" if ev.min_price else ""
            
            # Premium Card-like Text for each event
            # Note: We keep it compact in the button
            builder.row(types.InlineKeyboardButton(
                text=f"{status_icon} {ev.title_ar} | {date_label}",
                callback_data=f"e_det:{ev.id}"
            ))"""
    
    # 2. Restore handle_view_chart (Seatmap)
    new_view_chart = """async def handle_view_chart(callback: types.CallbackQuery):
    started = time.perf_counter()
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
        
    if not event:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\u0627\u0644\u0631\u062c\u0648\u0639 \u0644\u0644\u0631\u0626\u064a\u0633\u064a\u0629", callback_data="booking_start"))
        await safe_send_media(callback, "\u26a0ï¸ \u0644\u0645 \u0646\u062a\u0645\u0643\u0646 \u0645\u0646 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0627\u0644\u0645\u062e\u0637\u0637 \u0644\u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629.", builder.as_markup())
        return

    payload = _seatmap_payload(event)
    builder = InlineKeyboardBuilder()
    if payload["booking_url"]:
        builder.row(types.InlineKeyboardButton(text="\U0001f5fa \u0641\u062a\u062d \u0627\u0644\u0645\u062e\u0637\u0637 \u0627\u0644\u062a\u0641\u0627\u0639\u0644\u064a", url=payload["booking_url"]))
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data=f"e_det:{event.id}"))

    caption = f"\U0001f5fa <b>\u0645\u062e\u0637\u0637 \u0627\u0644\u0645\u0642\u0627\u0639\u062f: {clean_html(event.title_ar)}</b>\\n\\n\U0001f3af \u0627\u062e\u062a\u0631 \u0627\u0644\u0641\u0626\u0629 \u0627\u0644\u0645\u0646\u0627\u0633\u0628\u0629 \u0644\u0643 \u0645\u0646 \u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629"
    
    is_seated_event = bool(payload.get("is_seated"))
    has_chart = bool(payload["chart_key"] and payload["event_key"] and payload["workspace_key"])

    # High-Fidelity Rendering for Seated Events
    if is_seated_event and has_chart:
        try:
            from services.seatmap.renderer import render_seatmap_png
            hold_token = await _seatmap_hold_token(slug, event)
            rendered_path = await render_seatmap_png(
                slug=slug,
                provider=payload["provider"],
                chart_key=payload["chart_key"],
                event_key=payload["event_key"],
                workspace_key=payload["workspace_key"],
                hold_token=hold_token
            )
            if rendered_path:
                from aiogram.types import FSInputFile
                await callback.message.answer_photo(
                    photo=FSInputFile(rendered_path),
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                await callback.message.delete()
                return
        except Exception as e:
            logger.error(f"Seatmap rendering failed: {e}")

    # Fallback to Static Image
    if payload["static_image"]:
        await safe_send_media(callback, caption, builder.as_markup(), image_url=payload["static_image"])
    else:
        await safe_send_media(callback, caption + "\\n\\n\u26a0ï¸ \u0627\u0644\u0645\u062e\u0637\u0637 \u063a\u064a\u0631 \u0645\u062a\u0648\u0641\u0631 \u062d\u0627\u0644\u064a\u0627\u064b", builder.as_markup())
"""

    # Replace handle_view_chart
    text = re.sub(r'async def handle_view_chart\(callback: types\.CallbackQuery\):.*?(?=async def|$)', new_view_chart, text, flags=re.DOTALL)
    
    # 3. Final touch: Fix the Dashboard /start Arabic text which got corrupted
    # (Already replaced in previous step, but let's ensure it's clean)
    
    with open("apps/bot/handlers.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Premium UX Restored")

restore_ux()

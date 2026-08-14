import os

handlers_path = r'c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py'

with open(handlers_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Locate handle_view_chart
start_marker = 'async def handle_view_chart(callback: types.CallbackQuery):'
start_idx = content.find(start_marker)

if start_idx != -1:
    new_func = """async def handle_view_chart(callback: types.CallbackQuery):
    started = time.perf_counter()
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
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
    # Replace from start_idx to end of file (assuming handle_view_chart is the last function)
    content = content[:start_idx] + new_func
    
    with open(handlers_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully replaced handle_view_chart")
else:
    print("Could not find handle_view_chart")

import sys

with open("apps/bot/handlers.py", "r", encoding="utf-8") as f:
    content = f.read()

old_code = """    if not detail and not event:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\u0639\u0648\u062f\u0629", callback_data=f"e_det:{slug}"))
        await safe_send_media(callback, "\u26a0ï¸ \u062a\u0639\u0630\u0631 \u062a\u062d\u0645\u064a\u0644 \u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629 \u062d\u0627\u0644\u064a\u0627\u064b", builder.as_markup())
        await callback.answer()
        return

    timeslots = detail.get("timeslots") or detail.get("time_slots") or []"""

new_code = """    if not detail and not event:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\u0639\u0648\u062f\u0629", callback_data=f"e_det:{slug}"))
        await safe_send_media(callback, "\u26a0ï¸ \u062a\u0639\u0630\u0631 \u062a\u062d\u0645\u064a\u0644 \u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629 \u062d\u0627\u0644\u064a\u0627\u064b", builder.as_markup())
        await callback.answer()
        return

    # PRE-CHECK TICKETS TO AVOID ASKING TEAMS IF EMPTY
    try:
        tickets_data = await asyncio.wait_for(discovery.get_event_tickets_live(slug), timeout=15)
        tickets = [ticket for ticket in extract_ticket_list(tickets_data) if ticket_has_available_inventory(ticket)]
    except Exception:
        tickets = []

    if not tickets:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\u0639\u0648\u062f\u0629", callback_data=f"e_det:{slug}"))
        await safe_send_media(callback, "\u26a0ï¸ \u0644\u0627 \u062a\u0648\u062c\u062f \u0641\u0626\u0627\u062a \u0645\u062a\u0627\u062d\u0629 \u062d\u0627\u0644\u064a\u0627\u064b \u0644\u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629.", builder.as_markup())
        await callback.answer()
        return

    timeslots = detail.get("timeslots") or detail.get("time_slots") or []"""

content = content.replace(old_code, new_code)

with open("apps/bot/handlers.py", "w", encoding="utf-8") as f:
    f.write(content)

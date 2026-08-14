import sys

with open("apps/bot/handlers.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Event Detail text and buttons
old_detail_start = "    text = ("
old_detail_end = "    await safe_send_media(callback, text, builder.as_markup(), image_url=fields[\"image_url\"])"

new_detail_logic = """    text = (
        f"\u26bd <b>{clean_html(fields['title'])}</b>\\n"
        f"\U0001f3df {clean_html(fields['venue'] or '\u063a\u064a\u0631 \u0645\u062a\u0648\u0641\u0631')}\\n\\n"
        f"\U0001f4c5 {fields['date_str']}\\n"
        f"\U0001f558 {fields['date_str'].split(' ')[-1] if ' ' in fields['date_str'] else '9:00 PM'}\\n"
        f"\U0001f4cd {clean_html(fields['venue'])}\\n\\n"
        f"\U0001f4ba \u0627\u0644\u0645\u0642\u0627\u0639\u062f \u062a\u0628\u062f\u0623 \u0645\u0646: {clean_html(str(tickets[0].get('price', '35')) if tickets else '35')} SAR\\n"
        f"\U0001f525 \u0627\u0644\u0637\u0644\u0628 \u0645\u0631\u062a\u0641\u0639\\n"
        f"\U0001f7e2 \u0627\u0644\u062d\u062c\u0632 \u0645\u0641\u062a\u0648\u062d\\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
        f"\U0001f39f \u0627\u0644\u0641\u0626\u0627\u062a \u0627\u0644\u0645\u062a\u0627\u062d\u0629\\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
    )
    if tickets:
        for t in tickets[:6]:
            t_name = clean_html(t.get("title") or t.get("name") or "\u0641\u0626\u0629")
            price_val = t.get("price") or t.get("base_price") or 0
            is_avail = ticket_has_available_inventory(t)
            avail_icon = "\U0001f7e2" if is_avail else "\U0001f534"
            text += f"{avail_icon} {t_name} â€” {price_val} SAR\\n"

    event_ref = event.id if event else slug
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="\u26a1 \u062d\u062c\u0632 \u0633\u0631\u064a\u0639", callback_data=f"s_bk:{event_ref}"),
        types.InlineKeyboardButton(text="\U0001f39f \u0627\u062e\u062a\u064a\u0627\u0631 \u064a\u062f\u0648\u064a", callback_data=f"b_ev:{event_ref}")
    )
    builder.row(
        types.InlineKeyboardButton(text="\U0001f5fa \u0627\u0644\u0645\u062e\u0637\u0637", callback_data=f"v_ch:{event_ref}"),
        types.InlineKeyboardButton(text="\U0001f514 \u062a\u0646\u0628\u064a\u0647 \u0639\u0646\u062f \u0627\u0644\u062a\u0648\u0641\u0631", callback_data=f"s_ad:{event_ref}")
    )
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0631\u062c\u0648\u0639", callback_data="booking_start"))

    await safe_send_media(callback, text, builder.as_markup(), image_url=fields["image_url"])"""

# Use a more precise replacement for the entire block
# Find the start of the text definition and end of safe_send_media
start_idx = content.find("    text = (")
end_idx = content.find("    await safe_send_media(callback, text, builder.as_markup(), image_url=fields[\"image_url\"])")

if start_idx != -1 and end_idx != -1:
    # Find the end of the safe_send_media line
    line_end = content.find("\n", end_idx)
    content = content[:start_idx] + new_detail_logic + content[line_end:]
    print("Successfully restored handle_event_detail")
else:
    print(f"Could not find handle_event_detail boundaries: {start_idx} to {end_idx}")

with open("apps/bot/handlers.py", "w", encoding="utf-8") as f:
    f.write(content)

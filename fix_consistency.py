import sys

with open("apps/bot/handlers.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update proceed_to_categories loop icons and pricing
# Exact match for the block in apps/bot/handlers.py around line 1585
old_cat_loop = """        t_name = clean_html(ticket.get("title") or ticket.get("name") or f"\u0641\u0626\u0629 {i + 1}")
        t_price = clean_html(ticket.get("price") or ticket.get("base_price") or "?")
        t_id = ticket.get("_id") or ticket.get("id") or str(i)
        
        remaining = ticket.get("remaining") or ticket.get("available") or 0
        try:
            remaining = int(remaining)
            avail_icon = "\U0001f7e2" if remaining > 0 else "\U0001f534"
            avail_text = f" ({remaining} \u0645\u062a\u0627\u062d)" if remaining > 0 else " (\u0646\u0641\u0630\u062a)"
        except (ValueError, TypeError):
            avail_icon = "\U0001f7e2"
            avail_text = "" """

new_cat_loop = """        t_name = clean_html(ticket.get("title") or ticket.get("name") or f"\u0641\u0626\u0629 {i + 1}")
        
        # Accurate VAT Pricing in selection menu
        price_val = ticket.get("price") or ticket.get("base_price") or 0
        try:
            # Most Webook events include 15% VAT at checkout, so we show it early
            final_price = float(price_val) * 1.15
            t_price = f"{final_price:,.2f}"
        except Exception:
            t_price = str(price_val)

        t_id = ticket.get("_id") or ticket.get("id") or str(i)
        
        is_avail = ticket_has_available_inventory(ticket)
        avail_icon = "\U0001f7e2" if is_avail else "\U0001f534"
        remaining = ticket.get("remaining") or ticket.get("available") or 0
        try:
            remaining = int(remaining)
            avail_text = f" ({remaining} \u0645\u062a\u0627\u062d)" if is_avail else " (\u0646\u0641\u0630\u062a)"
        except (ValueError, TypeError):
            avail_text = "" """

if old_cat_loop in content:
    content = content.replace(old_cat_loop, new_cat_loop)
    print("Successfully replaced proceed_to_categories loop")
else:
    print("Could not find old_cat_loop in content")

with open("apps/bot/handlers.py", "w", encoding="utf-8") as f:
    f.write(content)

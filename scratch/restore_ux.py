import os

handlers_path = r'c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py'

with open(handlers_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 1. Restore handle_start (Premium Dashboard)
start_marker = 'async def handle_start(message: types.Message):'
next_func_marker = 'async def handle_booking_start'
start_idx = content.find(start_marker)
next_idx = content.find(next_func_marker)

if start_idx != -1 and next_idx != -1:
    premium_start = """async def handle_start(message: types.Message):
    async with AsyncSessionLocal() as db:
        from sqlalchemy import func
        acc_repo = AccountRepository(db)
        res_repo = ReservationRepository(db)
        active_accs = len(await acc_repo.get_available_accounts())
        active_tasks = len(await res_repo.get_active_tasks())
        
        # Count available events
        stmt = select(func.count(LiveEvent.id)).where(LiveEvent.status.in_(["AVAILABLE", "active"]))
        active_events_count = (await db.execute(stmt)).scalar() or 0
    
    dashboard = (
        "\U0001f680 <b>Webook Sniper Elite</b>\\n\\n"
        f"\U0001f3af \u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0627\u0644\u064a\u0648\u0645: {active_events_count}\\n"
        "\u26a1ï¸ \u0627\u0644\u0633\u0631\u0639\u0629: \u0641\u0627\u0626\u0642\u0629\\n"
        "\U0001f7e2 \u0627\u0644\u0646\u0638\u0627\u0645: \u0645\u062a\u0635\u0644\\n"
        "\U0001f6e1 \u0627\u0644\u062d\u0645\u0627\u064a\u0629: \u0645\u0641\u0639\u0644\u0629\\n"
        f"\U0001f464 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a: {active_accs} \u0646\u0634\u0637\u0629\\n\\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n\\n"
        "\u2705 \u062d\u062c\u0632 \u0645\u062a\u0627\u062d \u0628\u062d\u0633\u0627\u0628 \u0623\u0648 \u0628\u062f\u0648\u0646 \u062d\u0633\u0627\u0628\\n"
        "\u2705 \u0639\u0645\u0648\u0644\u0629 \u0645\u0645\u064a\u0632\u0629\\n"
        "\u2705 \u0628\u0648\u062a\u0627\u062a \u0641\u0627\u0626\u0642\u0629 \u0627\u0644\u0633\u0631\u0639\u0629 \u0644\u0644\u062d\u062c\u0632\\n"
        "\u2705 \u062d\u0645\u0627\u064a\u0629 \u0642\u0648\u064a\u0629 \u0636\u062f \u0627\u0644\u0628\u0627\u0646\\n"
        "\u2705 \u0625\u0645\u0643\u0627\u0646\u064a\u0629 \u0646\u0642\u0644 \u0627\u0644\u062a\u0630\u0627\u0643\u0631\\n"
        "\u2705 \u062d\u062c\u0632 \u0645\u0628\u0627\u0634\u0631 \u0639\u0628\u0631 \u0631\u0627\u0628\u0637 \u0627\u0644\u062f\u0641\u0639\\n"
        "\u2705 \u062a\u062c\u0627\u0648\u0632 \u0637\u0627\u0628\u0648\u0631\\n"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f680 \u0627\u0628\u062f\u0623 \u062d\u062c\u0632 \u062c\u062f\u064a\u062f", callback_data="booking_start"))
    builder.row(
        types.InlineKeyboardButton(text="\U0001f3af \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0627\u0644\u0634\u0627\u0626\u0639\u0629", callback_data="all_events"),
        types.InlineKeyboardButton(text="\u26bd \u0627\u0644\u062f\u0648\u0631\u064a \u0627\u0644\u0633\u0639\u0648\u062f\u064a", callback_data="browse_org:saudi-pro-league")
    )
    builder.row(
        types.InlineKeyboardButton(text="\U0001f3b5 \u0627\u0644\u062d\u0641\u0644\u0627\u062a", callback_data="browse_org:concerts"),
        types.InlineKeyboardButton(text="\U0001f39f \u062d\u062c\u0648\u0632\u0627\u062a\u064a", callback_data="list_tasks")
    )
    builder.row(
        types.InlineKeyboardButton(text="\U0001f464 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a", callback_data="list_accounts"),
        types.InlineKeyboardButton(text="\u2699ï¸ \u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a", callback_data="custom_events_menu")
    )
    builder.row(types.InlineKeyboardButton(text="\U0001f504 \u062a\u062d\u062f\u064a\u062b", callback_data="sync_now"))

    if isinstance(message, types.Message):
        await message.answer(dashboard, parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await safe_send_media(message, dashboard, builder.as_markup())

"""
    content = content[:start_idx] + premium_start + content[next_idx:]

# 2. Restore handle_event_detail (and fix misplaced logic in handle_confirm_count)
# We will insert handle_event_detail before handle_book_event
book_marker = 'async def handle_book_event'
book_idx = content.find(book_marker)

if book_idx != -1:
    event_detail_func = """async def handle_event_detail(callback: types.CallbackQuery, state: FSMContext):
    started = time.perf_counter()
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    
    await state.update_data(slug=slug)
    
    # 1. Fetch Event from DB
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
    
    # 2. Hydrate from API
    detail, status = await hydrate_detail_with_timeout(slug, timeout=15)
    
    if not detail:
        await callback.answer(f"\u26a0ï¸ \u0641\u0634\u0644 \u062a\u062d\u062f\u064a\u062b \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a ({status})", show_alert=True)
        return

    # 3. Extract Fields
    fields = {
        'title': detail.get('title') or (event.title_ar if event else slug),
        'venue': detail.get('venue', {}).get('name') or (event.venue_name if event else '\u063a\u064a\u0631 \u0645\u062a\u0648\u0641\u0631'),
        'image_url': detail.get('image_url') or (event.image_url if event else None),
        'date_str': detail.get('start_date_html') or (event.starts_at.strftime('%Y-%m-%d') if event and event.starts_at else '\u0642\u0631\u064a\u0628\u0627\u064b')
    }
    
    tickets = extract_ticket_list(detail)
    
    # 4. Premium UI Formatting
    text = (
        f"\u26bd <b>{clean_html(fields['title'])}</b>\\n"
        f"\U0001f3df {clean_html(fields['venue'])}\\n\\n"
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

    await safe_send_media(callback, text, builder.as_markup(), image_url=fields["image_url"])
    await callback.answer()
    
    logger.info(f"[HANDLER_SUCCESS] handle_event_detail | slug={slug} took={elapsed_ms(started)}ms")

"""
    content = content[:book_idx] + event_detail_func + content[book_idx:]

# 3. Restore handle_all_events
# Insert it after handle_booking_start
browse_marker = 'async def handle_browse_org'
browse_idx = content.find(browse_marker)

if browse_idx != -1:
    all_events_func = """async def handle_all_events(callback: types.CallbackQuery, state: FSMContext):
    events = await discovery.get_all_events(limit=20)
    
    builder = InlineKeyboardBuilder()
    if not events:
        await callback.message.edit_text("\U0001f50e \u0644\u0627 \u062a\u0648\u062c\u062f \u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0645\u0633\u062c\u0644\u0629 \u062d\u0627\u0644\u064a\u0627\u064b.", 
            reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="back_main")).as_markup())
        return
        
    for ev in events:
        date_label = ev.starts_at.strftime('%m/%d') if ev.starts_at else ''
        status_icon = "\U0001f7e2" if ev.status == "AVAILABLE" else "\U0001f534"
        builder.row(types.InlineKeyboardButton(
            text=f"{status_icon} {ev.title_ar} | {date_label}",
            callback_data=f"e_det:{ev.id}"
        ))
    
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="back_main"))
    await callback.message.edit_text(f"\U0001f30d <b>\u062c\u0645\u064a\u0639 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a ({len(events)}):</b>", parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

"""
    content = content[:browse_idx] + all_events_func + content[browse_idx:]

# 4. Clean up handle_confirm_count (Remove the misplaced event detail logic)
confirm_marker = 'async def handle_confirm_count(callback: types.CallbackQuery, state: FSMContext):'
confirm_idx = content.find(confirm_marker)
if confirm_idx != -1:
    # Replace the body of handle_confirm_count with actual mission summary
    end_of_func = content.find('async def handle_book_event', confirm_idx)
    if end_of_func == -1: # Should not happen
        end_of_func = content.find('async def proceed_to_teams', confirm_idx)
    
    actual_confirm_count = """async def handle_confirm_count(callback: types.CallbackQuery, state: FSMContext):
    \"\"\"Step 5: Mission Summary and Execution trigger.\"\"\"
    count = callback.data.split(":")[1]
    await state.update_data(count=count)
    data = await state.get_data()
    
    slug = data.get("slug")
    ticket_id = data.get("ticket_id")
    
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
    
    summary = (
        f"\U0001f680 <b>\u0645\u0644\u062e\u0635 \u0627\u0644\u0645\u0647\u0645\u0629</b>\\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
        f"\U0001f3af \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629: {event.title_ar if event else slug}\\n"
        f"\U0001f3ab \u0627\u0644\u0641\u0626\u0629: {data.get('category_name', '\u0627\u0641\u062a\u0631\u0627\u0636\u064a\u0629')}\\n"
        f"\U0001f522 \u0627\u0644\u0639\u062f\u062f: {count}\\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
        f"\u26a1ï¸ \u0633\u064a\u062a\u0645 \u0627\u0644\u0628\u062f\u0621 \u0641\u0648\u0631\u0627\u064b \u0628\u0623\u0641\u0636\u0644 \u062d\u0633\u0627\u0628 \u0645\u062a\u0627\u062d\\n"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f680 \u062a\u0646\u0641\u064a\u0630 \u0627\u0644\u062d\u062c\u0632", callback_data=f"exec_b:{slug}"))
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u062a\u0631\u0627\u062c\u0639", callback_data=f"e_det:{slug}"))
    
    await callback.message.edit_text(summary, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()
"""
    content = content[:confirm_idx] + actual_confirm_count + content[end_of_func:]

with open(handlers_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Restoration of Premium UX and logic completed in handlers.py")

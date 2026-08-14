import os

handlers_path = r'c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py'

with open(handlers_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# We want to replace the block from the first handle_booking_start 
# up to the helper functions.
start_line = -1
for i, line in enumerate(lines):
    if "async def handle_booking_start" in line:
        start_line = i
        break

end_line = -1
for i, line in enumerate(lines):
    if "def _looks_like_image_url" in line:
        end_line = i
        break

if start_line != -1 and end_line != -1:
    clean_handlers = r"""
async def handle_booking_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as db:
        categories = await discovery.get_live_categories()
        
        builder = InlineKeyboardBuilder()
        if not categories:
            await callback.answer("\u26a0ï¸ \u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u0635\u0646\u064a\u0641\u0627\u062a \u062d\u0627\u0644\u064a\u0627\u064b.")
            return
        
        for cat in categories:
            stmt = select(func.count(LiveEvent.id)).where(LiveEvent.genre_id == cat.id)
            count = (await db.execute(stmt)).scalar() or 0
            builder.row(types.InlineKeyboardButton(text=f"\U0001f3af {cat.name_ar} ({count})", callback_data=f"browse_org:{cat.slug}"))
        
        builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="back_main"))
        await safe_send_media(callback, "\U0001f3af <b>\u0627\u062e\u062a\u0631 \u0627\u0644\u062a\u0635\u0646\u064a\u0641:</b>\n<i>\u062c\u0645\u064a\u0639 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0645\u0632\u0627\u0645\u0646\u0629 \u0645\u0646 webook.com</i>", builder.as_markup())
        await callback.answer()

async def handle_all_events(callback: types.CallbackQuery, state: FSMContext):
    events = await discovery.get_all_events(limit=20)
    
    builder = InlineKeyboardBuilder()
    if not events:
        await callback.message.edit_text("\U0001f50e \u0644\u0627 \u062a\u0648\u062c\u062f \u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0645\u0633\u062c\u0644\u0629 \u062d\u0627\u0644\u064a\u0627\u064b.", 
            reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="back_main")).as_markup())
        return
        
    for ev in events:
        date_label = ev.starts_at.strftime('%m/%d') if ev.starts_at else ''
        status_icon = "\U0001f7e2" if ev.status == "AVAILABLE" else "\U0001f534"
        builder.row(types.InlineKeyboardButton(
            text=f"{status_icon} {ev.title_ar} | {date_label}",
            callback_data=f"e_det:{ev.id}"
        ))
    
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="back_main"))
    await safe_send_media(callback, f"\U0001f30d <b>\u062c\u0645\u064a\u0639 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a ({len(events)}):</b>", builder.as_markup())
    await callback.answer()

async def handle_browse_org(callback: types.CallbackQuery, state: FSMContext):
    org_slug = callback.data.split(":")[1]
    events = await discovery.get_events_by_genre(org_slug)
    
    builder = InlineKeyboardBuilder()
    if not events:
        builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="booking_start"))
        await callback.message.edit_text("\u26a0ï¸ \u0644\u0627 \u062a\u0648\u062c\u062f \u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0646\u0634\u0637\u0629 \u0641\u064a \u0647\u0630\u0627 \u0627\u0644\u062a\u0635\u0646\u064a\u0641 \u062d\u0627\u0644\u064a\u0627\u064b.", reply_markup=builder.as_markup())
        await callback.answer()
        return
        
    for ev in events[:20]:
        date_label = ev.starts_at.strftime('%m/%d') if ev.starts_at else ''
        status_icon = "\U0001f7e2" if ev.status == "AVAILABLE" else "\U0001f534"
        builder.row(types.InlineKeyboardButton(text=f"{status_icon} {ev.title_ar} | {date_label}", callback_data=f"e_det:{ev.id}"))
    
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="booking_start"))
    await safe_send_media(callback, f"\U0001f4c5 <b>\u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0627\u0644\u0645\u062a\u0627\u062d\u0629 ({len(events)}):</b>", builder.as_markup())
    await callback.answer()

async def handle_event_detail(callback: types.CallbackQuery, state: FSMContext):
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    await state.update_data(slug=slug)
    
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
    
    detail, status = await hydrate_detail_with_timeout(slug, timeout=15)
    if not detail:
        await callback.answer(f"\u26a0ï¸ \u0641\u0634\u0644 \u062a\u062d\u062f\u064a\u062b \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a ({status})", show_alert=True)
        return

    fields = {
        'title': detail.get('title') or (event.title_ar if event else slug),
        'venue': detail.get('venue', {}).get('name') or (event.venue_name if event else '\u0645\u0643\u0627\u0646 \u063a\u064a\u0631 \u0645\u0639\u0631\u0648\u0641'),
        'image_url': detail.get('image_url') or (event.image_url if event else None),
        'date_str': detail.get('start_date_html') or (event.starts_at.strftime('%Y-%m-%d') if event and event.starts_at else '\u0642\u0631\u064a\u0628\u0627\u064b')
    }
    tickets = extract_ticket_list(detail)
    
    text = (
        f"\U0001f3ad <b>{clean_html(fields['title'])}</b>\n"
        f"\U0001f4cd {clean_html(fields['venue'])}\n\n"
        f"\U0001f4c5 {fields['date_str']}\n"
        f"\U0001f4b0 \u0627\u0642\u0644 \u0633\u0639\u0631: {clean_html(str(tickets[0].get('price', '35')) if tickets else '35')} SAR\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
    )
    
    if tickets:
        for t in tickets[:6]:
            t_name = clean_html(t.get("title") or t.get("name") or "\u062a\u0630\u0643\u0631\u0629")
            price_val = t.get("price") or t.get("base_price") or 0
            is_avail = ticket_has_available_inventory(t)
            avail_icon = "\U0001f7e2" if is_avail else "\U0001f534"
            text += f"{avail_icon} {t_name} â† {price_val} SAR\n"

    event_ref = event.id if event else slug
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="\u26a1ï¸ \u062d\u062c\u0632 \u0633\u0631\u064a\u0639", callback_data=f"s_bk:{event_ref}"),
        types.InlineKeyboardButton(text="\U0001f39f \u0627\u062e\u062a\u064a\u0627\u0631 \u064a\u062f\u0648\u064a", callback_data=f"b_ev:{event_ref}")
    )
    builder.row(
        types.InlineKeyboardButton(text="\U0001f5fa \u0627\u0644\u0645\u062e\u0637\u0637", callback_data=f"v_ch:{event_ref}"),
        types.InlineKeyboardButton(text="\U0001f514 \u062a\u0646\u0628\u064a\u0647 \u0639\u0646\u062f \u0627\u0644\u062a\u0648\u0641\u0631", callback_data=f"s_ad:{event_ref}")
    )
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="booking_start"))

    await safe_send_media(callback, text, builder.as_markup(), image_url=fields["image_url"])
    await callback.answer()

async def handle_book_event(callback: types.CallbackQuery, state: FSMContext):
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    await state.clear()
    await state.update_data(slug=slug)
    await proceed_to_categories(callback, state, slug)

async def proceed_to_categories(callback: types.CallbackQuery, state: FSMContext, slug: str):
    async with AsyncSessionLocal() as db:
        acc_repo = AccountRepository(db)
        accounts = await acc_repo.get_available_accounts()
        if not accounts:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="\U0001f517 \u0631\u0628\u0637 \u062d\u0633\u0627\u0628 Webook", callback_data="link_account_prompt"))
            builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data=f"e_det:{slug}"))
            await safe_send_media(callback, "\u26a0ï¸ <b>\u0644\u0627 \u064a\u0648\u062c\u062f \u062d\u0633\u0627\u0628\u0627\u062a Webook \u0645\u0631\u062a\u0628\u0637\u0629!</b>\n\u064a\u0631\u062c\u0649 \u0631\u0628\u0637 \u062d\u0633\u0627\u0628 \u0623\u0648\u0644\u0627\u064b \u0644\u062a\u062a\u0645\u0643\u0646 \u0645\u0646 \u0639\u0631\u0636 \u0627\u0644\u0641\u0626\u0627\u062a \u0627\u0644\u0645\u062a\u0627\u062d\u0629.", builder.as_markup())
            return
            
    await callback.message.edit_text("\U0001f504 <b>\u062c\u0627\u0631\u064a \u062c\u0644\u0628 \u0627\u0644\u0641\u0626\u0627\u062a \u0627\u0644\u0645\u062a\u0627\u062d\u0629...</b>", parse_mode="HTML")
    detail = await discovery.sync_event_detail(slug)
    tickets = extract_ticket_list(detail)
    
    builder = InlineKeyboardBuilder()
    if not tickets:
        builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data=f"e_det:{slug}"))
        await callback.message.edit_text("\u26a0ï¸ <b>\u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u0630\u0627\u0643\u0631 \u0645\u062a\u0627\u062d\u0629 \u062d\u0627\u0644\u064a\u0627\u064b.</b>", parse_mode="HTML", reply_markup=builder.as_markup())
        return

    for t in tickets:
        if ticket_has_available_inventory(t):
            name = clean_html(t.get("title") or t.get("name") or "\u0641\u0626\u0629")
            price = t.get("price") or t.get("base_price") or "â€”"
            t_id = t.get("id") or t.get("_id")
            builder.row(types.InlineKeyboardButton(text=f"\U0001f3ab {name} ({price} SAR)", callback_data=f"sel_t:{t_id}"))
    
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data=f"e_det:{slug}"))
    await callback.message.edit_text("\U0001f3af <b>\u0627\u062e\u062a\u0631 \u0641\u0626\u0629 \u0627\u0644\u062a\u0630\u0627\u0643\u0631 \u0627\u0644\u0645\u0637\u0644\u0648\u0628\u0629:</b>", parse_mode="HTML", reply_markup=builder.as_markup())

async def handle_select_ticket(callback: types.CallbackQuery, state: FSMContext):
    ticket_id = callback.data.split(":")[1]
    await state.update_data(ticket_id=ticket_id)
    builder = InlineKeyboardBuilder()
    for i in range(1, 9): builder.button(text=str(i), callback_data=f"set_q:{i}")
    builder.adjust(4)
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="booking_start"))
    await callback.message.edit_text("\U0001f522 <b>\u0643\u0645 \u0639\u062f\u062f \u0627\u0644\u062a\u0630\u0627\u0643\u0631 \u0627\u0644\u0645\u0637\u0644\u0648\u0628 \u062d\u062c\u0632\u0647\u0627\u061f</b>", parse_mode="HTML", reply_markup=builder.as_markup())

async def handle_confirm_count(callback: types.CallbackQuery, state: FSMContext):
    count = int(callback.data.split(":")[1])
    await state.update_data(count=count)
    data = await state.get_data()
    slug, t_id = data.get("slug"), data.get("ticket_id")
    text = (
        f"\U0001f3af <b>\u062a\u0623\u0643\u064a\u062f \u0645\u0647\u0645\u0629 \u0627\u0644\u0642\u0646\u0635</b>\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        f"\U0001f3ad \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629: <code>{slug}</code>\n"
        f"\U0001f3ab \u0627\u0644\u0641\u0626\u0629: <code>{t_id}</code>\n"
        f"\U0001f522 \u0627\u0644\u0639\u062f\u062f: <b>{count}</b>\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        f"\u26a0ï¸ \u0633\u064a\u0642\u0648\u0645 \u0627\u0644\u0628\u0648\u062a \u0628\u0645\u0631\u0627\u0642\u0628\u0629 \u0627\u0644\u0633\u064a\u0631\u0641\u0631 \u0648\u0627\u0644\u0628\u062f\u0621 \u0628\u0627\u0644\u062d\u062c\u0632 \u0641\u0648\u0631\u0627\u064b."
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f680 \u0627\u0628\u062f\u0623 \u0627\u0644\u0642\u0646\u0635 \u0627\u0644\u0622\u0646!", callback_data=f"exec_b:{slug}"))
    builder.row(types.InlineKeyboardButton(text="\u274c \u0625\u0644\u063a\u0627\u0621 \u0648\u0627\u0644\u0639\u0648\u062f\u0629", callback_data=f"e_det:{slug}"))
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
"""
    new_lines = lines[:start_line] + [clean_handlers] + lines[end_line:]
    
    with open(handlers_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Purged broken handlers block (lines {start_line}-{end_line}) and restored clean versions.")
else:
    print(f"Markers not found. start_line={start_line}, end_line={end_line}")

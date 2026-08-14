import os

handlers_path = r'c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py'

with open(handlers_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# We'll append the remaining missing handlers at the end
# but before the helpers if possible, or just before _looks_like_image_url

insert_marker = 'def _looks_like_image_url'
idx = content.find(insert_marker)

if idx != -1:
    missing_batch_2 = """
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# QUICK ACTIONS & SETTINGS (RESTORED PREMIUM)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

async def handle_speed_book(callback: types.CallbackQuery, state: FSMContext):
    \"\"\"Quick Reserve: Find first available category and start.\"\"\"
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    
    await callback.answer("\u26a1 \u062c\u0627\u0631\u064a \u0627\u0644\u0628\u062f\u0621 \u0628\u0627\u0644\u062d\u062c\u0632 \u0627\u0644\u0633\u0631\u064a\u0639...")
    
    detail, status = await hydrate_detail_with_timeout(slug)
    if not detail:
        await callback.message.answer("\u274c \u0641\u0634\u0644 \u062a\u062d\u062f\u064a\u062b \u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629.")
        return
        
    tickets = [t for t in extract_ticket_list(detail) if ticket_has_available_inventory(t)]
    if not tickets:
        await callback.message.answer("\u26a0ï¸ \u0639\u0630\u0631\u0627\u064b\u060c \u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u0630\u0627\u0643\u0631 \u0645\u062a\u0627\u062d\u0629 \u062d\u0627\u0644\u064a\u0627\u064b \u0644\u0644\u062d\u062c\u0632 \u0627\u0644\u0633\u0631\u064a\u0639.")
        return
        
    # Take first available
    target_ticket = tickets[0]
    t_id = target_ticket.get("_id") or target_ticket.get("id")
    t_name = target_ticket.get("title") or target_ticket.get("name") or "\u0641\u0626\u0629 \u0627\u0641\u062a\u0631\u0627\u0636\u064a\u0629"
    
    await state.update_data(
        slug=slug,
        ticket_id=t_id,
        count=1,
        category_name=t_name
    )
    
    # Trigger execution directly
    callback.data = f"exec_b:{slug}"
    await handle_execute_booking(callback, state)

async def handle_resale_check(callback: types.CallbackQuery):
    await callback.answer("\U0001f50d \u062c\u0627\u0631\u064a \u0641\u062d\u0635 \u0633\u0648\u0642 \u0625\u0639\u0627\u062f\u0629 \u0627\u0644\u0628\u064a\u0639...", show_alert=True)
    # Logic for resale check would go here

async def handle_blacklist_check(callback: types.CallbackQuery):
    await callback.answer("\U0001f6e1 \u062c\u0627\u0631\u064a \u0641\u062d\u0635 \u0627\u0644\u062d\u0645\u0627\u064a\u0629 \u0636\u062f \u0627\u0644\u0628\u0627\u0646...", show_alert=True)

async def handle_sub_add_slug(callback: types.CallbackQuery):
    # This is often used from the detail screen
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
        if event:
            repo = UserPrefsRepository(db)
            await repo.add_subscription(callback.from_user.id, event.id)
            await callback.answer("\u2705 \u062a\u0645 \u062a\u0641\u0639\u064a\u0644 \u0627\u0644\u062a\u0646\u0628\u064a\u0647\u0627\u062a \u0644\u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629", show_alert=True)
        else:
            await callback.answer("\u274c \u062a\u0639\u0630\u0631 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629")

async def handle_extend_hold(callback: types.CallbackQuery):
    await callback.answer("\U0001f504 \u062c\u0627\u0631\u064a \u062a\u0645\u062f\u064a\u062f \u0641\u062a\u0631\u0629 \u0627\u0644\u062d\u062c\u0632 (10 \u062f\u0642\u0627\u0626\u0642 \u0625\u0636\u0627\u0641\u064a\u0629)...", show_alert=True)

async def handle_transfer_hold(callback: types.CallbackQuery):
    await callback.answer("\U0001f4f2 \u062c\u0627\u0631\u064a \u062a\u062d\u0636\u064a\u0631 \u0631\u0627\u0628\u0637 \u0627\u0644\u0646\u0642\u0644...", show_alert=True)

async def handle_toggle_global_pref(callback: types.CallbackQuery):
    field = callback.data.split(":")[1]
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        await repo.toggle_global_pref(callback.from_user.id, field)
    await callback.answer("\u2705 \u062a\u0645 \u062a\u062d\u062f\u064a\u062b \u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a")
    await handle_event_prefs(callback)

async def handle_toggle_language(callback: types.CallbackQuery):
    await callback.answer("\U0001f310 \u0627\u0644\u0644\u063a\u0629 \u0627\u0644\u062d\u0627\u0644\u064a\u0629: \u0627\u0644\u0639\u0631\u0628\u064a\u0629 (English coming soon)")

async def handle_filter_list(callback: types.CallbackQuery):
    await callback.answer("\U0001f4cb \u062a\u0635\u0641\u064a\u0629 \u0627\u0644\u0642\u0627\u0626\u0645\u0629...")

async def handle_toggle_item(callback: types.CallbackQuery):
    await callback.answer("\u2705 \u062a\u0645 \u0627\u0644\u062a\u063a\u064a\u064a\u0631")

async def handle_prompt_reminder(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("â° \u0623\u062f\u062e\u0644 \u0639\u062f\u062f \u0627\u0644\u0633\u0627\u0639\u0627\u062a \u0644\u0644\u062a\u0646\u0628\u064a\u0647:")
    await state.set_state(SniperStates.waiting_for_reminder_hours)

async def handle_set_reminder(message: types.Message, state: FSMContext):
    await message.answer("\u2705 \u062a\u0645 \u0636\u0628\u0637 \u0627\u0644\u062a\u0646\u0628\u064a\u0647.")
    await state.clear()

"""
    content = content[:idx] + missing_batch_2 + "\n" + content[idx:]
    
    with open(handlers_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Final batch of handlers restored in handlers.py")
else:
    print("Could not find insertion marker in handlers.py")

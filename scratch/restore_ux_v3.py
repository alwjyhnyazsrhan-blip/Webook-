import os

handlers_path = r'c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py'

with open(handlers_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# We'll insert these handlers before the helpers at the end
insert_marker = 'def _looks_like_image_url'
idx = content.find(insert_marker)

if idx != -1:
    missing_handlers = """
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ACCOUNT MANAGEMENT (RESTORED PREMIUM)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

async def list_accounts(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as db:
        repo = AccountRepository(db)
        accs = await repo.get_available_accounts()
        
    text = "\U0001f464 <b>\u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a \u0627\u0644\u0645\u0633\u062c\u0644\u0629:</b>\\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
    if not accs:
        text += "<i>\u0644\u0627 \u062a\u0648\u062c\u062f \u062d\u0633\u0627\u0628\u0627\u062a \u0645\u0631\u062a\u0628\u0637\u0629 \u062d\u0627\u0644\u064a\u0627\u064b.</i>\\n"
    
    for a in accs:
        status = "\U0001f7e2" if a.is_valid else "\U0001f534"
        role_icon = {"SNIPER": "\U0001f3af", "EXTENSION": "\U0001f504", "MONITOR": "\U0001f47b"}.get(a.role, "\U0001f464")
        text += f"{status} {role_icon} <code>{a.email}</code>\\n"

    builder = InlineKeyboardBuilder()
    for a in accs[:10]:
        builder.row(types.InlineKeyboardButton(text=f"\U0001f464 {a.email}", callback_data=f"acc_detail:{a.id}"))
    
    builder.row(
        types.InlineKeyboardButton(text="\U0001f3af \u0631\u0628\u0637 \u062d\u0633\u0627\u0628 \u0642\u0646\u0635", callback_data="link_sniper"),
        types.InlineKeyboardButton(text="\U0001f504 \u0631\u0628\u0637 \u062d\u0633\u0627\u0628 \u062a\u0645\u062f\u064a\u062f", callback_data="link_extension")
    )
    builder.row(types.InlineKeyboardButton(text="\u2705 \u062a\u062d\u0642\u0642 \u0645\u0646 \u0627\u0644\u0643\u0644", callback_data="verify_all_accounts"))
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="back_main"))
    
    await safe_send_media(callback, text, builder.as_markup())

async def handle_acc_detail(callback: types.CallbackQuery):
    acc_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        acc = await db.get(AuthSession, acc_id)
    
    if not acc:
        await callback.answer("\u26a0ï¸ \u0627\u0644\u062d\u0633\u0627\u0628 \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f")
        return

    status_str = "\U0001f7e2 \u0635\u0627\u0644\u062d" if acc.is_valid else "\U0001f534 \u063a\u064a\u0631 \u0635\u0627\u0644\u062d / \u0645\u0646\u062a\u0647\u064a"
    role_ar = {"SNIPER": "\u0642\u0646\u0635 (Sniper)", "EXTENSION": "\u062a\u0645\u062f\u064a\u062f (Extension)", "MONITOR": "\u0645\u0631\u0627\u0642\u0628\u0629"}.get(acc.role, acc.role)
    
    text = (
        f"\U0001f464 <b>\u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u062d\u0633\u0627\u0628</b>\\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
        f"\U0001f4e7 \u0627\u0644\u0628\u0631\u064a\u062f: <code>{acc.email}</code>\\n"
        f"\U0001f3f7ï¸ \u0627\u0644\u062f\u0648\u0631: {role_ar}\\n"
        f"\U0001f4ca \u0627\u0644\u062d\u0627\u0644\u0629: {status_str}\\n"
        f"\U0001f552 \u0627\u0644\u062a\u062d\u062f\u064a\u062b: {acc.updated_at.strftime('%Y-%m-%d %H:%M') if acc.updated_at else 'â€”'}\\n"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f504 \u0627\u0644\u062a\u062d\u0642\u0642 \u0645\u0646 \u0627\u0644\u062a\u0648\u0643\u0646", callback_data=f"verify_acc:{acc_id}"))
    builder.row(
        types.InlineKeyboardButton(text="\U0001f3af \u0642\u0646\u0635", callback_data=f"set_role:{acc_id}:SNIPER"),
        types.InlineKeyboardButton(text="\U0001f504 \u062a\u0645\u062f\u064a\u062f", callback_data=f"set_role:{acc_id}:EXTENSION"),
        types.InlineKeyboardButton(text="\U0001f47b \u0645\u0631\u0627\u0642\u0628", callback_data=f"set_role:{acc_id}:MONITOR"),
    )
    builder.row(types.InlineKeyboardButton(text="\U0001f5d1 \u062d\u0630\u0641 \u0627\u0644\u062d\u0633\u0627\u0628", callback_data=f"delete_acc:{acc_id}"))
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="list_accounts"))
    
    await safe_send_media(callback, text, builder.as_markup())

async def handle_set_role(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    acc_id, role = int(parts[1]), parts[2]
    async with AsyncSessionLocal() as db:
        repo = AccountRepository(db)
        await repo.set_role(acc_id, role)
    
    await callback.answer("\u2705 \u062a\u0645 \u062a\u063a\u064a\u064a\u0631 \u062f\u0648\u0631 \u0627\u0644\u062d\u0633\u0627\u0628")
    callback.data = f"acc_detail:{acc_id}"
    await handle_acc_detail(callback)

async def handle_verify_acc(callback: types.CallbackQuery):
    acc_id = int(callback.data.split(":")[1])
    from services.account.manager import AccountManager
    async with AsyncSessionLocal() as db:
        mgr = AccountManager(db)
        ok = await mgr.verify_account(acc_id)
    
    await callback.answer("\u2705 \u0627\u0644\u062a\u0648\u0643\u0646 \u0635\u0627\u0644\u062d!" if ok else "\U0001f534 \u0627\u0644\u062a\u0648\u0643\u0646 \u0645\u0646\u062a\u0647\u064a", show_alert=True)
    callback.data = f"acc_detail:{acc_id}"
    await handle_acc_detail(callback)

async def handle_verify_all(callback: types.CallbackQuery):
    await callback.message.edit_text("\U0001f504 <b>\u062c\u0627\u0631\u064a \u0627\u0644\u062a\u062d\u0642\u0642 \u0645\u0646 \u062c\u0645\u064a\u0639 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a...</b>", parse_mode="HTML")
    from services.account.manager import AccountManager
    async with AsyncSessionLocal() as db:
        mgr = AccountManager(db)
        results = await mgr.verify_all_accounts()
    
    text = (
        f"\u2705 <b>\u0646\u062a\u0627\u0626\u062c \u0627\u0644\u062a\u062d\u0642\u0642:</b>\\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
        f"\U0001f7e2 \u0646\u0634\u0637: {results['active']}\\n"
        f"\U0001f534 \u0645\u0646\u062a\u0647\u064a: {results['expired']}\\n"
        f"\U0001f4ca \u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a: {results['total']}\\n"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="list_accounts"))
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())

async def handle_delete_acc(callback: types.CallbackQuery):
    acc_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        acc = await db.get(AuthSession, acc_id)
        if acc:
            await db.delete(acc)
            await db.commit()
    await callback.answer("\u2705 \u062a\u0645 \u062d\u0630\u0641 \u0627\u0644\u062d\u0633\u0627\u0628")
    await list_accounts(callback)

async def handle_link_sniper(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(link_role="SNIPER")
    await handle_link_account_prompt(callback, state)

async def handle_link_extension(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(link_role="EXTENSION")
    await handle_link_account_prompt(callback, state)

async def handle_link_account_prompt(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="list_accounts"))
    await callback.message.edit_text(
        "\U0001f517 <b>\u0631\u0628\u0637 \u062d\u0633\u0627\u0628 Webook \u0627\u0644\u062c\u062f\u064a\u062f</b>\\n\\n"
        "\u064a\u0631\u062c\u0649 \u0625\u0631\u0633\u0627\u0644 \u0627\u0644\u0640 <code>Bearer Token</code> \u0627\u0644\u062e\u0627\u0635 \u0628\u0627\u0644\u062d\u0633\u0627\u0628.\\n\\n"
        "<i>\u064a\u0645\u0643\u0646\u0643 \u0627\u0644\u062d\u0635\u0648\u0644 \u0639\u0644\u064a\u0647 \u0645\u0646 \u0627\u0644\u0645\u062a\u0635\u0641\u062d (Inspect -> Network -> api.webook.com -> Authorization)</i>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await state.set_state(SniperStates.waiting_for_token)

async def handle_token_submission(message: types.Message, state: FSMContext):
    token = message.text.replace("Bearer ", "").strip()
    status_msg = await message.answer("\U0001f504 <b>\u062c\u0627\u0631\u064a \u0627\u0644\u062a\u062d\u0642\u0642 \u0645\u0646 \u0627\u0644\u062d\u0633\u0627\u0628...</b>", parse_mode="HTML")

    data = await state.get_data()
    role = data.get("link_role", "SNIPER")

    from services.account.manager import AccountManager
    async with AsyncSessionLocal() as db:
        mgr = AccountManager(db)
        result = await mgr.add_account_via_token(token, role=role)

    if result.get("error"):
        await status_msg.edit_text(f"\u274c <b>\u062e\u0637\u0623:</b>\\n{result['error']}", parse_mode="HTML")
    else:
        profile = result.get("profile", {})
        name = profile.get("first_name", "")
        email = result.get("email", "")
        role_ar = {"SNIPER": "\u0642\u0646\u0635", "EXTENSION": "\u062a\u0645\u062f\u064a\u062f"}.get(role, role)
        await status_msg.edit_text(
            f"\u2705 <b>\u062a\u0645 \u0631\u0628\u0637 \u0627\u0644\u062d\u0633\u0627\u0628 \u0628\u0646\u062c\u0627\u062d!</b>\\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
            f"\U0001f464 \u0627\u0644\u0625\u0633\u0645: {name}\\n"
            f"\U0001f4e7 \u0627\u0644\u0628\u0631\u064a\u062f: {email}\\n"
            f"\U0001f3f7ï¸ \u0627\u0644\u062f\u0648\u0631: {role_ar}",
            parse_mode="HTML"
        )
    await state.clear()
    await handle_start(message)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TASK & RESERVATION MANAGEMENT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

async def list_tasks(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as db:
        res_repo = ReservationRepository(db)
        tasks = await res_repo.get_active_tasks()
        
    text = "\U0001f3af <b>\u0627\u0644\u0645\u0647\u0627\u0645 \u0627\u0644\u0646\u0634\u0637\u0629 (Monitoring):</b>\\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
    if not tasks:
        text += "<i>\u0644\u0627 \u062a\u0648\u062c\u062f \u0645\u0647\u0627\u0645 \u0642\u0646\u0635 \u0646\u0634\u0637\u0629 \u062d\u0627\u0644\u064a\u0627\u064b.</i>\\n"
    
    for t in tasks:
        status_icon = "\U0001f7e2" if t.status == "RESERVED" else "\U0001f504"
        text += f"{status_icon} <code>{t.event_slug}</code> | #{t.id}\\n"

    builder = InlineKeyboardBuilder()
    for t in tasks[:10]:
        builder.row(types.InlineKeyboardButton(text=f"\U0001f4cc \u0627\u0644\u0645\u0647\u0645\u0629 #{t.id}", callback_data=f"task_detail:{t.id}"))
    
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="back_main"))
    await safe_send_media(callback, text, builder.as_markup())

async def handle_task_detail(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        from database.models.reservation import ReservationTask
        task = await db.get(ReservationTask, task_id)
    
    if not task:
        await callback.answer("\u26a0ï¸ \u0627\u0644\u0645\u0647\u0645\u0629 \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f\u0629")
        return

    text = (
        f"\U0001f3af <b>\u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0645\u0647\u0645\u0629 #{task.id}</b>\\n"
        f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
        f"\U0001f3ad \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629: <code>{task.event_slug}</code>\\n"
        f"\U0001f3ab \u0627\u0644\u0641\u0626\u0629: {task.category}\\n"
        f"\U0001f522 \u0627\u0644\u0639\u062f\u062f: {task.seat_count}\\n"
        f"\U0001f4ca \u0627\u0644\u062d\u0627\u0644\u0629: <b>{task.status}</b>\\n"
        f"\U0001f552 \u0627\u0644\u0628\u062f\u0627\u064a\u0629: {task.created_at.strftime('%H:%M:%S') if task.created_at else 'â€”'}\\n"
    )
    
    builder = InlineKeyboardBuilder()
    if task.status == "RESERVED":
        builder.row(types.InlineKeyboardButton(text="\U0001f4b3 \u0631\u0627\u0628\u0637 \u0627\u0644\u062f\u0641\u0639", callback_data=f"payment_link:{task.id}"))
    
    builder.row(types.InlineKeyboardButton(text="\u274c \u0625\u0644\u063a\u0627\u0621 \u0627\u0644\u0645\u0647\u0645\u0629", callback_data=f"cancel_task:{task.id}"))
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="list_tasks"))
    
    await safe_send_media(callback, text, builder.as_markup())

async def handle_cancel_task(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        from database.models.reservation import ReservationTask, TaskStatus
        task = await db.get(ReservationTask, task_id)
        if task:
            task.status = TaskStatus.CANCELLED.value
            await db.commit()
    await callback.answer("\u2705 \u062a\u0645 \u0625\u0644\u063a\u0627\u0621 \u0627\u0644\u0645\u0647\u0645\u0629 \u0628\u0646\u062c\u0627\u062d")
    await list_tasks(callback)

async def handle_execute_booking(callback: types.CallbackQuery, state: FSMContext):
    # This triggers the actual Sniper Orchestrator
    # We resolve the slug from the data
    raw_data = callback.data.split(":")[1]
    
    await callback.message.edit_text("\U0001f680 <b>\u062c\u0627\u0631\u064a \u0625\u0637\u0644\u0627\u0642 \u0627\u0644\u0645\u0647\u0645\u0629...</b>\\n\u26a1ï¸ \u064a\u062a\u0645 \u0627\u0644\u0622\u0646 \u062a\u062c\u0627\u0648\u0632 \u0627\u0644\u0637\u0627\u0628\u0648\u0631 \u0648\u0627\u0644\u0628\u062d\u062b \u0639\u0646 \u0645\u0642\u0627\u0639\u062f.", parse_mode="HTML")
    
    async with AsyncSessionLocal() as db:
        from services.reservation.orchestrator import ReservationOrchestrator
        orch = ReservationOrchestrator(db)
        
        try:
            # We'll create a new task directly from the state data or find the CREATED one
            data = await state.get_data()
            task = await orch.start_reservation(
                user_id=callback.from_user.id,
                event_slug=data.get("slug"),
                category=data.get("ticket_id"),
                count=int(data.get("count", 1)),
                timeslot_id=data.get("timeslot_id"),
                team_id=data.get("team_id")
            )
            
            await callback.message.edit_text(
                f"\u2705 <b>\u062a\u0645 \u0625\u0637\u0644\u0627\u0642 \u0627\u0644\u0645\u0647\u0645\u0629 \u0628\u0646\u062c\u0627\u062d!</b>\\n"
                f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n"
                f"\U0001f194 \u0631\u0642\u0645 \u0627\u0644\u0645\u0647\u0645\u0629: #{task.id}\\n"
                f"\U0001f7e2 \u0627\u0644\u062d\u0627\u0644\u0629: \u062c\u0627\u0631\u064a \u0627\u0644\u0642\u0646\u0635 \u0627\u0644\u0646\u0634\u0637...\\n\\n"
                f"\U0001f4a1 \u0633\u064a\u062a\u0645 \u0625\u062e\u0637\u0627\u0631\u0643 \u0641\u0648\u0631 \u0646\u062c\u0627\u062d \u0627\u0644\u062d\u062c\u0632.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="\U0001f4ca \u0645\u0631\u0627\u0642\u0628\u0629 \u0627\u0644\u0645\u0647\u0645\u0629", callback_data=f"task_detail:{task.id}")).as_markup()
            )
        except Exception as e:
            logger.error(f"[EXECUTE_FAIL] {e}")
            await callback.message.edit_text(f"\u274c <b>\u0641\u0634\u0644 \u0625\u0637\u0644\u0627\u0642 \u0627\u0644\u0645\u0647\u0645\u0629:</b>\\n{str(e)}", parse_mode="HTML")
    
    await state.clear()

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SETTINGS & OTHER HANDLERS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

async def handle_custom_events_menu(callback: types.CallbackQuery):
    text = "\u2699ï¸ <b>\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a \u0648\u0627\u0644\u062a\u062d\u0643\u0645</b>\\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f514 \u0625\u0639\u062f\u0627\u062f\u0627\u062a \u0627\u0644\u062a\u0646\u0628\u064a\u0647\u0627\u062a", callback_data="event_prefs"))
    builder.row(types.InlineKeyboardButton(text="\U0001f310 \u062a\u063a\u064a\u064a\u0631 \u0627\u0644\u0644\u063a\u0629 (Arabic/English)", callback_data="toggle_language"))
    builder.row(types.InlineKeyboardButton(text="\U0001f504 \u062a\u062d\u062f\u064a\u062b \u064a\u062f\u0648\u064a \u0644\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a", callback_data="sync_now"))
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="back_main"))
    await safe_send_media(callback, text, builder.as_markup())

async def handle_sync_now(callback: types.CallbackQuery):
    await callback.answer("\U0001f504 \u062c\u0627\u0631\u064a \u062a\u062d\u062f\u064a\u062b \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0645\u0646 Webook...")
    from services.discovery.engine import DiscoveryEngine
    discovery = DiscoveryEngine()
    await discovery.sync_all()
    await callback.answer("\u2705 \u062a\u0645 \u062a\u062d\u062f\u064a\u062b \u062c\u0645\u064a\u0639 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0628\u0646\u062c\u0627\u062d!", show_alert=True)
    await handle_start(callback)

async def handle_event_prefs(callback: types.CallbackQuery):
    # Simplified premium prefs menu
    text = "\U0001f514 <b>\u062a\u0641\u0636\u064a\u0644\u0627\u062a \u0627\u0644\u062a\u0646\u0628\u064a\u0647\u0627\u062a</b>\\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f4cb \u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0627\u0644\u0645\u062a\u0627\u0628\u0639\u0629", callback_data="list_custom_events"))
    builder.row(types.InlineKeyboardButton(text="â¬…ï¸ \u0639\u0648\u062f\u0629", callback_data="custom_events_menu"))
    await safe_send_media(callback, text, builder.as_markup())

async def handle_payment_link(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        from database.models.reservation import ReservationTask
        task = await db.get(ReservationTask, task_id)
        
    if task and task.checkout_url:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\U0001f4b3 \u062f\u0641\u0639 \u0627\u0644\u062a\u0630\u0627\u0643\u0631", url=task.checkout_url))
        await callback.message.answer(f"\u2705 <b>\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0631\u0627\u0628\u0637 \u0627\u0644\u062f\u0641\u0639 \u0644\u0644\u0645\u0647\u0645\u0629 #{task.id}:</b>", parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await callback.answer("\u26a0ï¸ \u0631\u0627\u0628\u0637 \u0627\u0644\u062f\u0641\u0639 \u063a\u064a\u0631 \u0645\u062a\u0648\u0641\u0631 \u062d\u0627\u0644\u064a\u0627\u064b \u0644\u0647\u0630\u0627 \u0627\u0644\u062d\u062c\u0632", show_alert=True)

"""
    content = content[:idx] + missing_handlers + "\n" + content[idx:]
    
    with open(handlers_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Relocated and Restored Premium Handlers in handlers.py")
else:
    print("Could not find insertion marker in handlers.py")

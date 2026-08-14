import os

path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"

with open(path, 'rb') as f:
    data = f.read()

# We'll use a very loose byte pattern to find the function and replace it.
# We know the function starts with b'async def handle_custom_events_menu' 
# and ends with b'await callback.answer()'

start_marker = b'async def handle_custom_events_menu(callback: types.CallbackQuery):'
end_marker = b'await callback.answer()'

# Find the first occurrence of handle_custom_events_menu
start_idx = data.find(start_marker)
if start_idx != -1:
    # Find the next occurrence of await callback.answer() after start_idx
    end_idx = data.find(end_marker, start_idx)
    if end_idx != -1:
        end_idx += len(end_marker)
        
        new_func = """async def handle_custom_events_menu(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        p = await repo.get_global_prefs(callback.from_user.id)
        lang = p.language or "ar"

    builder = InlineKeyboardBuilder()
    def t(val): return "✅" if val else "❌"
    
    builder.row(types.InlineKeyboardButton(text=f"{t(p.all_notifications)} تفعيل/تعطيل جميع الاشعارات", callback_data="toggle_pref:all_notifications"))
    builder.row(
        types.InlineKeyboardButton(text=f"{t(p.update_alerts)} التحديثات", callback_data="toggle_pref:update_alerts"),
        types.InlineKeyboardButton(text=f"{t(p.new_event_alerts)} فعاليات جديدة", callback_data="toggle_pref:new_event_alerts")
    )
    builder.row(
        types.InlineKeyboardButton(text=f"{t(p.ticket_change_alerts)} التذاكر", callback_data="toggle_pref:ticket_change_alerts"),
        types.InlineKeyboardButton(text=f"{t(p.price_change_alerts)} الاسعار", callback_data="toggle_pref:price_change_alerts")
    )
    
    builder.row(types.InlineKeyboardButton(text="🎯 تفضيلات الفعاليات", callback_data="event_prefs"))
    builder.row(
        types.InlineKeyboardButton(text="📋 الفئات", callback_data="filter_list:favorite_categories"),
        types.InlineKeyboardButton(text="🏙 المناطق", callback_data="filter_list:favorite_zones")
    )
    
    lang_text = "🇺🇸 English" if lang == "ar" else "🇸🇦 العربية"
    builder.row(types.InlineKeyboardButton(text=f"🌐 {lang_text}", callback_data="toggle_language"))
    
    builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="back_main"))
    await safe_edit_text(callback.message, "⚙️ <b>مركز التحكم والاعدادات</b>", reply_markup=builder.as_markup())
    await callback.answer()""".encode('utf-8')
        
        data = data[:start_idx] + new_func + data[end_idx:]
        print(f"Replaced handle_custom_events_menu at {start_idx}:{end_idx}")

# Do same for list_tasks
start_marker_tasks = b'async def list_tasks(callback: types.CallbackQuery):'
start_idx_tasks = data.find(start_marker_tasks)
if start_idx_tasks != -1:
    end_idx_tasks = data.find(end_marker, start_idx_tasks)
    if end_idx_tasks != -1:
        end_idx_tasks += len(end_marker)
        
        new_tasks = """async def list_tasks(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as db:
        repo = ReservationRepository(db)
        tasks = await repo.get_active_tasks()
        text = (
            "📊 <b>العمليات الجارية:</b>\\n"
            "──────────────────\\n"
        )
        if not tasks:
            text += "<i>لا توجد عمليات نشطة.</i>\\n"
        for t in tasks:
            status_icon = {
                "CREATED": "🆕", "SEARCHING": "🔍", "HOLDING": "🔒",
                "RESERVED": "✅", "FAILED": "❌", "EXPIRED": "💀",
            }.get(t.status, "⚡")
            hold_info = ""
            if t.hold_expires_at:
                remaining = (t.hold_expires_at - datetime.now(timezone.utc)).total_seconds()
                if remaining > 0:
                    hold_info = f" | ⏳ {int(remaining)}s"
            text += f"{status_icon} <code>#{t.id}</code> | {t.status} | {t.event_slug}{hold_info}\\n"

    builder = InlineKeyboardBuilder()
    for t in tasks[:10]:
        builder.row(types.InlineKeyboardButton(
            text=f"#{t.id} {t.event_slug}",
            callback_data=f"task_detail:{t.id}"
        ))
    builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="back_main"))
    await safe_edit_text(callback.message, text, builder.as_markup())
    await callback.answer()""".encode('utf-8')
        
        data = data[:start_idx_tasks] + new_tasks + data[end_idx_tasks:]
        print(f"Replaced list_tasks at {start_idx_tasks}:{end_idx_tasks}")

with open(path, 'wb') as f:
    f.write(data)

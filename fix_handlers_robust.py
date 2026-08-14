import os

path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"

with open(path, 'rb') as f:
    data = f.read()

def replace_func(data, func_name, new_body):
    marker = func_name.encode('utf-8')
    start_idx = data.find(b'async def ' + marker)
    if start_idx == -1:
        print(f"Could not find {func_name}")
        return data
    
    # Find next function or end of file
    # For simplicity, we find the next 'async def' or a large distance
    end_marker = b'await callback.answer()'
    end_idx = data.find(end_marker, start_idx)
    if end_idx == -1:
        print(f"Could not find end of {func_name}")
        return data
    
    end_idx += len(end_marker)
    return data[:start_idx] + new_body.encode('utf-8') + data[end_idx:]

new_menu = """async def handle_custom_events_menu(callback: types.CallbackQuery):
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
    await callback.answer()"""

data = replace_func(data, 'handle_custom_events_menu', new_menu)

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
    await callback.answer()"""

data = replace_func(data, 'list_tasks', new_tasks)

# Global cleanup
data = data.replace(b'\xc3\x83\xc2\xa2\xc3\x83\xc2\xa2\xc3\x82\xc2\xac\xc3\x82\xc2\xa2', b'\xe2\x80\xa2')
data = data.replace(b'\xc3\x83\xc2\xaf\xc3\x82\xc2\xb8\xc3\x82\xc2\x8f', b'')

with open(path, 'wb') as f:
    f.write(data)
print("Done")

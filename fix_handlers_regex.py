import os
import re

def fix_handlers_final():
    path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"
    if not os.path.exists(path): return

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Define the clean functions
    clean_list_tasks = """async def list_tasks(callback: types.CallbackQuery):
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

    clean_custom_events_menu = """async def handle_custom_events_menu(callback: types.CallbackQuery):
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

    # Replace using regex to match from start of function to end
    content = re.sub(r'async def list_tasks\(callback: types\.CallbackQuery\):.*?await callback\.answer\(\)', clean_list_tasks, content, flags=re.DOTALL)
    content = re.sub(r'async def handle_custom_events_menu\(callback: types\.CallbackQuery\):.*?await callback\.answer\(\)', clean_custom_events_menu, content, flags=re.DOTALL)

    # Global cleanup for some recurring patterns
    content = content.replace("ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â°", "⏳")
    content = content.replace("ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â³", "🆕")
    content = content.replace("ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â", "") # Clean variation selector artifacts
    content = content.replace("ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â", "•")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed handlers.py with regex")

fix_handlers_final()

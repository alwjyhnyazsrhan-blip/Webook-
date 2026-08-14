import os

def fix_handlers():
    path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"
    if not os.path.exists(path): return

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        # Control Center
        if 'مركز التحكم والاعدادات' in line and 'await safe_edit_text' in line:
            line = '    await safe_edit_text(callback.message, "⚙️ <b>مركز التحكم والاعدادات</b>", reply_markup=builder.as_markup())\n'
        
        # Ongoing Operations
        if 'العمليات الجارية' in line and 'text =' in line:
            line = '        text = "📊 <b>العمليات الجارية:</b>\\n──────────────────\\n"\n'
        
        # لا توجد عمليات نشطة
        if 'لا توجد عمليات نشطة' in line and 'text +=' in line:
            line = '            text += "<i>لا توجد عمليات نشطة.</i>\\n"\n'

        # Task detail
        if 'تفاصيل المهمة' in line and 'text =' in line:
            line = '        text = (f"📋 <b>تفاصيل المهمة #{task.id}</b>\\n" "──────────────────\\n")\n'

        # Status icons
        if '"CREATED":' in line and 'status_icon =' in line:
            line = '            status_icon = {"CREATED": "🆕", "SEARCHING": "🔍", "HOLDING": "🔒", "RESERVED": "✅", "FAILED": "❌", "EXPIRED": "💀"}.get(t.status, "⚡")\n'

        # Separators
        if 'ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â' in line:
            line = line.replace('ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â', '─')
        
        # Warning icons
        if '\\u26a0ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â' in line:
            line = line.replace('\\u26a0ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â', '⚠️')
        if '\u26a0ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â' in line:
            line = line.replace('\u26a0ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â', '⚠️')

        new_lines.append(line)

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Fixed handlers.py")

fix_handlers()


import os

path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if 'result.get("error")' in line and 'if' in line:
        # Start of the block we want to replace
        new_lines.append(line)
        new_lines.append('        await safe_answer_text(message, f"❌ {result[\'error\']}")\n')
        new_lines.append('    else:\n')
        new_lines.append('        profile = result.get("profile", {})\n')
        new_lines.append('        name = profile.get("first_name", "")\n')
        new_lines.append('        email = result.get("email", "")\n')
        new_lines.append('        role_ar = {"SNIPER": "قنص", "EXTENSION": "تمديد", "MONITOR": "مراقبة"}.get(role, role)\n')
        new_lines.append('        \n')
        new_lines.append('        # Check for AUTH_REQUIRED tasks to resume\n')
        new_lines.append('        async with AsyncSessionLocal() as db:\n')
        new_lines.append('            from database.models.reservation import ReservationTask, TaskStatus\n')
        new_lines.append('            stmt = select(ReservationTask).where(\n')
        new_lines.append('                ReservationTask.user_id == message.from_user.id,\n')
        new_lines.append('                ReservationTask.status == TaskStatus.AUTH_REQUIRED.value\n')
        new_lines.append('            ).order_by(ReservationTask.updated_at.desc())\n')
        new_lines.append('            pending = (await db.execute(stmt)).scalars().first()\n')
        new_lines.append('            \n')
        new_lines.append('            resume_builder = InlineKeyboardBuilder()\n')
        new_lines.append('            resume_text = ""\n')
        new_lines.append('            if pending:\n')
        new_lines.append('                resume_builder.row(types.InlineKeyboardButton(\n')
        new_lines.append('                    text=f"🚀 استئناف المهمة #{pending.id}", \n')
        new_lines.append('                    callback_data=f"exec_b:{pending.id}"\n')
        new_lines.append('                ))\n')
        new_lines.append('                resume_text = f"\\n\\n💡 <b>لديك مهمة معلقة:</b> #{pending.id}\\nيمكنك الضغط على الزر أدناه لاستئناف القنص فوراً."\n')
        new_lines.append('\n')
        new_lines.append('            await safe_answer_text(message, \n')
        new_lines.append('                f"✅ <b>تم ربط الحساب!</b>\\n"\n')
        new_lines.append('                f"👤 {name} ({email})\\n"\n')
        new_lines.append('                f"🏷️ الدور: {role_ar}{resume_text}",\n')
        new_lines.append('                reply_markup=resume_builder.as_markup() if pending else None\n')
        new_lines.append('            )\n')
        skip = True
        continue
    
    if skip:
        if 'await state.clear()' in line:
            new_lines.append('    await state.clear()\n')
            new_lines.append('    if not result.get("status") in ["created", "updated"]:\n')
            new_lines.append('         await handle_start(message)\n')
            skip = False
        continue
    
    new_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("SUCCESS")

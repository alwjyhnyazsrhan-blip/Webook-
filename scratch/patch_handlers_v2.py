
import os

path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Replace lines 1445 to 1459 (0-indexed: 1444 to 1459)
# Note: inclusive of 1459 which is '    await handle_start(message)'

replacement = """    if result.get("error"):
        await safe_answer_text(message, f"❌ {result['error']}")
    else:
        profile = result.get("profile", {})
        name = profile.get("first_name", "")
        email = result.get("email", "")
        role_ar = {"SNIPER": "قنص", "EXTENSION": "تمديد", "MONITOR": "مراقبة"}.get(role, role)
        
        # Check for AUTH_REQUIRED tasks to resume
        async with AsyncSessionLocal() as db:
            from database.models.reservation import ReservationTask, TaskStatus
            stmt = select(ReservationTask).where(
                ReservationTask.user_id == message.from_user.id,
                ReservationTask.status == TaskStatus.AUTH_REQUIRED.value
            ).order_by(ReservationTask.updated_at.desc())
            pending = (await db.execute(stmt)).scalars().first()
            
            resume_builder = InlineKeyboardBuilder()
            resume_text = ""
            if pending:
                resume_builder.row(types.InlineKeyboardButton(
                    text=f"🚀 استئناف المهمة #{pending.id}", 
                    callback_data=f"exec_b:{pending.id}"
                ))
                resume_text = f"\\n\\n💡 <b>لديك مهمة معلقة:</b> #{pending.id}\\nيمكنك الضغط على الزر أدناه لاستئناف القنص فوراً."

            await safe_answer_text(message, 
                f"✅ <b>تم ربط الحساب!</b>\\n"
                f"👤 {name} ({email})\\n"
                f"🏷️ الدور: {role_ar}{resume_text}",
                reply_markup=resume_builder.as_markup() if pending else None
            )
            
    await state.clear()
    if not result.get("status") in ["created", "updated"]:
         await handle_start(message)
"""

# Be careful with line indices. 1445 is index 1444. 1459 is index 1458.
# We want to replace from 1445 to 1459 inclusive.
lines[1444:1459] = [line + '\n' for line in replacement.split('\n')]

with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("SUCCESS_BY_LINE")

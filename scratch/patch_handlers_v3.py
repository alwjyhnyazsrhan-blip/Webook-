
import os

path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

target = """    if result.get("error"):
        await safe_answer_text(message, f"\\u274c {result['error']}")
    else:
        profile = result.get("profile", {})
        name = profile.get("first_name", "")
        email = result.get("email", "")
        role_ar = {"SNIPER": "\\u0642\\u0646\\u0635", "EXTENSION": "\\u062a\\u0645\\u062f\\u064a\\u062f", "MONITOR": "\\u0645\\u0631\\u0627\\u0642\\u0628\\u0629"}.get(role, role)
        await safe_answer_text(message, 
            f"\\u2705 **\\u062a\\u0645 \\u0631\\u0628\\u0637 \\u0627\\u0644\\u062d\\u0633\\u0627\\u0628!**\\n"
            f"\\U0001f464 {name} ({email})\\n"
            f"\\U0001f3f7  \\u0627\\u0644\\u062f\\u0648\\u0631: {role_ar}"
            f"\\U0001f3f7  \\u0627\\u0644\\u062f\\u0648\\u0631: {role_ar}"
        )
    await state.clear()
    await handle_start(message)"""

# Note the literal \u escapes in the target string above to match the file content if it was saved that way.
# But wait, view_file showed them as literal arabic if I recall correctly? 
# Actually, the view_file output showed \u0642...

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
         await handle_start(message)"""

if target in content:
    content = content.replace(target, replacement)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS_REPLACED")
else:
    print("TARGET_NOT_FOUND")
    # Try with literal arabic in target
    target_literal = """    if result.get("error"):
        await safe_answer_text(message, f"❌ {result['error']}")
    else:
        profile = result.get("profile", {})
        name = profile.get("first_name", "")
        email = result.get("email", "")
        role_ar = {"SNIPER": "قنص", "EXTENSION": "تمديد", "MONITOR": "مراقبة"}.get(role, role)
        await safe_answer_text(message, 
            f"✅ **تم ربط الحساب!**\\n"
            f"👤 {name} ({email})\\n"
            f"🏷️  الدور: {role_ar}"
            f"🏷️  الدور: {role_ar}"
        )
    await state.clear()
    await handle_start(message)"""
    if target_literal in content:
        content = content.replace(target_literal, replacement)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("SUCCESS_REPLACED_LITERAL")
    else:
        print("LITERAL_TARGET_NOT_FOUND")


import os
import re

path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Search for the block starting with if result.get("error"): inside handle_token_submission
# and ending before Speed Booking header.

pattern = re.compile(r'async def handle_token_submission.*?if result\.get\("error"\):.*?await handle_start\(message\)', re.DOTALL)

replacement = """async def handle_token_submission(message: types.Message, state: FSMContext):
    token = message.text.replace("Bearer ", "").strip()
    await safe_answer_text(message, "🔄 **جاري التحقق من التوكن...**")

    # Get role from state (set by link_sniper or link_extension)
    data = await state.get_data()
    role = data.get("link_role", "SNIPER")

    from services.account.manager import AccountManager
    async with AsyncSessionLocal() as db:
        mgr = AccountManager(db)
        result = await mgr.add_account_via_token(token, role=role)

    if result.get("error"):
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

new_content = pattern.sub(replacement, content)

if new_content != content:
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("SUCCESS_REGEX_REPLACED")
else:
    print("REGEX_MATCH_FAILED")

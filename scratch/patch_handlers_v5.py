
import os

path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"
print(f"Checking path: {path}")
if not os.path.exists(path):
    print("PATH NOT FOUND")
    exit(1)

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

found = False
for i, line in enumerate(lines):
    if "async def handle_token_submission" in line:
        print(f"FOUND handle_token_submission AT LINE {i+1}")
        found = True
        # Find end of function
        j = i + 1
        while j < len(lines) and not (lines[j].startswith("async def") or lines[j].startswith("# ──")):
             j += 1
        
        print(f"REPLACING FROM {i+1} TO {j}")
        
        replacement = [
            f"async def handle_token_submission(message: types.Message, state: FSMContext):\n",
            f"    token = message.text.replace(\"Bearer \", \"\").strip()\n",
            f"    await safe_answer_text(message, \"🔄 **جاري التحقق من التوكن...**\")\n",
            f"\n",
            f"    # Get role from state (set by link_sniper or link_extension)\n",
            f"    data = await state.get_data()\n",
            f"    role = data.get(\"link_role\", \"SNIPER\")\n",
            f"\n",
            f"    from services.account.manager import AccountManager\n",
            f"    async with AsyncSessionLocal() as db:\n",
            f"        mgr = AccountManager(db)\n",
            f"        result = await mgr.add_account_via_token(token, role=role)\n",
            f"\n",
            f"    if result.get(\"error\"):\n",
            f"        await safe_answer_text(message, f\"❌ {{result['error']}}\")\n",
            f"    else:\n",
            f"        profile = result.get(\"profile\", {{}})\n",
            f"        name = profile.get(\"first_name\", \"\")\n",
            f"        email = result.get(\"email\", \"\")\n",
            f"        role_ar = {{\"SNIPER\": \"قنص\", \"EXTENSION\": \"تمديد\", \"MONITOR\": \"مراقبة\"}}.get(role, role)\n",
            f"        \n",
            f"        # Check for AUTH_REQUIRED tasks to resume\n",
            f"        async with AsyncSessionLocal() as db:\n",
            f"            from database.models.reservation import ReservationTask, TaskStatus\n",
            f"            stmt = select(ReservationTask).where(\n",
            f"                ReservationTask.user_id == message.from_user.id,\n",
            f"                ReservationTask.status == TaskStatus.AUTH_REQUIRED.value\n",
            f"            ).order_by(ReservationTask.updated_at.desc())\n",
            f"            pending = (await db.execute(stmt)).scalars().first()\n",
            f"            \n",
            f"            resume_builder = InlineKeyboardBuilder()\n",
            f"            resume_text = \"\"\n",
            f"            if pending:\n",
            f"                resume_builder.row(types.InlineKeyboardButton(\n",
            f"                    text=f\"🚀 استئناف المهمة #{{pending.id}}\", \n",
            f"                    callback_data=f\"exec_b:{{pending.id}}\"\n",
            f"                ))\n",
            f"                resume_text = f\"\\n\\n💡 <b>لديك مهمة معلقة:</b> #{{pending.id}}\\nيمكنك الضغط على الزر أدناه لاستئناف القنص فوراً.\"\n",
            f"\n",
            f"            await safe_answer_text(message, \n",
            f"                f\"✅ <b>تم ربط الحساب!</b>\\n\"\n",
            f"                f\"👤 {{name}} ({{email}})\\n\"\n",
            f"                f\"🏷️ الدور: {{role_ar}}{{resume_text}}\",\n",
            f"                reply_markup=resume_builder.as_markup() if pending else None\n",
            f"            )\n",
            f"            \n",
            f"    await state.clear()\n",
            f"    if not result.get(\"status\") in [\"created\", \"updated\"]:\n",
            f"         await handle_start(message)\n"
        ]
        
        lines[i:j] = replacement
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("SUCCESS_PATCH_BY_DISCOVERY")
        break

if not found:
    print("NOT_FOUND")

import sys

with open("apps/bot/handlers.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the handle_start block and replace it correctly
start_line = -1
end_line = -1
for i, line in enumerate(lines):
    if "async def handle_start" in line:
        start_line = i
    if start_line != -1 and "await safe_send_media(message, dashboard, builder.as_markup())" in line:
        end_line = i
        break

if start_line != -1 and end_line != -1:
    new_handle_start = [
        "async def handle_start(message: types.Message):\n",
        "    async with AsyncSessionLocal() as db:\n",
        "        acc_repo = AccountRepository(db)\n",
        "        res_repo = ReservationRepository(db)\n",
        "        active_accs = len(await acc_repo.get_available_accounts())\n",
        "        active_tasks = len(await res_repo.get_active_tasks())\n",
        "    \n",
        "    dashboard = (\n",
        "        \"\U0001f680 <b>Webook Sniper Elite</b>\\n\\n\"\n",
        "        f\"\U0001f3af \u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0627\u0644\u064a\u0648\u0645: {61}\\n\"\n",
        "        \"\u26a1ï¸ \u0627\u0644\u0633\u0631\u0639\u0629: \u0641\u0627\u0626\u0642\u0629\\n\"\n",
        "        \"\U0001f7e2 \u0627\u0644\u0646\u0638\u0627\u0645: \u0645\u062a\u0635\u0644\\n\"\n",
        "        \"\U0001f6e1 \u0627\u0644\u062d\u0645\u0627\u064a\u0629: \u0645\u0641\u0639\u0644\u0629\\n\"\n",
        "        f\"\U0001f464 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a: {active_accs} \u0646\u0634\u0637\u0629\\n\\n\"\n",
        "        \"â”â”â”â”â”â”â”â”â”â”â”â”â”â”\\n\\n\"\n",
        "        \"\u2705 \u062d\u062c\u0632 \u0645\u062a\u0627\u062d \u0628\u062d\u0633\u0627\u0628 \u0623\u0648 \u0628\u062f\u0648\u0646 \u062d\u0633\u0627\u0628\\n\"\n",
        "        \"\u2705 \u0639\u0645\u0648\u0644\u0629 \u0645\u0645\u064a\u0632\u0629\\n\"\n",
        "        \"\u2705 \u0628\u0648\u062a\u0627\u062a \u0641\u0627\u0626\u0642\u0629 \u0627\u0644\u0633\u0631\u0639\u0629 \u0644\u0644\u062d\u062c\u0632\\n\"\n",
        "        \"\u2705 \u062d\u0645\u0627\u064a\u0629 \u0642\u0648\u064a\u0629 \u0636\u062f \u0627\u0644\u0628\u0627\u0646\\n\"\n",
        "        \"\u2705 \u0625\u0645\u0643\u0627\u0646\u064a\u0629 \u0646\u0642\u0644 \u0627\u0644\u062a\u0630\u0627\u0643\u0631\\n\"\n",
        "        \"\u2705 \u062d\u062c\u0632 \u0645\u0628\u0627\u0634\u0631 \u0639\u0628\u0631 \u0631\u0627\u0628\u0637 \u0627\u0644\u062f\u0641\u0639\\n\"\n",
        "        \"\u2705 \u062a\u062c\u0627\u0648\u0632 \u0637\u0627\u0628\u0648\u0631\\n\"\n",
        "    )\n",
        "\n",
        "    builder = InlineKeyboardBuilder()\n",
        "    builder.row(types.InlineKeyboardButton(text=\"\U0001f680 \u0627\u0628\u062f\u0623 \u062d\u062c\u0632 \u062c\u062f\u064a\u062f\", callback_data=\"booking_start\"))\n",
        "    builder.row(\n",
        "        types.InlineKeyboardButton(text=\"\U0001f3af \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0627\u0644\u0634\u0627\u0626\u0639\u0629\", callback_data=\"all_events\"),\n",
        "        types.InlineKeyboardButton(text=\"\u26bd \u0627\u0644\u062f\u0648\u0631\u064a \u0627\u0644\u0633\u0639\u0648\u062f\u064a\", callback_data=\"browse_org:saudi-pro-league\")\n",
        "    )\n",
        "    builder.row(\n",
        "        types.InlineKeyboardButton(text=\"\U0001f3b5 \u0627\u0644\u062d\u0641\u0644\u0627\u062a\", callback_data=\"browse_org:concerts\"),\n",
        "        types.InlineKeyboardButton(text=\"\U0001f39f \u062d\u062c\u0648\u0632\u0627\u062a\u064a\", callback_data=\"list_tasks\")\n",
        "    )\n",
        "    builder.row(\n",
        "        types.InlineKeyboardButton(text=\"\U0001f464 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a\", callback_data=\"list_accounts\"),\n",
        "        types.InlineKeyboardButton(text=\"\u2699ï¸ \u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a\", callback_data=\"custom_events_menu\")\n",
        "    )\n",
        "    builder.row(types.InlineKeyboardButton(text=\"\U0001f504 \u062a\u062d\u062f\u064a\u062b\", callback_data=\"sync_now\"))\n",
        "\n",
        "    if isinstance(message, types.Message):\n",
        "        await message.answer(dashboard, parse_mode=\"HTML\", reply_markup=builder.as_markup())\n",
        "    else:\n",
        "        await safe_send_media(message, dashboard, builder.as_markup())\n"
    ]
    lines[start_line : end_line + 1] = new_handle_start
    
    with open("apps/bot/handlers.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Successfully restored handle_start")
else:
    print(f"Could not find handle_start boundaries: {start_line} to {end_line}")

with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\apps\bot\main.py', 'rb') as f:
    content = f.read()

lines = content.decode('utf-8', errors='replace').split('\n')
lines[95] = '            await event.update.callback_query.answer("\u26a0ï¸ \u062d\u062f\u062b \u062e\u0637\u0623 \u063a\u064a\u0631 \u0645\u062a\u0648\u0642\u0639. \u0644\u0645 \u062a\u0633\u062c\u0644 \u0627\u0644\u062a\u0641\u0627\u0635\u064a\u0644.", show_alert=True)'
lines[96] = '        elif hasattr(event, "update") and event.update.message:'
lines[97] = '            await event.update.message.answer("\u26a0ï¸ \u062d\u062f\u062b \u062e\u0637\u0623 \u063a\u064a\u0631 \u0645\u062a\u0648\u0642\u0639. \u0644\u0645 \u062a\u0633\u062c\u0644 \u0627\u0644\u062a\u0641\u0627\u0635\u064a\u0644.")'

result = '\n'.join(lines).encode('utf-8')
with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\apps\bot\main.py', 'wb') as f:
    f.write(result)
print('Done')

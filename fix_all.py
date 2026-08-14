import os
import re

def fix_file(filepath):
    with open(filepath, 'rb') as f:
        content = f.read()
    
    # Check if file has the problematic pattern
    if b'callback_query' not in content and b'callback_query' not in content:
        print(f"Skipping {filepath} - no callback issues")
        return
    
    text = content.decode('utf-8', errors='replace')
    original = text
    
    # Fix 1: callback_query -> callback_query
    text = text.replace('callback_query', 'callback_query')
    
    # Fix 2: corrupted Arabic strings (lines with show_alert=True)
    # Pattern: await event.update.callback_query.answer("...") with corrupted text
    text = re.sub(
        r'await event\.update\.callback_query\.answer\("[^"]*show_alert=True\)',
        'await event.update.callback_query.answer("\u26a0ï¸ \u062d\u062f\u062b \u062e\u0637\u0623 \u063a\u064a\u0631 \u0645\u062a\u0648\u0642\u0639. \u0644\u0645 \u062a\u0633\u062c\u0644 \u0627\u0644\u062a\u0641\u0627\u0635\u064a\u0644.", show_alert=True)',
        text
    )
    text = re.sub(
        r'await event\.update\.message\.answer\("[^"]*\)',
        'await event.update.message.answer("\u26a0ï¸ \u062d\u062f\u062b \u062e\u0637\u0623 \u063a\u064a\u0631 \u0645\u062a\u0648\u0642\u0639. \u0644\u0645 \u062a\u0633\u062c\u0644 \u0627\u0644\u062a\u0641\u0627\u0635\u064a\u0644.")',
        text
    )
    
    # Fix 3: Remove any remaining control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    if text != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Fixed {filepath}")
    else:
        print(f"No changes needed for {filepath}")

# Fix main.py
fix_file(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\apps\bot\main.py')
print("Done!")

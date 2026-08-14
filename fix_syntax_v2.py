import os

handlers_path = r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py"

with open(handlers_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the specific broken InlineKeyboardBuilder.row() calls
content = content.replace("InlineKeyboardBuilder().row()", "InlineKeyboardBuilder().row(")

# Fix broken reply_markup=.as_markup() issues
# We want to match .as_markup(), trace_ctx=trace_ctx) and ensure there's a balanced set of parens BEFORE it.
# Actually, the replacement script V5 messed up the end_paren.

with open(handlers_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Manual-ish fix complete.")

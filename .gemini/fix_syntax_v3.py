import re
import os

handlers_path = r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py"

with open(handlers_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the missing closing paren for reply_markup=...as_markup()
# Pattern: reply_markup=...as_markup() but it should be followed by ) or , 
# Actually, the lines found by Select-String ended with as_markup()

# We'll look for:
# await callback.message.edit_text(..., reply_markup=...as_markup()
# and replace it with:
# await traced_callback_edit(callback, ..., reply_markup=...as_markup(), trace_ctx=trace_ctx)

# 1. First, convert all remaining callback.message.edit_text(...) to traced_callback_edit(callback, ...)
def sub_callback_edit(m):
    args = m.group(1).strip()
    # If it ends with as_markup(), it's missing a closing paren from the previous mess
    if args.endswith("as_markup()"):
        args += ")"
    
    if "trace_ctx=" in args:
        return f"await traced_callback_edit(callback, {args})"
    return f"await traced_callback_edit(callback, {args}, trace_ctx=trace_ctx)"

content = re.sub(r"await callback\.message\.edit_text\((.*?)\)", sub_callback_edit, content, flags=re.DOTALL)

# 2. Cleanup double trace_ctx
content = content.replace(", trace_ctx=trace_ctx, trace_ctx=trace_ctx", ", trace_ctx=trace_ctx")
content = content.replace("), trace_ctx=trace_ctx)", "), trace_ctx=trace_ctx)") # Ensure balance

with open(handlers_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Syntax fix V3 complete.")

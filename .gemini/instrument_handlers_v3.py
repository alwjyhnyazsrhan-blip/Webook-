import re
import os

handlers_path = r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py"

with open(handlers_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Imports
new_imports = "from core.tracing.telegram_instruments import traced_send_message, traced_edit_text, traced_answer_callback, traced_message_edit, traced_message_answer, traced_callback_edit"
content = re.sub(r"from core.tracing.telegram_instruments import .*", new_imports, content)

# Helper to fix empty arguments
def fix_args(args):
    args = args.strip()
    if not args:
        return ""
    return args + ", "

# 2. Replace callback.message.edit_text(...) -> traced_callback_edit(callback, ...)
# Pattern: await callback.message.edit_text(...)
def sub_callback_edit(m):
    args = m.group(1).strip()
    if "trace_ctx=" in args:
        return f"await traced_callback_edit(callback, {args})"
    return f"await traced_callback_edit(callback, {fix_args(args)}trace_ctx=trace_ctx)"

content = re.sub(r"await callback\.message\.edit_text\((.*?)\)", sub_callback_edit, content, flags=re.DOTALL)

# 3. Replace message.edit_text(...) -> traced_message_edit(message, ...)
def sub_message_edit(m):
    args = m.group(1).strip()
    if "trace_ctx=" in args:
        return f"await traced_message_edit(message, {args})"
    return f"await traced_message_edit(message, {fix_args(args)}trace_ctx=trace_ctx)"

content = re.sub(r"await message\.edit_text\((.*?)\)", sub_message_edit, content, flags=re.DOTALL)

# 4. Replace message.answer(...) -> traced_message_answer(message, ...)
def sub_message_answer(m):
    args = m.group(1).strip()
    if "trace_ctx=" in args:
        return f"await traced_message_answer(message, {args})"
    return f"await traced_message_answer(message, {fix_args(args)}trace_ctx=trace_ctx)"

content = re.sub(r"await message\.answer\((.*?)\)", sub_message_answer, content, flags=re.DOTALL)

# 5. Replace callback.answer(...) -> traced_answer_callback(callback, ...)
def sub_callback_answer(m):
    args = m.group(1).strip()
    if "trace_ctx=" in args:
        return f"await traced_answer_callback(callback, {args})"
    return f"await traced_answer_callback(callback, {fix_args(args)}trace_ctx=trace_ctx)"

content = re.sub(r"await callback\.answer\((.*?)\)", sub_callback_answer, content, flags=re.DOTALL)

# 6. Final Cleanup: fix ", , " or ", trace_ctx=trace_ctx, trace_ctx=trace_ctx"
content = content.replace(", , ", ", ")
content = content.replace(", trace_ctx=trace_ctx, trace_ctx=trace_ctx", ", trace_ctx=trace_ctx")

with open(handlers_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replacement complete.")

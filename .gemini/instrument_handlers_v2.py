import re
import os

handlers_path = r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py"

with open(handlers_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Imports
new_imports = "from core.tracing.telegram_instruments import traced_send_message, traced_edit_text, traced_answer_callback, traced_message_edit, traced_message_answer, traced_callback_edit"
content = re.sub(r"from core.tracing.telegram_instruments import .*", new_imports, content)

# 2. Replace callback.message.edit_text(...) -> traced_callback_edit(callback, ...)
# Pattern: await callback.message.edit_text(text, ...)
# Replacement: await traced_callback_edit(callback, text, trace_ctx=trace_ctx, ...)
def replace_callback_edit(match):
    text_and_args = match.group(1)
    # Check if trace_ctx is already there
    if "trace_ctx=" not in text_and_args:
        # Try to insert trace_ctx=trace_ctx before the closing parenthesis
        if text_and_args.strip().endswith(")"):
             # Handle nested parentheses if any (simple approach)
             return f"await traced_callback_edit(callback, {text_and_args[:-1]}, trace_ctx=trace_ctx)"
        return f"await traced_callback_edit(callback, {text_and_args}, trace_ctx=trace_ctx)"
    return f"await traced_callback_edit(callback, {text_and_args})"

content = re.sub(r"await callback\.message\.edit_text\((.*)\)", replace_callback_edit, content)

# 3. Replace message.edit_text(...) -> traced_message_edit(message, ...)
content = re.sub(r"await message\.edit_text\((.*)\)", r"await traced_message_edit(message, \1, trace_ctx=trace_ctx)", content)

# 4. Replace message.answer(...) -> traced_message_answer(message, ...)
content = re.sub(r"await message\.answer\((.*)\)", r"await traced_message_answer(message, \1, trace_ctx=trace_ctx)", content)

# 5. Replace callback.answer(...) -> traced_answer_callback(callback, ...)
content = re.sub(r"await callback\.answer\((.*)\)", r"await traced_answer_callback(callback, \1, trace_ctx=trace_ctx)", content)

# 6. Cleanup duplicate trace_ctx=trace_ctx
content = content.replace("trace_ctx=trace_ctx, trace_ctx=trace_ctx", "trace_ctx=trace_ctx")

with open(handlers_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replacement complete.")

import os

def balance_parens(text, start_index):
    count = 0
    for i in range(start_index, len(text)):
        if text[i] == '(':
            count += 1
        elif text[i] == ')':
            count -= 1
            if count == 0:
                return i
    return -1

handlers_path = r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py"

with open(handlers_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the mess from the previous run first
content = content.replace(", trace_ctx=trace_ctx)", ")") # Dangerous but maybe works for now
content = content.replace(", trace_ctx=trace_ctx", "") # More dangerous

# Restore imports
content = "from core.tracing.telegram_instruments import traced_send_message, traced_edit_text, traced_answer_callback, traced_message_edit, traced_message_answer, traced_callback_edit\n" + content

def replace_calls(content, old_call_prefix, new_func_name, extra_arg=""):
    index = 0
    while True:
        index = content.find(old_call_prefix, index)
        if index == -1:
            break
        
        start_paren = content.find("(", index)
        if start_paren == -1:
            index += 1
            continue
            
        end_paren = balance_parens(content, start_paren)
        if end_paren == -1:
            index += 1
            continue
            
        args = content[start_paren+1 : end_paren].strip()
        
        # Construct new call
        new_args = ""
        if extra_arg:
            new_args = extra_arg
            if args:
                new_args += ", " + args
        else:
            new_args = args
            
        if "trace_ctx=" not in new_args:
            if new_args:
                new_args += ", trace_ctx=trace_ctx"
            else:
                new_args = "trace_ctx=trace_ctx"
        
        new_call = f"await {new_func_name}({new_args})"
        
        # Replace the whole await ...()
        # Find the 'await' before the old_call_prefix
        await_index = content.rfind("await", 0, index)
        if await_index != -1 and (index - await_index) < 10:
             content = content[:await_index] + new_call + content[end_paren+1:]
             index = await_index + len(new_call)
        else:
             index += 1
    return content

# 1. Replace callback.message.edit_text(...) -> traced_callback_edit(callback, ...)
content = replace_calls(content, "callback.message.edit_text", "traced_callback_edit", "callback")

# 2. Replace message.edit_text(...) -> traced_message_edit(message, ...)
content = replace_calls(content, "message.edit_text", "traced_message_edit", "message")

# 3. Replace message.answer(...) -> traced_message_answer(message, ...)
content = replace_calls(content, "message.answer", "traced_message_answer", "message")

# 4. Replace callback.answer(...) -> traced_answer_callback(callback, ...)
content = replace_calls(content, "callback.answer", "traced_answer_callback", "callback")

with open(handlers_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replacement complete with balancer.")

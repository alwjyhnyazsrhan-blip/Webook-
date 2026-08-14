import os

def balance_parens(text, start_index):
    count = 0
    found_first = False
    for i in range(start_index, len(text)):
        if text[i] == '(':
            count += 1
            found_first = True
        elif text[i] == ')':
            count -= 1
            if found_first and count == 0:
                return i
    return -1

handlers_path = r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py"

with open(handlers_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. CLEANUP messy calls from previous failed runs
# Specifically fix things like (..., trace_ctx=trace_ctx) inside other calls
# We'll do this by looking for 'traced_' calls and re-balancing them if they look wrong.
# Actually, it's easier to just REVERT to a state where we use standard aiogram calls and then re-run the balancer.

def revert_to_standard(content):
    # This is a bit risky but we can try to undo the 'traced_' replacements
    content = content.replace("traced_callback_edit(callback, ", "callback.message.edit_text(")
    content = content.replace("traced_message_edit(message, ", "message.edit_text(")
    content = content.replace("traced_message_answer(message, ", "message.answer(")
    content = content.replace("traced_answer_callback(callback, ", "callback.answer(")
    content = content.replace("traced_answer_callback(callback)", "callback.answer()")
    
    # Clean up any residual trace_ctx=trace_ctx we added
    # We only want to remove it if it was added by us.
    # But wait, some handlers might already have it? No, standard aiogram doesn't use it.
    # So we can remove ', trace_ctx=trace_ctx'
    content = content.replace(", trace_ctx=trace_ctx", "")
    content = content.replace("trace_ctx=trace_ctx", "")
    return content

content = revert_to_standard(content)

def replace_calls_v2(content, old_call_pattern, new_func_name, extra_arg=""):
    index = 0
    while True:
        index = content.find(old_call_pattern, index)
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
        
        # New args construction
        if extra_arg:
            if args:
                new_args = f"{extra_arg}, {args}, trace_ctx=trace_ctx"
            else:
                new_args = f"{extra_arg}, trace_ctx=trace_ctx"
        else:
            if args:
                new_args = f"{args}, trace_ctx=trace_ctx"
            else:
                new_args = "trace_ctx=trace_ctx"
        
        new_call = f"await {new_func_name}({new_args})"
        
        # Find 'await'
        await_index = content.rfind("await", 0, index)
        if await_index != -1 and (index - await_index) < 20:
            content = content[:await_index] + new_call + content[end_paren+1:]
            index = await_index + len(new_call)
        else:
            index += 1
    return content

# Perform replacements
content = replace_calls_v2(content, "callback.message.edit_text", "traced_callback_edit", "callback")
content = replace_calls_v2(content, "message.edit_text", "traced_message_edit", "message")
content = replace_calls_v2(content, "message.answer", "traced_message_answer", "message")
content = replace_calls_v2(content, "callback.answer", "traced_answer_callback", "callback")

# Final fix for double trace_ctx
content = content.replace("trace_ctx=trace_ctx, trace_ctx=trace_ctx", "trace_ctx=trace_ctx")
content = content.replace(", , ", ", ")

with open(handlers_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replacement complete with V2 balancer.")

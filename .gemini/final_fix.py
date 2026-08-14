import os

handlers_path = r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py"

with open(handlers_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("as_markup(, trace_ctx=trace_ctx)", "as_markup(), trace_ctx=trace_ctx")
content = content.replace("as_markup()trace_ctx=trace_ctx", "as_markup(), trace_ctx=trace_ctx")

with open(handlers_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Final syntax fix complete.")

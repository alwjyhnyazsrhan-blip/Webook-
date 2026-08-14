import os

handlers_path = r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py"

with open(handlers_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    # Look for common syntax errors introduced by previous turns
    # 1. Missing closing paren on traced_ calls
    if "traced_" in line and "reply_markup=" in line and line.count("(") > line.count(")"):
        line = line.rstrip() + ")\n"
    
    # 2. Fix double commas
    line = line.replace(", ,", ",")
    
    fixed_lines.append(line)

with open(handlers_path, "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print("Syntax fix complete.")

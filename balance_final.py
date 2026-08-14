import os

handlers_path = r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py"

with open(handlers_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    if "traced_" in line and "await" in line:
        if line.count("(") > line.count(")"):
            line = line.rstrip() + ")\n"
    fixed_lines.append(line)

with open(handlers_path, "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print("Balanced parens.")

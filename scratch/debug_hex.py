
filepath = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"

with open(filepath, 'rb') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if b"resale[:10]" in line:
        print(f"Line {i+1}: {line.hex()}")
        print(f"Next Line {i+2}: {lines[i+1].hex()}")
        break

with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\modules\webook\client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 396 (index 395) - should be indented
if lines[395].startswith('async def checkout_seated'):
    lines[395] = '    ' + lines[395]

# Fix line 443 (index 442) - should be indented
if lines[442].strip().startswith('async def release_reservation'):
    lines[442] = '    ' + lines[442].lstrip()

with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\modules\webook\client.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed indentation")

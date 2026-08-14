import os
path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"
with open(path, 'rb') as f:
    data = f.read()

print(f"File size: {len(data)}")
print(f"First 100 bytes: {data[:100]}")

idx = data.find(b'handle_custom_events_menu')
print(f"Index of handle_custom_events_menu: {idx}")
if idx != -1:
    print(f"Surrounding bytes: {data[idx-50:idx+100]}")


filepath = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"

with open(filepath, 'rb') as f:
    f.seek(131939 - 5000) # It's a large file, let's seek near where resale check is
    # Wait, I don't know the exact offset.
    # Let's just read the whole thing in binary and find the surrounding text.
    data = f.read()

target = "resale[:10]".encode('utf-8')
idx = data.find(target)
if idx != -1:
    # Print 200 bytes around it
    chunk = data[idx-100:idx+200]
    print(f"Hex: {chunk.hex()}")
    try:
        print(f"Decoded UTF-8: {chunk.decode('utf-8')}")
    except:
        print("Could not decode as UTF-8")
else:
    print("Target not found in binary")

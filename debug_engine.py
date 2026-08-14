with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\services\discovery\engine.py', 'rb') as f:
    content = f.read()
print(f'File size: {len(content)} bytes')
# Find position of the problematic area
text = content.decode('utf-8', errors='replace')
idx = text.find('"slug_in": [')
if idx >= 0:
    print(f'Found slug_in at position {idx}')
    print('Context around it:')
    print(repr(text[idx:idx+200]))
    # Check the lines around it
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'slug_in' in line:
            print(f'Line {i+1}: {repr(line)}')

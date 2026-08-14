import os

def fix_mojibake_binary(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    with open(path, 'rb') as f:
        data = f.read()

    # Define byte patterns
    # ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â  is the result of encoding \ufe0f multiple times.
    # \ufe0f is 0xEF 0xB8 0x8F in UTF-8.
    
    replacements = [
        (b'\xc3\x83\xc2\xaf\xc3\x82\xc2\xb8\xc3\x82\xc2\xbd', b'\xef\xb8\x8f'), # Variation Selector
        (b'\xc3\x83\xc2\xaf\xc3\x82\xc2\xb8\xc3\x82\xc2\x8f', b'\xef\xb8\x8f'), # Variation Selector
        (b'\xc3\x83\xc2\xa2\xc3\x83\xc2\xa2\xc3\x82\xc2\xac\xc3\x82\xc2\xa2', b'\xe2\x80\xa2'), # Bullet point
        (b'\xc3\x83\xc2\xa2\xc3\x82\xc2\xad\xc3\x82\xc2\xa2', b'\xe2\x80\xa2'), # Bullet point
        (b'\xc3\x83\xc2\xa2\xc3\x82\xc2\xac\xc3\x82\xc2\xa2', b'\xe2\x80\xa2'), # Bullet point
        (b'\xc3\x83\xc2\xa2\xc3\x83\xc2\xa2\xc3\x82\xc2\xac\xc3\x82\xc2\xa2', b'\xe2\x80\xa2'), # Bullet
        (b'\xc3\x83\xc2\xa2\xc3\x82\xc2\xad\xc3\x82\xc2\xa2', b'\xe2\x80\xa2'), # Bullet
        (b'\xc3\x83\xc2\xa2\xc3\x82\xc2\xa0\xc3\x82\xc2\xb0', b'\xe2\x8c\x9b'), # Hourglass
        (b'\xc3\x83\xc2\xa2\xc3\x82\xc2\xa0\xc3\x82\xc2\xb3', b'\xf0\x9f\x86\x95'), # NEW
        (b'\xc3\x82\xc2\xa0', b' '), # Non-breaking space
    ]

    for bad, good in replacements:
        data = data.replace(bad, good)
    
    # Custom fix for the Control Center title specifically if binary fails
    # "مركز التحكم والاعدادات" in UTF-8
    arabic_title = "\u0645\u0631\u0643\u0632 \u0627\u0644\u062a\u062d\u0643\u0645 \u0648\u0627\u0644\u0627\u0639\u062f\u0627\u062f\u0627\u062a".encode('utf-8')
    # Search for the corrupted version and replace with clean one
    # We'll just replace the whole line if we find a part of it.
    
    with open(path, 'wb') as f:
        f.write(data)
    print(f"Binary fix applied to {path}")

# Target files
files = [
    r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py",
    r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\services\monitor\ghost.py"
]

for p in files:
    fix_mojibake_binary(p)

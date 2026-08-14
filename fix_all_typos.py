import os
import re

def scan_and_fix_all():
    """Scan all Python files for common typos and fix them."""
    
    # Define all typos to fix
    typos = {
        '_request': '_request',
        'callback_query': 'callback_query',
    }
    
    # Also fix corrupted Arabic strings in specific patterns
    # This will be done file-by-file for precision
    
    fixed_count = 0
    
    for root, dirs, files in os.walk(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed'):
        # Skip scratch and other non-production folders
        if any(x in root for x in ['scratch', '.git', '__pycache__', 'node_modules']):
            continue
            
        for fname in files:
            if not fname.endswith('.py'):
                continue
                
            fpath = os.path.join(root, fname)
            
            with open(fpath, 'rb') as f:
                content = f.read()
            
            original = content.decode('utf-8', errors='replace')
            modified = original
            
            # Fix typos
            for typo, fix in typos.items():
                if typo in modified:
                    modified = modified.replace(typo, fix)
            
            if modified != original:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(modified)
                print(f"Fixed: {fpath}")
                fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

scan_and_fix_all()

import os
import re

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    changed = False
    for i, line in enumerate(lines):
        # Look for f-string with backslash inside {}
        if ('f"' in line or "f'" in line) and '{' in line and '\\' in line:
            # We'll try to find the expression and move it out or use .format()
            # For simplicity, let's just replace f-string with a concatenated version or .format()
            
            # Simple case: f"... {expr_with_backslash} ..."
            # We can change to "... {}".format(expr_with_backslash)
            
            # This regex finds f"text {expr} text" and captures text and expr
            # But it's hard to do perfectly.
            # Let's just fix the specific one reported in handlers_sub.py if we can find it.
            pass
        
        new_lines.append(line)
    
    # Actually, I'll just use a brute-force approach for the reported one
    content = "".join(new_lines)
    
    # Specific fix for handlers_sub.py line 72 area
    if "handlers_sub.py" in file_path:
         content = content.replace(
             "f\"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631')}\\n\"",
             "\"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {}\\n\".format(clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631'))"
         )
         # But wait, it might be inside a tuple (text = ( ... ))
         # So .format() will break it like before.
         # Let's use the variable approach.
         
    return content

# I'll just read handlers_sub.py first to see what's there

import os
import re

file_path = 'apps/bot/handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

def fix_fstring(match):
    prefix = match.group(1)
    expr = match.group(2)
    # If expression contains \u or \U, move it out
    if '\\u' in expr or '\\U' in expr:
        # This is a very complex transformation to do with regex alone reliably
        # We'll just replace the whole f-string if it has a simple ternary/fallback with unicode
        # For now, let's just find them and report or do a simple replace for known patterns
        return match.group(0) # placeholder
    return match.group(0)

# Pattern to find f-strings: f"..." or f'...'
# We want to find cases like f"{... '\u...'}"
# Safer approach: find all occurrences of f-strings and check them

new_content = content
# Pattern for ternary with unicode fallback in f-string
# e.g. f"{val or '\u0627'}"
pattern = re.compile(r'(f\"|f\')(.*?)(\{(?:[^{}]*?(?:\\u|\\U)[^{}]*?)\})(.*?)(\"|\')')

def replacer(match):
    f_start = match.group(1)
    f_content_pre = match.group(2)
    f_expr = match.group(3)
    f_content_post = match.group(4)
    f_end = match.group(5)
    
    # Extract the actual expression inside {}
    expr_inner = f_expr[1:-1]
    
    # Check if it has a backslash
    if '\\' in expr_inner:
        # Simple fix: move the expression to a temporary variable-like structure if possible
        # But we are editing a file, so we need to insert a line before
        # This is too risky with just regex.
        pass
    return match.group(0)

# Final approach: Find every line with f-string and backslash inside {} and manually fix the ones I see
# I'll just search for them and output them so I can fix them.

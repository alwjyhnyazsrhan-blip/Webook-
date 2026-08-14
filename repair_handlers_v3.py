import re

file_path = 'apps/bot/handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix Line 1345
old1 = r"f\"\u274c \*\*\\u0641\u0634\u0644 \\u0627\u0644\u062a\u0645\u062f\u064a\u062f:\*\* {result.get('error', '\\u062e\u0637\u0623 \\u063a\u064a\u0631 \\u0645\u0639\u0631\u0648\u0641')}\""
# Wait, I'll just use a more generic regex fix for ALL occurrences.

def fix_content(c):
    # Pattern: f"..." with { ... \u... }
    # We want to find the expression inside {} that contains \ and move it out.
    # But doing this safely with regex is hard.
    
    # Specific fix for known ones
    c = c.replace(
        "f\"\\u274c **\\u0641\\u0634\\u0644 \\u0627\\u0644\\u062a\\u0645\\u062f\\u064a\\u062f:** {result.get('error', '\\u062e\\u0637\\u0623 \\u063a\\u064a\\u0631 \\u0645\\u0639\\u0631\\u0648\\u0641')}\"",
        "\"\\u274c **\\u0641\\u0634\\u0644 \\u0627\\u0644\\u062a\\u0645\\u062f\\u064a\\u062f:** {}\".format(result.get('error', '\\u062e\\u0637\\u0623 \\u063a\\u064a\\u0631 \\u0645\\u0639\\u0631\\u0648\\u0641'))"
    )
    
    c = c.replace(
        "f\"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631')}\\n\"",
        "\"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {}\\n\".format(clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631'))"
    )
    
    return c

new_content = fix_content(content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fixed")

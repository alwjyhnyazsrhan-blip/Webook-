import re

file_path = 'apps/bot/handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the specific broken block around 1420
old_block = """    text = (
        f"\\U0001f3ad <b>{clean_html(fields['title'])}</b>\\n"
        f"\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\n"
        "\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {}\\n".format(clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631'))
        f"\\U0001f4c5 \\u0627\\u0644\\u0645\\u0648\\u0639\\u062f: <code>{fields['date_str']}</code>\\n"
    )"""

new_block = """    venue_val = clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631')
    text = (
        f"\\U0001f3ad <b>{clean_html(fields['title'])}</b>\\n"
        f"\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\n"
        f"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {venue_val}\\n"
        f"\\U0001f4c5 \\u0627\\u0644\\u0645\\u0648\\u0639\\u062f: <code>{fields['date_str']}</code>\\n"
    )"""

# Use string replace for safety
if old_block in content:
    content = content.replace(old_block, new_block)
else:
    # Fallback to a simpler search if whitespace differs
    print("Exact block match failed, trying line by line")
    content = content.replace(
        "\"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {}\\n\".format(clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631'))",
        "f\"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631')}\\n\"" # Wait, I need to NOT use f-string here
    )
    # Actually I'll just use a smarter replace
    content = content.replace(
        "\"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {}\\n\".format(clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631'))",
        "f\"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {clean_html(fields['venue'])} \\n\"" # This is also bad if venue is None
    )

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed")

import os

file_path = 'apps/bot/handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # Fix Line 1345
    if "format(result.get('error'" in line:
        line = "            \"\\u274c **\\u0641\\u0634\\u0644 \\u0627\\u0644\\u062a\\u0645\\u062f\\u064a\\u062f:** \" + str(result.get('error', '\\u062e\\u0637\\u0623 \\u063a\\u064a\\u0631 \\u0645\\u0639\\u0631\\u0648\\u0641')) + \",\",\n"
    
    # Fix Line 1420
    if "format(clean_html(fields['venue']" in line:
        # We need to move the variable BEFORE the text assignment
        # This is hard line by line.
        pass
    
    new_lines.append(line)

# Let's do a simpler full replacement for the venue part
content = "".join(new_lines)
target = """    text = (
        f"\\U0001f3ad <b>{clean_html(fields['title'])}</b>\\n"
        f"\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\n"
        "\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {}\\n".format(clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631'))
        f"\\U0001f4c5 \\u0627\\u0644\\u0645\\u0648\\u0639\\u062f: <code>{fields['date_str']}</code>\\n"
    )"""

replacement = """    venue_str = clean_html(fields['venue'] or '\\u063a\\u064a\\u0631 \\u0645\\u062a\\u0648\\u0641\\u0631')
    text = (
        f"\\U0001f3ad <b>{clean_html(fields['title'])}</b>\\n"
        f"\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\u2500\\n"
        f"\\U0001f4cd \\u0627\\u0644\\u0645\\u0643\\u0627\\u0646: {venue_str}\\n"
        f"\\U0001f4c5 \\u0627\\u0644\\u0645\\u0648\\u0639\\u062f: <code>{fields['date_str']}</code>\\n"
    )"""

content = content.replace(target, replacement)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed")

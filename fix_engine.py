with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\services\discovery\engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the broken section
start_marker = '                    "slug_in": ['
end_marker = '        event_filter = {'

# The fix - complete the function properly
# Remove the broken event_filter section and replace with complete implementation
old_section = '''        event_filter = {
            **base_filter,
            "AND": [{
                "category": {
                    "slug_in": ['''

new_section = '''        event_filter = {
            **base_filter,
            "AND": [{
                "category": {
                    "slug_in": ["events", "sports", "experience", "music-events", "football", "theater", "kids", "esports", "activities-adventures", "restaurants"]
                }
            }]
        }'''

if start_marker in content:
    # Find the full section to replace
    old_start = content.find('        event_filter = {')
    if old_start > 0:
        # Find where this section ends (next function definition)
        next_func = content.find('\n    async def ', old_start)
        if next_func > 0:
            # Get everything after this section
            after_section = content[next_func:]
            content = content[:old_start] + new_section + '\n' + after_section

with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\services\discovery\engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed _sync_from_contentful function')

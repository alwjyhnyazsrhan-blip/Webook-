with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\modules\webook\client.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix _request -> _request
count = content.count('_request')
content = content.replace('_request', '_request')
print(f"Fixed {count} occurrences of _request -> _request")

with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\modules\webook\client.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")

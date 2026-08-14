import ast
with open(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\modules\webook\client.py', 'r', encoding='utf-8') as f:
    content = f.read()
try:
    ast.parse(content)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax Error at line {e.lineno}: {e.msg}")
    # Show context
    lines = content.split('\n')
    for i in range(max(0, e.lineno-5), min(len(lines), e.lineno+5)):
        marker = ">>>" if i+1 == e.lineno else "   "
        print(f"{marker} {i+1}: {repr(lines[i])}")

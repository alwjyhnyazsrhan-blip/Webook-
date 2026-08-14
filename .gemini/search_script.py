import os

def search_text(root_dir, text):
    for root, dirs, files in os.walk(root_dir):
        if ".git" in root or "__pycache__" in root or ".gemini" in root:
            continue
        for file in files:
            if not file.endswith(('.py', '.env', '.yml', '.txt', '.md')):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if text in content:
                        print(f"FOUND in {path}")
            except:
                try:
                    with open(path, 'r', encoding='latin-1') as f:
                        content = f.read()
                        if text in content:
                            print(f"FOUND in {path}")
                except:
                    pass

if __name__ == "__main__":
    search_text(".", "ØªÙ… ØªØ­Ø¯ÙŠØ«Ù‡Ø§")
    search_text(".", "18 ÙØ¹Ø§Ù„ÙŠØ©")

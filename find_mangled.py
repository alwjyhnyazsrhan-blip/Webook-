import os

def find_mangled():
    target = "\U0001f3af"
    root = "."
    for dirpath, dirnames, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(".py"):
                path = os.path.join(dirpath, f)
                try:
                    # Try reading as latin-1 to see if we can find the literal mangled bytes
                    content = open(path, 'r', encoding='latin-1').read()
                    if target in content:
                        print(f"FOUND IN {path}")
                        # Find line number
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if target in line:
                                print(f"Line {i+1}: {line}")
                except:
                    pass

if __name__ == "__main__":
    find_mangled()

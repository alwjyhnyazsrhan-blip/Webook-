import os
import py_compile
import sys

# Set encoding for windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_all_syntax(root_dir):
    print(f"Checking syntax in {root_dir}...")
    errors = 0
    checked = 0
    for root, dirs, files in os.walk(root_dir):
        if ".venv" in root or "__pycache__" in root or ".git" in root or ".gemini" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                checked += 1
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as e:
                    print(f"FAIL: {path}")
                    # Use repr to avoid encoding issues when printing the error message
                    print(repr(e))
                    errors += 1
                except Exception as e:
                    print(f"ERROR: {path} - {type(e).__name__}: {str(e)}")
                    errors += 1
    
    print(f"Checked {checked} files.")
    if errors == 0:
        print("All files passed syntax check.")
    else:
        print(f"Found {errors} syntax errors.")

if __name__ == "__main__":
    check_all_syntax(".")

import os

file_path = "apps/bot/handlers.py"
with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

targets = [2016, 2043, 2072, 2091, 2159, 2160, 2165, 2212, 2333]
for t in targets:
    start = max(0, t - 15)
    end = min(len(lines), t + 10)
    print(f"=== Line {t} ===")
    for idx in range(start, end):
        print(f"{idx+1}: {lines[idx]}", end="")
    print("\n" + "="*40 + "\n")

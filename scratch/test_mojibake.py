
import html
import re
import sys

# Ensure stdout handles UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

_MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ï", "", "Æ", "€")
_MOJIBAKE_REPLACEMENTS = {
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â": "\ufe0f",
    "ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¯ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â": "\ufe0f",
    "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â": "•",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â³": "🆕",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â°": "⏳",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â»": "»",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â¬Ãƒâ€šÃ‚Â¢": "•",
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¿Ãƒâ€šÃ‚Â½": "",
    "Ãƒâ€šÃ‚Â ": " ",
    "Ã‚Â ": " ",
    "Æ’Ã‚Â¢": "",
    "Â¬Ã‚Â¢": "",
    "€šÃ‚Â": "",
}

def repair_mojibake_text(text: str) -> str:
    if not isinstance(text, str) or not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text

    def score(value: str) -> tuple[int, int, int]:
        suspicious = sum(value.count(marker) for marker in _MOJIBAKE_MARKERS)
        arabic = sum(1 for char in value if "\u0600" <= char <= "\u06ff")
        replacement_chars = value.count("\ufffd")
        return (suspicious + replacement_chars, -arabic, len(value))

    best = text
    for _ in range(8):
        candidates = [best]
        for source_encoding in ("latin1", "cp1252"):
            try:
                candidates.append(best.encode(source_encoding).decode("utf-8"))
            except Exception:
                continue
        next_best = min(candidates, key=score)
        if next_best == best or not any(marker in next_best for marker in _MOJIBAKE_MARKERS):
            best = next_best
            break
        best = next_best
    return best

def normalize_telegram_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text)
    
    # 1. Handle long divider-like garbage sequences
    text = re.sub(r"(?:Ãƒ[^\s\n]{1,24}){6,}", "──────────────────", text)
    # Catch interleaved garbage in dividers and bullets
    text = re.sub(r"([─•])(?:[\u0080-\u00ff]{2,}|[Æ’Â¬€šÃ¢â€šÂ¬Ãƒâ€šÃ‚Â]+)+", r"\1", text)
    
    # 2. Heuristic multi-pass repair
    text = repair_mojibake_text(text)
    
    # 3. Targeted dictionary replacements
    for bad, good in _MOJIBAKE_REPLACEMENTS.items():
        if bad:
            text = text.replace(bad, good)
        
    # 4. Final cleanup of any remaining Mojibake artifacts
    text = re.sub(r"[\u00c0-\u00ff]{2,}", "", text)
    
    return text

test_strings = [
    "──────────────────Æ’Ã‚Â¢──────────────────Â¬Ã‚Â¢──────────────────€šÃ‚Â──────────────────Æ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â",
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â الدور: قنص"
]

with open("scratch/output.txt", "w", encoding="utf-8") as f:
    for s in test_strings:
        f.write(f"Original: {s}\n")
        f.write(f"Fixed:    {normalize_telegram_text(s)}\n")
        f.write("-" * 20 + "\n")
print("Done")

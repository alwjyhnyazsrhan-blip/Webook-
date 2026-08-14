import re
import html
import time
from datetime import datetime, timezone

_MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ï", "", "Æ", "€", "†", "™")

_MOJIBAKE_REPLACEMENTS = {
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â": "️",
    "ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¯ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â": "️",
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
    "ÃƒÂ¢Ã¢â‚¬Â Ã¢â€šÂ¬": "─",
    "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢": "•",
    "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â": "—",
    "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â¹Ãƒâ€šÃ‚Â": "", # Zero width space
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸": "", # Variation selector corrupted
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â": "", # Variation selector corrupted
    "ÃƒÆ’Ã‚Â¯Ãƒâ¸": "", # User reported marker
}

def repair_mojibake(text: str) -> str:
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

def clean_mojibake(text: str) -> str:
    if text is None:
        return ""
    text = str(text)
    
    # 1. Targeted replacements
    for bad, good in _MOJIBAKE_REPLACEMENTS.items():
        if bad:
            text = text.replace(bad, good)
            
    # 2. Sequential multi-pass repair
    text = repair_mojibake(text)
    
    # 3. Handle divider patterns
    text = text.replace("──────────────────Æ’Ã‚Â¢──────────────────Â¬Ã‚Â¢──────────────────€šÃ‚Â──────────────────Æ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â", "──────────────────")
    text = re.sub(r"(?:Ãƒ[^\s\n]{1,24}){6,}", "──────────────────", text)
    
    # 4. Final cleanup of aggressive Latin1 patterns that survived
    text = re.sub(r"[\u00c0-\u00ff]{2,}", "", text)
    
    return text

def markdownish_to_html(text: str) -> str:
    if not isinstance(text, str):
        return text

    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda match: f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>',
        text,
    )
    text = re.sub(r"`([^`]+)`", lambda match: f"<code>{html.escape(match.group(1))}</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda match: f"<b>{match.group(1)}</b>", text)
    text = re.sub(r"_([^_]+)_", lambda match: f"<i>{match.group(1)}</i>", text)
    return text

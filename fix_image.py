import sys

with open("apps/bot/handlers.py", "r", encoding="utf-8") as f:
    content = f.read()

old_code = """        nested_value(data, "image31", "url"),
        nested_value(data, "imageBg", "url"),
        nested_value(data, "logo", "url"),
    )"""

new_code = """        nested_value(data, "image31", "url"),
        nested_value(data, "imageBg", "url"),
        nested_value(data, "logo", "url"),
        data.get("logo") if isinstance(data.get("logo"), str) else None,
        nested_value(data, "organization", "logo"),
        nested_value(data, "home_team", "logo"),
    )"""

content = content.replace(old_code, new_code)

with open("apps/bot/handlers.py", "w", encoding="utf-8") as f:
    f.write(content)

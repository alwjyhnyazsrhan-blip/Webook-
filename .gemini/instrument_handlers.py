import re
import os

def instrument_file(filepath):
    print(f"Instrumenting {filepath}...")
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add Tracing Imports
    if "core.tracing" not in content:
        import_marker = "import time"
        if import_marker in content:
            print("Adding imports...")
            tracing_imports = (
                "\n# --- Observability Imports ---\n"
                "from core.tracing.middleware import traced_handler\n"
                "from core.tracing.telegram_instruments import traced_send_message, traced_edit_text\n"
                "from core.tracing.keyboard_forensics import validate_keyboard\n"
            )
            content = content.replace(import_marker, import_marker + tracing_imports)

    # 2. Instrument safe_send_media definition
    if "async def safe_send_media" in content:
        print("Instrumenting safe_send_media definition...")
        content = re.sub(
            r'async def safe_send_media\(callback: types\.CallbackQuery, text: str, reply_markup=None, image_url: str = None\):',
            r'async def safe_send_media(callback: types.CallbackQuery, text: str, reply_markup=None, image_url: str = None, trace_ctx=None):',
            content
        )

        # Update edit_text call inside safe_send_media
        old_edit = r'await callback\.message\.edit_text\(\s+text=text,\s+parse_mode="HTML",\s+reply_markup=reply_markup\s+\)'
        new_edit = (
            'if trace_ctx: validate_keyboard(reply_markup, "safe_send_media", trace_ctx)\n'
            '            await traced_edit_text(bot=callback.bot, chat_id=callback.message.chat.id, '
            'message_id=callback.message.message_id, text=text, parse_mode="HTML", reply_markup=reply_markup, trace_ctx=trace_ctx)'
        )
        content = re.sub(old_edit, new_edit, content)

        # Update answer call inside safe_send_media
        old_answer = r'await callback\.message\.answer\(text, parse_mode="HTML", reply_markup=reply_markup\)'
        new_answer = (
            'await traced_send_message(bot=callback.bot, chat_id=callback.message.chat.id, '
            'text=text, parse_mode="HTML", reply_markup=reply_markup, trace_ctx=trace_ctx)'
        )
        content = re.sub(old_answer, new_answer, content)

    # 3. Decorate handlers (handle_*)
    print("Decorating handlers...")
    def decorate_match(m):
        func_name = m.group(1)
        args = m.group(2)
        if "trace_ctx" in args:
            return m.group(0)
        return f"@traced_handler\nasync def {func_name}({args}, trace_ctx=None):"

    content = re.sub(r'async def (handle_[a-zA-Z0-9_]+)\(([^)]*)\):', decorate_match, content)

    # 4. Pass trace_ctx to safe_send_media calls
    print("Updating safe_send_media calls...")
    
    def inject_trace_ctx(content):
        pos = 0
        while True:
            match = re.search(r'safe_send_media\(', content[pos:])
            if not match:
                break
            
            start_idx = pos + match.start()
            # Find the closing parenthesis of this call
            paren_count = 1
            i = start_idx + len('safe_send_media(')
            while paren_count > 0 and i < len(content):
                if content[i] == '(':
                    paren_count += 1
                elif content[i] == ')':
                    paren_count -= 1
                i += 1
            
            call_end = i
            full_call = content[start_idx:call_end]
            
            # Skip the definition itself
            if 'async def ' in content[start_idx-10:start_idx]:
                pos = call_end
                continue
            
            if 'trace_ctx=' not in full_call:
                # Remove trailing comma if present
                inner = full_call[len('safe_send_media('):-1].strip()
                if inner.endswith(','):
                    inner = inner[:-1].strip()
                new_call = f"safe_send_media({inner}, trace_ctx=trace_ctx)"
                content = content[:start_idx] + new_call + content[call_end:]
                pos = start_idx + len(new_call)
            else:
                pos = call_end
        return content

    content = inject_trace_ctx(content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done.")

if __name__ == "__main__":
    instrument_file(r"apps\bot\handlers.py")

import re
import os

def instrument_main(filepath):
    print(f"Instrumenting {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add Tracing Imports
    if "core.tracing" not in content:
        import_marker = "from core.logging.logger import logger"
        tracing_imports = (
            "\nfrom core.tracing.middleware import TracingMiddleware\n"
            "from core.tracing.buffer import trace_buffer\n"
        )
        content = content.replace(import_marker, import_marker + tracing_imports)

    # 2. Register Middleware
    if "dp.update.outer_middleware" not in content:
        middleware_reg = "\ndp.update.outer_middleware(TracingMiddleware())\n"
        content = content.replace("dp = Dispatcher(storage=storage)", "dp = Dispatcher(storage=storage)" + middleware_reg)

    # 3. Add /debug_last_trace command
    if "debug_last_trace" not in content:
        debug_command = (
            "\n# â•â•â• OBSERVABILITY â•â•â•\n"
            "@dp.message(Command(\"debug_last_trace\"))\n"
            "async def handle_debug_last_trace(message: types.Message):\n"
            "    # Simple diagnostic export\n"
            "    recent = trace_buffer.last(5)\n"
            "    if not recent:\n"
            "        await message.answer(\"No traces in buffer.\")\n"
            "        return\n"
            "    \n"
            "    report = \"ðŸ” **Recent Traces:**\\n\"\n"
            "    for t in recent:\n"
            "        status = \"âŒ\" if t.stages and \"failed\" in t.stages[-1].name.lower() else \"âœ…\"\n"
            "        report += f\"{status} `{t.trace_id[:8]}` | {t.callback_data or 'start'}\\n\"\n"
            "    \n"
            "    await message.answer(report, parse_mode=\"Markdown\")\n"
        )
        # Find where to insert - after dp.message.register(handle_start, Command("start"))
        insertion_point = 'dp.message.register(handle_start, Command("start"))'
        content = content.replace(insertion_point, insertion_point + debug_command)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done.")

if __name__ == "__main__":
    instrument_main(r"apps\bot\main.py")

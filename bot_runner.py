import subprocess
import os
import sys
import time

env = os.environ.copy()
env["PYTHONUTF8"] = "1"
env["PYTHONUNBUFFERED"] = "1"
env["PYTHONPATH"] = os.getcwd()

cmd = [sys.executable, "apps/bot/main.py"]

with open("bot.log", "a", encoding="utf-8") as out, open("bot_err.log", "a", encoding="utf-8") as err:
    p = subprocess.Popen(cmd, env=env, stdout=out, stderr=err, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    with open("bot.pid", "w") as f:
        f.write(str(p.pid))
    print(f"Bot started with PID {p.pid}")

time.sleep(2)
if p.poll() is None:
    print("Bot is running.")
else:
    print(f"Bot failed to start. Exit code: {p.returncode}")

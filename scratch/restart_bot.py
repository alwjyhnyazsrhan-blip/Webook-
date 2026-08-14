import subprocess
import os

def kill_process_by_cmdline(pattern):
    try:
        cmd = f'wmic process where "commandline like \'%{pattern}%\'" get processid'
        output = subprocess.check_output(cmd, shell=True).decode()
        pids = [line.strip() for line in output.split('\n') if line.strip().isdigit()]
        for pid in pids:
            print(f"Killing process {pid} ({pattern})")
            subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
    except Exception as e:
        print(f"Error killing {pattern}: {e}")

# Restart Bot
print("Restarting Bot...")
kill_process_by_cmdline("apps/bot/main.py")
# Redirect stdout to bot.log and stderr to bot_err.log
ps_cmd_bot = '$env:PYTHONPATH="."; $env:PYTHONIOENCODING="utf-8"; Start-Process py -ArgumentList "apps/bot/main.py" -NoNewWindow -RedirectStandardOutput "bot.log" -RedirectStandardError "bot_err.log"'
subprocess.run(['powershell', '-Command', ps_cmd_bot])

# Restart Worker
print("Restarting Worker...")
kill_process_by_cmdline("services/reservation/worker.py")
ps_cmd_worker = '$env:PYTHONPATH="."; $env:PYTHONIOENCODING="utf-8"; Start-Process py -ArgumentList "services/reservation/worker.py" -NoNewWindow -RedirectStandardOutput "worker.log" -RedirectStandardError "worker_err.log"'
subprocess.run(['powershell', '-Command', ps_cmd_worker])

print("Restart complete.")

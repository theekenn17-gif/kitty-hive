import os
import sys
import psutil
import json

# Ensure absolute project paths match system boundaries layout parameters
PROJECT_ROOT = "/root/KITTY_HIVE"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.radiograph_link import get_windows_hardware_status

def get_hive_status():
    status = {}
    status["queen"] = "online"
    status["worker"] = "online"
    status["scout"] = "online"
    status["analyst"] = "online"
    status["soldier"] = "online"

    status["memory"] = (
        "online"
        if os.path.exists("memory/database")
        else "offline"
    )

    status["ollama"] = "offline"
    try:
        for process in os.popen("ps aux").read().splitlines():
            if "ollama serve" in process:
                status["ollama"] = "online"
                break
    except Exception:
        status["ollama"] = "unknown"

    # Capture direct Linux WSL hardware footprints
    status["linux_wsl_cpu"] = f"{psutil.cpu_percent()}%"
    status["linux_wsl_ram"] = f"{psutil.virtual_memory().percent}%"

    # 🔌 LIVE INTERCEPT HOCK: Reach out of WSL and capture raw Windows host telemetry
    print("🔌 Sensors: Fetching cross-platform Windows metrics from Radiograph Host...")
    windows_hardware = get_windows_hardware_status()
    status["windows_host_state"] = windows_hardware["status"]
    status["windows_host_metrics"] = windows_hardware["data"]

    return status

if __name__ == "__main__":
    print(json.dumps(get_hive_status(), indent=2))

import json
import os
import subprocess
import chromadb

PROJECT_ROOT = "/root/KITTY_HIVE"

STATE_FILE = "console/hive_state.json"

print("\n══════════════════════════════════════════════")
print("🐝 KITTY HIVE HEALTH REPORT")
print("══════════════════════════════════════════════")

# ----------------------------------
# Hive State
# ----------------------------------

try:
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
except Exception:
    state = {}

# ----------------------------------
# Helper
# ----------------------------------

def check(flag):
    return "✅ ONLINE" if flag else "❌ OFFLINE"

# ----------------------------------
# Core
# ----------------------------------

print("\nCORE SYSTEMS")
print("--------------------------------------")
print(f"Queen.............. {check(state.get('queen'))}")
print(f"Worker............. {check(state.get('worker'))}")
print(f"Scout.............. {check(state.get('scout'))}")
print(f"Analyst............ {check(state.get('analyst'))}")
print(f"Soldier............ {check(state.get('soldier'))}")

# ----------------------------------
# AI
# ----------------------------------

print("\nAI SYSTEMS")
print("--------------------------------------")

try:
    subprocess.run(
        ["ollama", "list"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )
    print("Ollama............. ✅ RUNNING")
except:
    print("Ollama............. ❌ OFFLINE")

try:
    chromadb.PersistentClient(path="memory/database")
    print("ChromaDB........... ✅ CONNECTED")
except:
    print("ChromaDB........... ❌ FAILED")

print(f"Memory............. {check(state.get('memory'))}")

# ----------------------------------
# Infrastructure
# ----------------------------------

print("\nINFRASTRUCTURE")
print("--------------------------------------")

print(f"Telemetry.......... {check(state.get('telemetry'))}")
print(f"MCP................ {check(state.get('mcp'))}")

# ----------------------------------
# Runtime
# ----------------------------------

print("\nRUNTIME")
print("--------------------------------------")

cloud = state.get("cloud", False)
local = state.get("local", True)

print(f"Cloud Mode......... {'ON' if cloud else 'OFF'}")
print(f"Local Mode......... {'ON' if local else 'OFF'}")

if cloud:
    print("Queen Brain........ ChatGPT/Claude/Gemini")
else:
    print("Queen Brain........ Qwen 2.5")

print(f"Background Learn... {'ON' if state.get('background_learning') else 'OFF'}")

# ----------------------------------
# Hive
# ----------------------------------

print("\nHIVE")
print("--------------------------------------")

print(f"Hive Health........ {state.get('hive_health',100)} %")
print(f"Response Priority.. {state.get('response_priority','HIGH')}")
print(f"Average Response... {state.get('average_response_time',0.0)} sec")

print("\n══════════════════════════════════════════════")
print("Hive Diagnostics Complete")
print("══════════════════════════════════════════════")

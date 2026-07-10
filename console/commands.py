import json

STATE_FILE = "console/hive_state.json"


def load():
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


def hive_dashboard(state):
    """Generates an enhanced high-utility text dashboard of the entire Kitty Hive OS runtime metrics."""
    # 👑 ENHANCED QUEEN BRAIN VISUAL LOGIC
    if state.get("cloud"):
        queen_brain = "ChatGPT + Claude + Gemini"
    else:
        queen_brain = "Qwen 2.5 Local"

    return f"""
══════════════════════════════════════
🐝 KITTY HIVE STATUS
══════════════════════════════════════

👑 Queen.............. {'🟢 ONLINE' if state.get('queen') else '🔴 OFFLINE'}
🛠 Worker............. {'🟢 ONLINE' if state.get('worker') else '🔴 OFFLINE'}
🕵 Scout.............. {'🟢 ONLINE' if state.get('scout') else '🔴 OFFLINE'}
📊 Analyst............ {'🟢 ONLINE' if state.get('analyst') else '🔴 OFFLINE'}
🛡 Soldier............ {'🟢 ONLINE' if state.get('soldier') else '🔴 OFFLINE'}

🧠 Queen Brain........ {queen_brain}
☁️ Cloud.............. {"ON" if state.get("cloud") else "OFF"}
🌐 Internet........... {"ON" if state.get("internet") else "OFF"}
⚙️ Learning........... {"BACKGROUND" if state.get("background_learning") else "OFF"}

💾 Memory............. {'🟢 ONLINE' if state.get('memory') else '🔴 OFFLINE'}
🗄 ChromaDB........... {'🟢 ONLINE' if state.get('chromadb') else '🔴 OFFLINE'}
🦙 Ollama............. {'🟢 ONLINE' if state.get('ollama') else '🔴 OFFLINE'}
📡 Telemetry.......... {'🟢 ONLINE' if state.get('telemetry') else '🔴 OFFLINE'}
🔌 MCP................ {'🟢 ONLINE' if state.get('mcp') else '🔴 OFFLINE'}

❤️ Hive Health........ {state.get('hive_health', 100)}%
⚡ Response Mode...... {state.get('response_priority', 'Balanced')}

══════════════════════════════════════
"""


def execute(command):

    state = load()

    cmd = command.lower().strip()

    if cmd == "c on":
        state["cloud"] = True
        state["local"] = False
        state["internet"] = True
        state["chatgpt"] = True
        state["claude"] = True
        state["gemini"] = True
        state["qwen"] = False
        save(state)
        return "☁️ Cloud Queen Activated."

    if cmd == "c off":
        state["cloud"] = False
        state["local"] = True
        state["internet"] = False
        state["chatgpt"] = False
        state["claude"] = False
        state["gemini"] = False
        state["qwen"] = True
        save(state)
        return "☁️ Cloud Queen Offline. 🧠 Local Queen Activated."

    if cmd == "q on":
        state["cloud"] = False
        state["local"] = True
        state["internet"] = False
        state["chatgpt"] = False
        state["claude"] = False
        state["gemini"] = False
        state["qwen"] = True
        save(state)
        return "🧠 Local Queen Activated."

    if cmd == "q off":
        return "❌ Operation denied. Queen brain cannot be completely disabled."

    if cmd == "status":
        return hive_dashboard(state)

    return None

import sys
import os

# 👑 PATH OVERRIDE: Must sit on lines 1-10 to ensure global path availability
PROJECT_ROOT = "/root/KITTY_HIVE"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Pre-inject tools directory explicitly into system search paths
tools_path = os.path.join(PROJECT_ROOT, "tools")
if tools_path not in sys.path:
    sys.path.insert(0, tools_path)

import ollama
import chromadb
from chromadb.utils import embedding_functions
import json
from hive_dispatcher import activate_agent
from monitor.hive_status import get_hive_status

print("👑 Queen Kitty Online")
print("🐝 Hive Core Connected")

def load_identity():
    with open("identity/ken_profile.json", "r") as f:
        ken = json.load(f)
    with open("identity/kitty_identity.json", "r") as f:
        kitty = json.load(f)
    return ken, kitty

ken_profile, kitty_identity = load_identity()

def load_plan():
    with open("knowledge/hive_plan.txt", "r") as f:
        return f.read()

hive_plan = load_plan()

def load_core():
    with open("knowledge/kitty_core.txt", "r") as f:
        return f.read()

kitty_core = load_core()

def load_rules():
    with open("knowledge/agent_rules.txt", "r") as f:
        return f.read()

agent_rules = load_rules()

def load_agents():
    agents = {}
    for agent in os.listdir("agents"):
        role_file = f"agents/{agent}/role.txt"
        if os.path.exists(role_file):
            with open(role_file, "r") as f:
                agents[agent] = f.read()
    return agents

agents = load_agents()

memory_client = chromadb.PersistentClient(path="memory/database")

def get_agent_memory(agent_name: str):
    return memory_client.get_or_create_collection(
        name=f"kitty_{agent_name}_memory",
        embedding_function=embedding_functions.OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name="nomic-embed-text"
        )
    )

def choose_agent(question):
    q = question.lower()
    if q.startswith("worker ") or "ask worker" in q: return "worker"
    if q.startswith("scout ") or "ask scout" in q: return "scout"
    if q.startswith("analyst ") or "ask analyst" in q: return "analyst"
    if q.startswith("soldier ") or "ask soldier" in q: return "soldier"

    if any(word in q for word in ["who are you", "what is your name", "hello", "hi", "hey", "status check"]):
        return "queen"

    if any(word in q for word in ["build", "create", "code", "script", "make", "plan", "program", "fix"]): return "worker"
    if any(word in q for word in ["research", "market", "opportunity", "find", "search", "web"]): return "scout"
    if any(word in q for word in ["analysis", "data", "trading", "prediction", "sports", "math"]): return "analyst"
    if any(word in q for word in ["security", "protect", "check", "vulnerability"]): return "soldier"
    return "queen"

def ask_kitty(question):
    print("\n👑 Queen thinking...")
    agent = choose_agent(question)
    print(f"🐝 Routing to: {agent}")
    
    hive_status = get_hive_status()
    active_memory = get_agent_memory(agent)
    memories = active_memory.query(query_texts=[question], n_results=3)

    # Secure nested list retrieval pattern layout for ChromaDB
    context = ""
    try:
        docs = memories.get("documents", [])
        if docs and isinstance(docs, list) and len(docs) > 0:
            context = "\n".join(docs[0])
    except Exception as e:
        print(f"⚠️ Memory read skipped or structure empty: {e}")
        context = ""

    if agent != "queen":
        print(f"👑 Queen: Commanding {agent.upper()} to execute...")

        task_with_sensors = (
            f"REAL HIVE STATUS:\n"
            f"{json.dumps(hive_status, indent=2)}\n\n"
            f"TASK:\n{question}"
        )

        # Execute selected Hive agent
        answer = activate_agent(agent, task_with_sensors)

        # Store execution into long-term memory
        active_memory.add(
            documents=[f"Task: {question}\nExecution:\n{answer}"],
            ids=[f"task_{os.urandom(2).hex()}"]
        )

        print("👑 Queen reviewing report...")

        summary_response = ollama.chat(
            model="qwen2.5:7b",
            messages=[
                {
                    "role": "system",
                    "content": """
You are Queen Kitty.

One of your Hive Agents has completed its assignment.

Your responsibility is to:

• Read the report.
• Summarize it in executive language.
• Mention any warnings.
• Mention telemetry concerns if present.
• Mention files changed if important.
• Recommend the next step.

Never repeat the whole report.

Maximum 10 lines.
"""
                },
                {
                    "role": "user",
                    "content": answer
                }
            ]
        )

        queen_summary = summary_response["message"]["content"]

        return f"""
{answer}

══════════════════════════════════════
👑 QUEEN EXECUTIVE SUMMARY
══════════════════════════════════════

{queen_summary}
"""

    system_prompt = f"""
You are {kitty_identity['name']} 👑🐝.
Title: {kitty_identity['title']}
You are {ken_profile['name']}'s personal AI assistant.
Creator: {kitty_identity['creator']}
Your purpose: {kitty_identity['purpose']}
Your personality: {kitty_identity['personality']}
Your mission: {kitty_identity['mission']}
Ken's projects: {ken_profile['projects']}
Ken's interests: {ken_profile['interests']}

Kitty Core:
{kitty_core}

Hive Blueprint:
{hive_plan}

Available Hive Agents:
{agents}

Hive Agent Rules:
{agent_rules}

REAL HIVE STATUS:
{json.dumps(hive_status, indent=2)}

Always answer as Kitty. Use memory when available.
"""

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Memory Context:\n{context}\n\nQuestion:\n{question}"}
        ]
    )

    answer = response["message"]["content"]
    active_memory.add(
        documents=[f"Question: {question} Answer: {answer}"],
        ids=[f"queen_{os.urandom(2).hex()}"]
    )
    return answer

while True:
    try:
        user = input("\nKen > ")
        if user.lower() == "exit": break
        if not user.strip(): continue
        print("\n🐝 Kitty:")
        print(ask_kitty(user))
    except KeyboardInterrupt:
        print("\nHive offline.")
        break

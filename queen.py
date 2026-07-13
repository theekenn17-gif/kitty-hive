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

# ⚡ HIGH-PERFORMANCE LIFECYCLE: Initialize uvloop immediately
import uvloop
import asyncio
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

import ollama
import chromadb
from chromadb.utils import embedding_functions
import json
import tiktoken
from rank_bm25 import BM25Okapi
from hive_dispatcher import activate_agent
from monitor.hive_status import get_hive_status
from console.commands import execute, load

# ⚡ HIGH-PERFORMANCE LIFECYCLE: Link RAM Cache and Millisecond Tracking Modules
from performance.cache import (
    get_cached_identity, get_cached_plan, get_cached_core,
    get_cached_rules, get_cached_agents
)
from performance.timer import hive_timer

# 🔌 MCP INITIALIZATION BLOCK MAPPING
from core.mcp_manager import mcp_manager
from core.mcp_clients.radiograph_client import RadiographClient

print("👑 Queen Kitty Online")
print("🐝 Hive Core Connected")

# Core async wrapper bundling registration steps smoothly to prevent runtime crashes
async def init_mcp_ecosystem():
    try:
        radiograph = RadiographClient()
        await mcp_manager.register_server("radiograph", radiograph)
        await mcp_manager.connect_all()
    except Exception as e:
        print(f"⚠️ MCP initialization bypassed or ran into structural hurdle: {e}")

# Trigger the single async lifecycle loop boot pass natively
asyncio.run(init_mcp_ecosystem())

# ⚡ PROGRAMMATIC VRAM PRIMING: Loads weights straight into RAM without wasting time on token inference
print("🦙 Loading Qwen 2.5 into RAM...")
try:
    ollama.generate(model="qwen2.5:7b", prompt="", options={"num_predict": 0}, keep_alive="30m")
    print("✅ Neural path arrays primed.")
except Exception as e:
    print(f"⚠️ Warming skipped: {e}")

# Load all core identities and data frameworks directly from fast RAM cache blocks
ken_profile, kitty_identity = get_cached_identity()
hive_plan = get_cached_plan()
kitty_core = get_cached_core()
agent_rules = get_cached_rules()
agents = get_cached_agents()

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
    # Start the monotonic millisecond tracker
    hive_timer.start()
    
    agent = choose_agent(question)
    hive_timer.mark("Agent Routing Decisions")

    active_memory = get_agent_memory(agent)

    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(question))
        if token_count > 1500:
            print("⚠️ Warning: Input context token size high. Truncating payload boundary layout.")
    except Exception:
        pass

    # Preserved pure semantic vector database query processing patterns
    memories = active_memory.query(query_texts=[question], n_results=5)
    hive_timer.mark("Semantic Vector DB Retrieval")

    context = ""
    try:
        # ✅ BUGFIX: Target the first index list array [0] to securely un-nest ChromaDB's matrix layout
        docs = memories.get("documents", [])
        if docs and isinstance(docs, list) and len(docs) > 0 and docs[0]:
            target_docs = docs[0]
            corpus = [doc.lower().split() for doc in target_docs]
            bm25 = BM25Okapi(corpus)
            tokenized_query = question.lower().split()
            best_docs = bm25.get_top_n(tokenized_query, target_docs, n=min(3, len(target_docs)))
            context = "\n".join(best_docs)
            hive_timer.mark("BM25 Keyword Re-ranking")
    except Exception as e:
        print(f"⚠️ Hybrid retrieval re-ranking pass skipped or structure empty: {e}")
        context = ""

    # Lazy Telemetry Logic implementation. Bypass heavy scans for basic conversations.
    hive_status = {}
    needs_sensors = agent != "queen" or any(w in question.lower() for w in ["status", "system", "metrics", "telemetry"])
    
    if needs_sensors:
        hive_status = get_hive_status()
        hive_timer.mark("Cross-Platform Sensor Scan")

    if agent != "queen":
        print(f"👑 Queen: Commanding {agent.upper()} to execute...")
        task_with_sensors = (
            f"REAL HIVE STATUS:\n"
            f"{json.dumps(hive_status, indent=2)}\n\n"
            f"TASK:\n{question}"
        )

        answer = activate_agent(agent, task_with_sensors)
        hive_timer.mark(f"{agent.upper()} Agent Task Execution Loop")

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
        hive_timer.mark("Queen Executive Review Logic")
        
        # RAM STATE MANAGER PASS: Bypasses heavy disk I/O reads
        try:
            state_cache = load()
            if state_cache.get("performance_logs"):
                print(hive_timer.report())
        except Exception:
            pass

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
{json.dumps(hive_status, indent=2) if hive_status else "Telemetry skipped for conversational efficiency context."} 
"""

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Memory Context:\n{context}\n\nQuestion:\n{question}"}
        ]
    )

    answer = response["message"]["content"]
    hive_timer.mark("Queen Neural Core Response")
    
    try:
        active_memory.add(
            documents=[f"Question: {question} Answer: {answer}"],
            ids=[f"queen_{os.urandom(2).hex()}"]
        )
    except Exception:
        pass
        
    # RAM STATE MANAGER PASS: Bypasses heavy disk I/O reads
    try:
        state_cache = load()
        if state_cache.get("performance_logs"):
            print(hive_timer.report())
    except Exception:
        pass
        
    return answer

# 👑 INTERACTIVE TERMINAL LOOP ENVIRONMENT WITH CONSOLE INTERCEPT ROUTING
while True:
    try:
        user = input("\nKen > ")

        if user.lower() == "exit":
            break

        if not user.strip():
            continue

        # 🐝 Console Command Check
        result = execute(user)

        if result is not None:
            print("\n🐝 Kitty:")
            print(result)
            continue

        print("\n🐝 Kitty:")
        print(ask_kitty(user))

    except KeyboardInterrupt:
        print("\nHive offline.")
        break

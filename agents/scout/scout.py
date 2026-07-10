import ollama
import urllib.request
import urllib.parse
import re
import os
from datetime import datetime

def load_scout_role():
    if os.path.exists("agents/scout/role.txt"):
        with open("agents/scout/role.txt", "r") as f:
            return f.read()
    return "ROLE: Master Intelligence and Web Reconnaissance Agent of Kitty Hive 🔎🐝."

def web_search(query: str) -> list:
    """Performs a programmatic lookup via DuckDuckGo HTML layout."""
    try:
        url = "https://duckduckgo.com" + urllib.parse.quote(query) + "&df=w"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        links = re.findall(r'<a class="result__url" href=".*?">(.*?)</a>', html)[:5]
        snippets = re.findall(r'<td class="result__snippet">(.*?)</td>', html)[:5]
        
        results = []
        for title, snap in zip(links, snippets):
            clean_title = re.sub(r'<[^<]+?>', '', title).strip()
            clean_snap = re.sub(r'<[^<]+?>', '', snap).strip()
            clean_snap = clean_snap.replace('&amp;', '&').replace('&quot;', '"').replace('&#x27;', "'")
            if clean_title and clean_snap:
                results.append((clean_title, clean_snap))
        return results
    except Exception:
        return []

def scout_execute(task_payload: str) -> str:
    print("\n🔎 Scout extracting operational instruction bounds...")
    
    actual_task = task_payload
    if "REAL HIVE STATUS:" in task_payload and "TASK:" in task_payload:
        try:
            actual_task = task_payload.split("\n\nTASK:\n")[1].strip()
        except Exception:
            pass

    search_query = actual_task.lower()
    for word in ["scout", "research", "the", "latest", "find", "search", "for"]:
        search_query = search_query.replace(word, "")
    search_query = " ".join(search_query.split()).strip()
    
    if not search_query:
        search_query = "ai news updates"

    print(f"🔎 Scout Attempting Web Search For: '{search_query}'")
    raw_findings = web_search(search_query)
    
    if raw_findings:
        print("✅ Scout: Live network stream captured successfully.")
        status_state = "Success (Live Data)"
        findings_blocks = []
        for title, snippet in raw_findings:
            findings_blocks.append(f"- [{title}]\n  {snippet}")
        findings_str = "\n".join(findings_blocks)
    else:
        print("⚠️ Scout: Web sensor throttled. Activating offline model fallback logic...")
        status_state = "Offline Fallback Mode"
        
        fallback_prompt = f"""
You are the Scout Agent operating in Offline Fallback Mode. The web search endpoint is throttled.
Provide a research overview of general trends relevant to: '{search_query}'.
CRITICAL: Explicitly state that this data is generated from offline knowledge and may lack real-time events.
"""
        try:
            response = ollama.chat(
                model="qwen2.5:7b",
                options={"num_predict": 2048},
                messages=[
                    {"role": "system", "content": fallback_prompt},
                    {"role": "user", "content": f"Compile a report for: {actual_task}"}
                ]
            )
            findings_str = response["message"]["content"]
        except Exception as e:
            findings_str = f"Critical Failure: Both web sensor and model fallback dropped. Error: {e}"

    scout_role = load_scout_role()
    
    # Complete Scout Report block formatting layout string
    report = f"""
==================================================
{scout_role}
==================================================
SEARCH QUERY: "{search_query}"
STATUS: {status_state}

FINDINGS:
{findings_str}
"""
    
    # 🧠 FIX 3: Dynamic long-term source cache logging mechanism
    try:
        log_dir = "research/scout_reports"
        os.makedirs(log_dir, exist_ok=True)
        safe_filename = "".join([c if c.isalnum() else "_" for c in search_query[:20]])
        timestamp = datetime.now().strftime("%Y-%m-%d")
        log_path = f"{log_dir}/{timestamp}_{safe_filename}.txt"
        
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📂 Scout: Permanent cache entry log generated at '{log_path}'.")
    except Exception as e:
        print(f"⚠️ Scout: Source memory logging skipped. {e}")

    # 🧠 FIX 1: Chain handoff to the Analyst Agent autonomously
    try:
        from hive_dispatcher import activate_agent
        print("\n⚡ Scout: Automated Handoff triggered. Forwarding report block data packet directly to ANALYST...")
        analyst_task = f"Analyze this newly extracted Scout report block data and extract operational conclusions:\n{report}"
        analyst_report = activate_agent("analyst", analyst_task)
        return f"{report}\n\n==================================================\n{analyst_report}"
    except Exception as e:
        return f"{report}\n\n❌ Scout Chain Error: Could not automatically pass data packet to Analyst. Error: {e}"

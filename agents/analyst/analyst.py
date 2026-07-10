import os
import sys
import ollama

PROJECT_ROOT = "/root/KITTY_HIVE"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def load_analyst_role():
    if os.path.exists("agents/analyst/role.txt"):
        with open("agents/analyst/role.txt", "r") as f:
            return f.read()
    return "ROLE: Master Business Intelligence and Strategy Analyst Agent of Kitty Hive 📊🐝."

analyst_role = load_analyst_role()

def analyst_execute(task_payload: str) -> str:
    print("\n📊 Analyst analyzing data arrays and preparing strategy profiles...")

    actual_task = task_payload
    if "REAL HIVE STATUS:" in task_payload and "TASK:" in task_payload:
        try:
            actual_task = task_payload.split("\n\nTASK:\n", 1)[1].strip()
        except Exception:
            pass

    try:
        response = ollama.chat(
            model="qwen2.5:7b",
            options={"num_predict": 2048},
            messages=[
                {"role": "system", "content": analyst_role},
                {"role": "user", "content": f"Extract patterns and determine business strategy requirements for this dataset: {actual_task}"}
            ]
        )
        analysis_result = response["message"]["content"]
        
        # ⚡ CHAIN STEP 2: Pass strategic requirements directly down to the Worker
        from hive_dispatcher import activate_agent
        print("\n⚡ Analyst Chain: Forwarding parsed strategy directives down to the WORKER for implementation...")
        worker_directive = f"Implement file system architecture adjustments matching this strategic breakdown:\n{analysis_result}"
        worker_report = activate_agent("worker", worker_directive)
        
        return f"ANALYST DEDUCTIONS:\n{analysis_result}\n\n================================\n{worker_report}"
    except Exception as e:
        return f"❌ Local Analyst Processing Failure: {e}"

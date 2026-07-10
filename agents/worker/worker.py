import os
import sys
import json
import ollama
from json import JSONDecoder

PROJECT_ROOT = "/root/KITTY_HIVE"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.telemetry import telemetry
from tools.file_manager import execute_file_command

def load_hive_plan():
    if os.path.exists("knowledge/hive_plan.txt"):
        with open("knowledge/hive_plan.txt", "r") as f:
            return f.read()
    return "No plan available."

def load_worker_role():
    if os.path.exists("agents/worker/role.txt"):
        with open("agents/worker/role.txt", "r") as f:
            return f.read()
    return "ROLE: Master Systems Engineer Agent of Kitty Hive 🛠️🐝."

def extract_first_json(text: str):
    """Deterministically extracts the first valid JSON block using raw_decode to prevent regex conflicts."""
    decoder = JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, end = decoder.raw_decode(text[i:])
                return obj, text[i:end+i]
            except Exception:
                pass
    return None, None

hive_plan = load_hive_plan()
worker_role = load_worker_role()

def worker_execute(task_payload: str) -> str:
    print("\n🛠️ Worker analyzing incoming data arrays and preparing actions...")

    actual_task = task_payload
    sensors_context = "No system sensor telemetry context provided."
    
    if "REAL HIVE STATUS:" in task_payload and "TASK:" in task_payload:
        try:
            parts = task_payload.split("\n\nTASK:\n", 1)
            sensors_context = parts[0].replace("REAL HIVE STATUS:\n", "").strip()
            if len(parts) > 1:
                actual_task = parts[1].strip()
        except Exception:
            pass

    tool_instruction_prompt = f"""
{worker_role}

==================================================
CRITICAL SYSTEM STATE FACTS (NO HALLUCINATIONS):
==================================================
{sensors_context}

Current Kitty Hive Blueprint:
{hive_plan}

==================================================
CRITICAL PROTOCOL RULES:
==================================================
If this task requires you to create, write, edit, or read a file, your response text MUST output a clean JSON block configuration following this exact schema:
{{
  "file_tool_trigger": true,
  "action": "write" or "append" or "read" or "list",
  "file_path": "folder/target_file.py",
  "content": "THE EXACT SCRIPT CONTENT"
}}
Any conversational summary or status report text you generate must come AFTER the JSON block structure.
"""

    try:
        response = ollama.chat(
            model="qwen2.5:7b",
            options={"num_predict": 2048},
            messages=[
                {"role": "system", "content": tool_instruction_prompt},
                {"role": "user", "content": f"Execute task assignment: {actual_task}. If checking status, read the CRITICAL SYSTEM STATE FACTS block above and list out the exact metrics explicitly inside your final text report below."}
            ]
        )
        model_output = response["message"]["content"]

        # Default fallback reporting states if no file changes trigger
        action_taken = model_output
        files_changed = "N/A"
        execution_status = "Success"
        next_step = "Await further system commands from Queen."

        # 👑 INDUSTRIAL-GRADE JSONDECODER INTERCEPT
        tool_data, raw_json_str = extract_first_json(model_output)

        if tool_data and tool_data.get("file_tool_trigger"):
            try:
                req_path = tool_data.get("file_path", "unknown")
                print(f"🛠️ Worker Intercept: Activating File System tool to execute '{tool_data['action']}' on '{req_path}'...")

                # Call file manager sandbox tool
                tool_result = execute_file_command(
                    action=tool_data["action"],
                    file_path=req_path,
                    content=tool_data.get("content", "")
                )

                target_abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, tool_result["path"]))

                # Live disk assertions layer verification mapping pass
                if tool_data["action"] in ["write", "append"]:
                    print(f"🔍 Verifying action execution: Checking if '{tool_result['path']}' exists...")
                    if os.path.exists(target_abs_path) and os.path.getsize(target_abs_path) > 0:
                        print("✅ Verification Check: Passed. File modification confirmed.")
                        execution_status = "Success (Verified)"
                    else:
                        print("❌ Verification Check: Failed! File was not written.")
                        execution_status = "Failed (Verification Rejection)"
                else:
                    execution_status = tool_result["status"]

                # Isolate conversational text remaining after the JSON block structure
                conversational_report = model_output.replace(raw_json_str, "").strip()
                action_taken = f"{tool_result['log']}\n\nNotes:\n{conversational_report}" if conversational_report else tool_result["log"]
                files_changed = tool_result["path"]
                next_step = f"Analyze file content changes or proceed with script execution updates."
            except Exception as e:
                action_taken = f"System Error: Failed to execute tool structure block. Parsing exception: {e}"
                execution_status = "Failed"

        # Construct final raw python string report format template
        report = f"""TASK:
{actual_task}

ACTION:
{action_taken}

FILES CHANGED:
{files_changed}

STATUS:
{execution_status}

NEXT STEP:
{next_step}
"""
        return report

    except Exception as e:
        return f"❌ Local Worker Processing Failure: {e}"

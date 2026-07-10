import os
import sys
import importlib.util

PROJECT_ROOT = "/root/KITTY_HIVE"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def load_direct(module_name, file_path):
    if not os.path.exists(file_path):
        return None
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Bind executable agent hooks directly via absolute physical targets
worker_mod = load_direct("worker_core_engine", "/root/KITTY_HIVE/agents/worker/worker.py")
scout_mod = load_direct("scout_core_engine", "/root/KITTY_HIVE/agents/scout/scout.py")
analyst_mod = load_direct("analyst_core_engine", "/root/KITTY_HIVE/agents/analyst/analyst.py")
soldier_mod = load_direct("soldier_core_engine", "/root/KITTY_HIVE/agents/soldier/soldier.py")

def activate_agent(agent, task):
    """Central gateway routing commands across sub-agents dynamically."""
    if agent == "worker" and worker_mod:
        return worker_mod.worker_execute(task)

    if agent == "scout" and scout_mod:
        return scout_mod.scout_execute(task)

    if agent == "analyst" and analyst_mod:
        return analyst_mod.analyst_execute(task)

    if agent == "soldier" and soldier_mod and hasattr(soldier_mod, 'soldier_execute'):
        return soldier_mod.soldier_execute(task)

    role_file = f"agents/{agent}/role.txt"
    if not os.path.exists(role_file):
        return f"❌ {agent} agent configuration details or executable script not found on disk"

    return f"❌ Agent execution file for {agent} failed to respond."

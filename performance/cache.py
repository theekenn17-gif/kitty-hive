import os
import json

PROJECT_ROOT = "/root/KITTY_HIVE"

_cache = {
    "identity": None,
    "plan": None,
    "core": None,
    "rules": None,
    "agents": None
}

def get_cached_identity():
    if _cache["identity"] is None:
        with open(os.path.join(PROJECT_ROOT, "identity/ken_profile.json"), "r") as f:
            ken = json.load(f)
        with open(os.path.join(PROJECT_ROOT, "identity/kitty_identity.json"), "r") as f:
            kitty = json.load(f)
        _cache["identity"] = (ken, kitty)
    return _cache["identity"]

def get_cached_plan():
    if _cache["plan"] is None:
        with open(os.path.join(PROJECT_ROOT, "knowledge/hive_plan.txt"), "r") as f:
            _cache["plan"] = f.read()
    return _cache["plan"]

def get_cached_core():
    if _cache["core"] is None:
        with open(os.path.join(PROJECT_ROOT, "knowledge/kitty_core.txt"), "r") as f:
            _cache["core"] = f.read()
    return _cache["core"]

def get_cached_rules():
    if _cache["rules"] is None:
        with open(os.path.join(PROJECT_ROOT, "knowledge/agent_rules.txt"), "r") as f:
            _cache["rules"] = f.read()
    return _cache["rules"]

def get_cached_agents():
    if _cache["agents"] is None:
        agents = {}
        agents_dir = os.path.join(PROJECT_ROOT, "agents")
        for agent in os.listdir(agents_dir):
            role_file = os.path.join(agents_dir, agent, "role.txt")
            if os.path.exists(role_file):
                with open(role_file, "r") as f:
                    agents[agent] = f.read()
        _cache["agents"] = agents
    return _cache["agents"]

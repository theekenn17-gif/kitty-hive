import os

def execute_file_command(action: str, file_path: str, content: str = "") -> dict:
    """
    Executes precise, sandboxed file modifications within the KITTY_HIVE workspace.
    Forces all relative and absolute paths to land inside the project root folder.
    """
    PROJECT_ROOT = "/root/KITTY_HIVE"
    
    # Extract only the base filename or sub-path if Qwen invents an external Linux route
    if os.path.isabs(file_path):
        filename = os.path.basename(file_path)
        target_path = os.path.abspath(os.path.join(PROJECT_ROOT, filename))
    else:
        target_path = os.path.abspath(os.path.join(PROJECT_ROOT, file_path))
    
    # Extra security line layer
    if not target_path.startswith(PROJECT_ROOT):
        target_path = os.path.abspath(os.path.join(PROJECT_ROOT, os.path.basename(file_path)))

    relative_display_path = os.path.relpath(target_path, PROJECT_ROOT)

    try:
        if action == "write":
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "Success", "log": f"Written cleanly to {relative_display_path}.", "path": relative_display_path}

        elif action == "append":
            if not os.path.exists(target_path):
                return {"status": "Failed", "log": f"Target file '{relative_display_path}' does not exist.", "path": relative_display_path}
            with open(target_path, "a", encoding="utf-8") as f:
                f.write("\n" + content)
            return {"status": "Success", "log": f"Appended cleanly to {relative_display_path}.", "path": relative_display_path}

        elif action == "read":
            if not os.path.exists(target_path):
                return {"status": "Failed", "log": f"File '{relative_display_path}' not found.", "path": relative_display_path}
            with open(target_path, "r", encoding="utf-8") as f:
                return {"status": "Success", "log": f.read(), "path": relative_display_path}

        elif action == "list":
            if not os.path.exists(target_path) or not os.path.isdir(target_path):
                return {"status": "Failed", "log": f"Directory '{relative_display_path}' not found.", "path": relative_display_path}
            items = os.listdir(target_path)
            return {"status": "Success", "log": ", ".join(items), "path": relative_display_path}

        return {"status": "Failed", "log": f"Unknown action: {action}", "path": relative_display_path}

    except Exception as e:
        return {"status": "Failed", "log": f"Exception: {e}", "path": relative_display_path}

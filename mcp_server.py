import sys
import os
import json
from mcp.server.fastapi import FastMcpServer
from mcp.types import Tool, TextContent

# Ensure absolute project boundaries load smoothly
PROJECT_ROOT = "/root/KITTY_HIVE"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from monitor.hive_status import get_hive_status
from tools.file_manager import execute_file_command

# Initialize FastMCP Server named KittyHive
mcp_server = FastMcpServer("KittyHive")

@mcp_server.tool()
def fetch_telemetry_metrics() -> str:
    """Retrieves real-time CPU, RAM, database, and Ollama server states from Kitty Hive sensors."""
    metrics = get_hive_status()
    return json.dumps(metrics, indent=2)

@mcp_server.tool()
def file_system_operation(action: str, file_path: str, content: str = "") -> str:
    """
    Executes sandboxed write, read, append, or list operations within the project directory.
    Paths are automatically anchored securely inside /root/KITTY_HIVE.
    """
    result = execute_file_command(action=action, file_path=file_path, content=content)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    # Start the server loop using standard Stdio communication channel mapping
    mcp_server.run_stdio()

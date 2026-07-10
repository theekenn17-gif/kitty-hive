import os
import sys

PROJECT_ROOT = "/root/KITTY_HIVE"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class MCPManager:
    """
    Sovereign Model Context Protocol Hub of Kitty Hive.
    Tracks, registers, and initiates communication pipelines with local and external MCP clients.
    """
    _initialized = False  # 👑 STATIC STATE PROTECTION LINK

    def __init__(self):
        self.servers = {}
        self.active_connections = {}

    async def register_server(self, server_name: str, client_instance) -> bool:
        """Binds an incoming MCP Client driver cleanly into the registry matrix."""
        if not MCPManager._initialized:
            print(f"🔌 MCP Manager: Registering hardware interface bridge -> {server_name}")
        self.servers[server_name] = client_instance
        return True

    async def connect_all(self) -> bool:
        """Iterates over all registered servers and safely kicks off their async loops."""
        if MCPManager._initialized:
            return True
            
        print("🔌 Initializing MCP Manager...")
        if not self.servers:
            print("🔌 MCP Manager: Operational mode stable (0 external servers registered).")
            MCPManager._initialized = True
            return True

        for name, client in self.servers.items():
            try:
                print(f"📡 MCP Hub: Attempting connection link to server workspace -> {name}")
                if hasattr(client, 'initialize'):
                    await client.initialize()
                elif hasattr(client, 'connect'):
                    await client.connect()
                
                self.active_connections[name] = True
                print(f"✅ Connected -> {name}")
            except Exception as e:
                print(f"⚠️ MCP Hub: Connection to '{name}' bypassed. Check host socket state loops: {e}")
                self.active_connections[name] = False
                
        print("✅ MCP initialization complete.")
        MCPManager._initialized = True
        return True

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict = None) -> dict:
        """Programmatic gateway for Worker or Analyst to invoke registered server tools."""
        if server_name not in self.servers or not self.active_connections.get(server_name):
            return {"status": "Failed", "error": f"Target MCP server '{server_name}' is offline or unreachable."}
        
        try:
            client = self.servers[server_name]
            if hasattr(client, 'call_tool'):
                result = await client.call_tool(tool_name, arguments or {})
                return {"status": "Success", "result": result}
            return {"status": "Failed", "error": f"Client '{server_name}' lacks a tool invocation execution loop."}
        except Exception as e:
            return {"status": "Failed", "error": f"MCP execution error: {e}"}

# Global singleton deployment hook
mcp_manager = MCPManager()

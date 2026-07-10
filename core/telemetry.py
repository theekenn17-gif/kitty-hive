import asyncio
from core.mcp_manager import mcp_manager

class Telemetry:

    async def get_radiograph_cpu(self):
        try:
            result = await mcp_manager.call_tool(
                "radiograph",
                "get_cpu_status",
                {}
            )
            return result
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    async def get_radiograph_gpu(self):
        try:
            result = await mcp_manager.call_tool(
                "radiograph",
                "get_gpu_status",
                {}
            )
            return result
        except Exception as e:
            return {"status": "offline", "error": str(e)}

telemetry = Telemetry()

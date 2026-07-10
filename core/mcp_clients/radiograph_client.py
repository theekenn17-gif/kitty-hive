import httpx


class RadiographClient:

    def __init__(self):

        self.base_url = "http://localhost:58743/mcp"

        self.session = None

        self.connected = False

    async def connect(self):

        self.session = httpx.AsyncClient(timeout=5)

        self.connected = True

        print("🖥️ Radiograph client initialized.")

    async def call_tool(self, tool_name, arguments=None):

        if arguments is None:
            arguments = {}

        if not self.connected:

            raise RuntimeError("Radiograph client not connected.")

        headers = {

            "Mcp-Session-Id": "kitty-hive"

        }

        payload = {

            "jsonrpc": "2.0",

            "id": 1,

            "method": "tools/call",

            "params": {

                "name": tool_name,

                "arguments": arguments

            }

        }

        response = await self.session.post(

            self.base_url,

            json=payload,

            headers=headers

        )

        return response.json()

from appservice.a2a import handle_a2a
from appservice.acp import handle_acp
from appservice.mcp import handle_mcp

class MessageRouter:
    def __init__(self, bridge, agent_manager):
        self.bridge = bridge
        self.agent_manager = agent_manager

    async def handle_message(self, evt):
        content = evt.content.get("body", "")
        sender = evt.sender

        if content.startswith("a2a:"):
            await handle_a2a(self.bridge, evt, self.agent_manager)
        elif content.startswith("mcp:"):
            await handle_mcp(self.bridge, evt, self.agent_manager)
        elif content.startswith("acp:"):
            await handle_acp(self.bridge, evt, self.agent_manager)
        else:
            print(f"Ignoring: {content}")

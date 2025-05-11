from mautrix.util.async_db import Database
from mautrix.bridge import BaseBridge

class AgentManager:
    def __init__(self, bridge: BaseBridge):
        self.bridge = bridge
        self.intent_cache = {}

    def get_agent_user_id(self, agent_id: str) -> str:
        return f"@agent_{agent_id}:{self.bridge.config['homeserver.domain']}"

    def get_intent(self, agent_id: str):
        mxid = self.get_agent_user_id(agent_id)
        if mxid not in self.intent_cache:
            self.intent_cache[mxid] = self.bridge.get_intent(mxid)
        return self.intent_cache[mxid]

from mautrix.appservice import AppService
from .agent_manager import AgentManager
from .router import MessageRouter

class AutonomousSphereBridge(AppService):
    async def start(self):
        self.agent_manager = AgentManager(self)
        self.router = MessageRouter(self, self.agent_manager)

        self.register_event_handler("m.room.message", self.router.handle_message)

        await super().start()

from mautrix.appservice import AppService
from appservice.base import AutonomousSphereBridge

appservice = AppService(main_class=AutonomousSphereBridge)
appservice.run()

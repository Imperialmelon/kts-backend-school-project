import typing

from app.FSM.chat.state import ChatFSM
from app.FSM.game.state import GameFSM
from app.FSM.player.state import PlayerFSM

if typing.TYPE_CHECKING:
    from app.web.app import Application


class FSMManager:
    def __init__(self, app: "Application"):
        self.chat_fsm = ChatFSM(app)
        self.game_fsm = GameFSM(app)
        self.player_fsm = PlayerFSM(app)


def setup_fsm_manager(app: "Application"):
    app.state_manager = FSMManager(app)

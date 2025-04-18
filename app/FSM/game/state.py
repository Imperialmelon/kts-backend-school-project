import typing
from enum import StrEnum

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameFSM:
    class GameStates(StrEnum):
        WaitingForConfirmation = "waiting_for_conf"
        GameGoing = "session"
        GameFinished = "finished"

    def __init__(self, app: "Application"):
        self.app = app

    async def get_state(self, app: "Application", game_id: int):
        return await self.app.store.game_accessor.get_game_state(game_id)

    async def set_state(self, game_id: int, state: GameStates):
        await self.app.store.game_accessor.set_game_state(
            game_id=game_id, state=state
        )

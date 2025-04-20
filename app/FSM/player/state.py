import typing
from enum import StrEnum

if typing.TYPE_CHECKING:
    from app.web.app import Application


class PlayerFSM:
    class PlayerStates(StrEnum):
        NOT_GAMING = "not_gaming"
        GAMING = "gaming"

    def __init__(self, app: "Application"):
        self.app = app

    async def get_state(self, player_id: int):
        pass

    async def set_state(self, player_id: int, state: PlayerStates):
        await self.app.store.game_accessor.set_player_state(player_id, state)

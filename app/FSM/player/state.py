import typing
from enum import StrEnum

if typing.TYPE_CHECKING:
    from app.web.app import Application


class PlayerProcessor:
    class PlayerStates(StrEnum):
        NotGaming = "not gaming"
        Gaming = "game"


class PlayerFSM:
    @staticmethod
    async def get_state(player_id: int):
        pass

    @staticmethod
    async def set_state(app: "Application", player_id: int, state: str):
        pass

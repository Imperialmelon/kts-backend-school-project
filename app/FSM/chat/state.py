import typing
from enum import StrEnum

if typing.TYPE_CHECKING:
    from app.web.app import Application


class ChatFSM:
    class ChatStates(StrEnum):
        WAITING_FOR_GAME = "no_game"
        GAME_IS_GOING = "game"

    def __init__(self, app: "Application"):
        self.app = app

    async def get_state_by_custom_id(
        self,
        custom_chat_id: int,
    ) -> str:
        chat = await self.app.tg_accessor.get_chat_by_custom_id(custom_chat_id)

        return chat.state

    async def get_state_by_tg_id(self, telegram_chat_id: int) -> str:
        chat = await self.app.tg_accessor.get_chat_by_telegram_id(
            telegram_chat_id
        )
        return chat.state

    async def set_state(self, chat_id: int, state: ChatStates):
        await self.app.tg_accessor.set_chat_state(chat_id=chat_id, state=state)

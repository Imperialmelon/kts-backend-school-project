import typing
from enum import StrEnum

if typing.TYPE_CHECKING:
    from app.web.app import Application


class ChatFSM:
    class ChatStates(StrEnum):
        WaitingForGame = "no_game"
        GameIsGoing = "game"

    def __init__(self, app: "Application"):
        self.app = app

    async def get_state(
        self,
        custom_chat_id: int | None = None,
        telegram_chat_id: int | None = None,
    ):
        if custom_chat_id:
            chat = await self.app.store.telegram_accessor.get_chat_by_custom_id(
                custom_chat_id
            )

        elif telegram_chat_id:
            chat = (
                await self.app.store.telegram_accessor.get_chat_by_telegram_id(
                    telegram_chat_id
                )
            )
        return chat.state

    async def set_state(self, chat_id: int, state: ChatStates):
        await self.app.store.telegram_accessor.set_chat_state(
            chat_id=chat_id, state=state
        )

import typing
from logging import Logger, getLogger

from app.store.tg_api.dataclasses import UpdateObj

if typing.TYPE_CHECKING:
    from app.web.app import Application

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.FSM.chat.state import ChatProcessor
from app.store.database.models import TgChat


class BotManager:
    def __init__(self, app: "Application"):
        self.app: "Application" = app
        self.logger: Logger = getLogger("handler")

    async def handle_updates(self, updates: list[UpdateObj]):
        for update in updates.result:
            if update.message is not None:
                await self._process_message(update)
                # await self.app.store.tg_api.tg_client.send_message(
                #     chat_id=update.message.chat.id,
                #     text=f"{update.message.text}",
                # )

            elif update.edited_message is not None:
                await self.app.store.tg_api.tg_client.send_message(
                    chat_id=update.edited_message.chat.id,
                    text=f"{update.edited_message.text}",
                )

    async def _process_message(self, update: UpdateObj):
        message = update.message
        chat_id = update.message.chat.id
        # user_id = update.message.from_.id
        # first_name = update.message.from_.first_name
        # last_name = update.message.from_.last_name
        # username = update.message.from_.username
        # text = message.text

        async with self.app.database.session() as session:
            async with session.begin():
                chat = await session.execute(
                    select(TgChat).where(TgChat.telegram_id == chat_id)
                )
                chat = chat.scalar_one_or_none()
                if not chat:
                    chat = TgChat(telegram_id=chat_id)
                    session.add(chat)
                    await session.flush()
                    await session.refresh(chat)
                chat_state = chat.state
            
            await self._state_processor(message.text, chat_state, chat_id, session)

    async def _state_processor(
        self,
        message: str,
        chat_state: str,
        chat_id: int,
        session: async_sessionmaker[AsyncSession],
    ):
        await ChatProcessor.processors[chat_state](
                message, chat_id, session, self.app
            )
 
from enum import StrEnum

from sqlalchemy import update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.store.database.models import TgChat


class ChatProcessor:
    class ChatStates(StrEnum):
        GameNotStarted = "no game"
        GameIsGoing = "game"

    @staticmethod
    async def game_is_going_processor( message: str, chat_id: int, session: async_sessionmaker[AsyncSession], app):

        if message == "/start_game":
            await app.store.tg_api.tg_client.send_message(
                chat_id=chat_id,
                text="game already started",
            )

    @staticmethod
    async def start_processor(
        message: str, chat_id: int, session: async_sessionmaker[AsyncSession], app
    ):
        
        if message == "/start_game":
            try:
                await ChatFSM.set_state(session, chat_id, "game")
                await app.store.tg_api.tg_client.send_message(
                chat_id=chat_id,
                text="game started",
            )
            except:
                await app.store.tg_api.tg_client.send_message(
                chat_id=chat_id,
                text="Error starting game",
            )
        return False

    processors = {
        ChatStates.GameNotStarted: start_processor,
        ChatStates.GameIsGoing: game_is_going_processor,
    }


class ChatFSM:
    @staticmethod
    async def get_state(chat_id: int):
        pass

    @staticmethod
    async def set_state(session: AsyncSession, chat_id: int, state: str):
        try:
            await session.execute(
                update(TgChat)
                .where(TgChat.telegram_id == chat_id)
                .values(state=state)
            )
            await session.commit()
        except Exception as e:
            return e
        


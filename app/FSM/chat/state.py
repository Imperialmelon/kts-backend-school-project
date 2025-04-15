from enum import StrEnum
import typing

from sqlalchemy import update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

from app.store.database.models import TgChat


class ChatProcessor:
    class ChatStates(StrEnum):
        GameNotStarted = "no game"
        GameIsGoing = "game"

    @staticmethod
    async def game_is_going_processor(
        message: str,
        chat_id: int,
        session: async_sessionmaker[AsyncSession],
        app : "Application",
    ):
        if message == "/start_game":
            await app.store.tg_api.tg_client.send_message(
                chat_id=chat_id,
                text="Игра уже начата",
            )

        elif message == "/stop_game":
            await ChatFSM.set_state(session, chat_id, "no game")
            await app.store.tg_api.tg_client.send_message(
                chat_id=chat_id,
                text="Игра оконончена",
            )



    @staticmethod
    async def start_processor(
        message: str,
        chat_id: int,
        session: async_sessionmaker[AsyncSession],
        app : "Application",
    ):
        if message == "/start_game":
            try:
                await ChatFSM.set_state(session, chat_id, "game")

                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat_id,
                    text="Игра началась!",
                )
                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat_id,
                    text="Для участия введите +",
                )

            except Exception:
                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat_id,
                    text="Error starting game",
                )
        elif message == "/stop_game":
            await app.store.tg_api.tg_client.send_message(
                chat_id=chat_id,
                text="game is not started",
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
        await session.execute(
            update(TgChat)
            .where(TgChat.telegram_id == chat_id)
            .values(state=state)
        )
        await session.commit()

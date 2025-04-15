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
from app.store.game.accessor import GameAccessor
from app.FSM.game.state import GameFSM, GameProcessor

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
            chat = await app.store.telegram_accessor.get_chat_by_telegram_id(chat_id=chat_id)
            custom_chat_id = chat.id
            game = await app.store.game_accessor.finish_game_in_chat(custom_chat_id)
            if game:
                
                await ChatFSM.set_state(session, chat_id, "no game")
                await GameFSM.set_state(session, game.id, GameProcessor.GameStates.GameFinished.value)
            await app.store.tg_api.tg_client.send_message(
                chat_id=chat_id,
                text="Игра оконончена",
            )
        # else:




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
                chat = await app.store.telegram_accessor.get_chat_by_telegram_id(chat_id=chat_id)
                custom_chat_id = chat.id
                await app.store.game_accessor.create_game_in_chat(custom_chat_id)
                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat_id,
                    text="Игра началась!",
                )

                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat_id,
                    text="Для участия введите +",
                )

            except Exception as e:
                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat_id,
                    text="Error starting game",
                )
                print(e)
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

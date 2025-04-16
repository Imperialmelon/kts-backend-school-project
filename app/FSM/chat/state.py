import typing
from enum import StrEnum

if typing.TYPE_CHECKING:
    from app.web.app import Application

from app.FSM.game.state import GameFSM, GameProcessor
from app.store.tg_api.dataclasses import Message


class ChatProcessor:
    class ChatStates(StrEnum):
        GameNotStarted = "no game"
        GameIsGoing = "game"

    @staticmethod
    async def game_is_going_processor(
        message: Message,
        chat_id: int,
        # session: async_sessionmaker[AsyncSession],
        app: "Application",
    ):
        if message.text == "/start_game":
            await app.store.tg_api.tg_client.send_message(
                chat_id=chat_id,
                text="Игра уже начата",
            )

        elif message.text == "/stop_game":
            chat = await app.store.telegram_accessor.get_chat_by_telegram_id(
                chat_id=chat_id
            )
            custom_chat_id = chat.id
            game = await app.store.game_accessor.finish_game_in_chat(
                custom_chat_id
            )
            if game:
                await ChatFSM.set_state(
                    app, chat_id, ChatProcessor.ChatStates.GameNotStarted.value
                )
                await GameFSM.set_state(
                    app, game.id, GameProcessor.GameStates.GameFinished.value
                )
            await app.store.tg_api.tg_client.send_message(
                chat_id=chat_id,
                text="Игра оконончена",
            )

        else:
            chat = await app.store.telegram_accessor.get_chat_by_telegram_id(
                chat_id=chat_id
            )
            custom_chat_id = chat.id
            current_game = (
                await app.store.game_accessor.get_active_game_by_chat_id(
                    custom_chat_id
                )
            )
            if current_game:
                game_state = current_game.state
                await GameProcessor.processors[game_state](
                    chat, current_game, message, app
                )
            else:
                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat_id,
                    text="Ошибка: игра не найдена",
                )

    @staticmethod
    async def start_processor(
        message: Message,
        chat_id: int,
        app: "Application",
    ):
        if message.text == "/start_game":
            try:
                await ChatFSM.set_state(app, chat_id, "game")
                chat = (
                    await app.store.telegram_accessor.get_chat_by_telegram_id(
                        chat_id=chat_id
                    )
                )
                custom_chat_id = chat.id
                await app.store.game_accessor.create_game_in_chat(
                    custom_chat_id
                )
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
        elif message.text == "/stop_game":
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
    async def set_state(app: "Application", chat_id: int, state: str):
        await app.store.telegram_accessor.set_chat_state(
            chat_id=chat_id, state=state
        )

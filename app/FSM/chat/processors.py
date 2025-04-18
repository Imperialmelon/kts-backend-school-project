import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


from app.FSM.chat.state import ChatFSM
from app.FSM.game.processors import GameProcessor
from app.FSM.game.state import GameFSM
from app.handlers.decorators import chat_message_handler
from app.store.tg_api.dataclasses import Message
from app.utils.keyboard import get_participation_keyboard


class ChatProcessor:
    current_timers = {}

    @chat_message_handler(
        text="/start_game", chat_state=ChatFSM.ChatStates.WaitingForGame
    )
    async def handle_start_game(self, message: Message, app: "Application"):
        await app.state_manager.chat_fsm.set_state(
            message.chat.id, ChatFSM.ChatStates.GameIsGoing
        )
        chat = await app.store.telegram_accessor.get_chat_by_telegram_id(
            message.chat.id
        )
        current_game = await app.store.game_accessor.create_game_in_chat(
            chat.id
        )

        await app.store.tg_api.tg_client.send_message(
            chat_id=message.chat.id,
            text="Игра началась! Подтвердите участие:",
            reply_markup=get_participation_keyboard(),
        )
        await GameProcessor.set_timer(app, chat, current_game, timeout=5)
        await app.store.tg_api.tg_client.send_message(
            chat_id=message.chat.id,
            text="Игра началась! Таймер запущен",
        )

    @chat_message_handler(
        text="/start_game", chat_state=ChatFSM.ChatStates.GameIsGoing
    )
    async def handle_start_game_when_game_is_going(
        self, message: Message, app: "Application"
    ):
        await app.store.tg_api.tg_client.send_message(
            chat_id=message.chat.id,
            text="Игра уже начата",
        )

    @chat_message_handler(
        text="/stop_game", chat_state=ChatFSM.ChatStates.GameIsGoing
    )
    async def handle_finish_game(
        self, message: Message, app: "Application"
    ) -> typing.NoReturn:
        chat = await app.telegram_accessor.get_chat_by_telegram_id(
            message.chat.id
        )
        game = await app.store.game_accessor.finish_game_in_chat(chat.id)

        if game:
            await GameProcessor().cancel_timer(game.id)
            await app.state_manager.chat_fsm.set_state(
                message.chat.id, ChatFSM.ChatStates.WaitingForGame
            )
            await app.state_manager.game_fsm.set_state(
                game.id, GameFSM.GameStates.GameFinished
            )

        await app.store.tg_api.tg_client.send_message(
            chat_id=message.chat.id,
            text="Игра окончена",
        )

    @classmethod
    async def process_message(
        cls, message: Message, app: "Application"
    ) -> typing.NoReturn:
        chat_state = await app.state_manager.chat_fsm.get_state(
            telegram_chat_id=message.chat.id
        )
        for method in cls.__dict__.values():
            if hasattr(method, "_handler_meta"):
                meta = method._handler_meta

                text_match = (
                    meta["text"] is None or message.text == meta["text"]
                )
                chat_state_match = (
                    meta["chat_state"] is None
                    or chat_state == meta["chat_state"]
                )
                if text_match and chat_state_match:
                    return await method(cls(), message, app)
        chat = await app.telegram_accessor.get_chat_by_telegram_id(
            message.chat.id
        )
        game = await app.game_accessor.get_active_game_by_chat_id(chat.id)
        if game:
            await GameProcessor.process_message(
                GameProcessor, chat, game, message, app
            )
        else:
            await app.store.tg_api.tg_client.send_message(
                chat_id=message.chat.id,
                text="Неизвестная команда",
            )
        return None

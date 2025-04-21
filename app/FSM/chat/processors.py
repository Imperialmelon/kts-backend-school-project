import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


from app.FSM.chat.state import ChatFSM
from app.FSM.game.messager import GameMessenger
from app.FSM.game.processors import GameProcessor
from app.FSM.game.state import GameFSM
from app.handlers.decorators import chat_message_handler
from app.store.tg_api.dataclasses import Message


class ChatProcessor:
    current_timers = {}

    @chat_message_handler(
        text="/start_game", chat_state=ChatFSM.ChatStates.WAITING_FOR_GAME
    )
    async def handle_start_game(self, message: Message, app: "Application"):
        await app.state_manager.chat_fsm.set_state(
            message.chat.id, ChatFSM.ChatStates.GAME_IS_GOING
        )
        chat = await app.store.telegram_accessor.get_chat_by_telegram_id(
            message.chat.id
        )
        current_game = await app.store.game_accessor.create_game_in_chat(
            chat.id
        )
        await GameMessenger.send_participation_keyboard(app, message.chat.id)

        await GameProcessor.set_timer(app, chat, current_game, timeout=5)

    @chat_message_handler(
        text="/start_game", chat_state=ChatFSM.ChatStates.GAME_IS_GOING
    )
    async def handle_start_game_when_game_is_going(
        self, message: Message, app: "Application"
    ):
        await GameMessenger.game_already_going_message(app, message.chat.id)

    @chat_message_handler(
        text="/stop_game", chat_state=ChatFSM.ChatStates.GAME_IS_GOING
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
                message.chat.id, ChatFSM.ChatStates.WAITING_FOR_GAME
            )
            await app.state_manager.game_fsm.set_state(
                game.id, GameFSM.GameStates.GAME_FINISHED
            )

        await GameMessenger.game_killed_message_(app, message.chat.id)

    @classmethod
    async def process_message(
        cls, message: Message, app: "Application"
    ) -> typing.NoReturn:
        chat_state = await app.state_manager.chat_fsm.get_state_by_tg_id(
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
            await GameProcessor.process_message(chat, game, message, app)
        else:
            await GameMessenger.unknown_command_message(app, message.chat.id)

        return None

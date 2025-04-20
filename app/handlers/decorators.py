import typing
from collections.abc import Callable
from functools import wraps

from app.FSM.chat.state import ChatFSM
from app.FSM.game.state import GameFSM
from app.FSM.player.state import PlayerFSM
from app.store.tg_api.dataclasses import Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


def chat_message_handler(
    text: str | None = None,
    chat_state: ChatFSM.ChatStates | None = None,
    game_state: GameFSM.GameStates | None = None,
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(update: Message, app: "Application", *args, **kwargs):
            return await func(update, app, *args, **kwargs)

        wrapper._handler_meta = {
            "text": text,
            "chat_state": chat_state,
            "game_state": game_state,
        }

        return wrapper

    return decorator


def game_message_handler(
    callback_data: str | None = None,
    callback_data_startswith: str | None = None,
    game_state: GameFSM.GameStates | None = None,
    player_state: PlayerFSM.PlayerStates | None = None,
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        wrapper._game_handler_meta = {
            "callback_data": callback_data,
            "callback_data_startswith": callback_data_startswith,
            "game_state": game_state,
            "player_state": player_state,
        }
        return wrapper

    return decorator

import typing
from enum import StrEnum

from app.FSM.player.state import PlayerProcessor
from app.store.database.models import Game, TgChat

if typing.TYPE_CHECKING:
    from app.web.app import Application

from app.store.tg_api.dataclasses import Message


class GameProcessor:
    class GameStates(StrEnum):
        WaitingForConfirmation = "waiting_for_conf"
        GameGoing = "session"
        GameFinished = "finished"

    @staticmethod
    async def waiting_for_confirmation_processor(
        chat: TgChat,
        current_game: Game,
        message: Message,
        app: "Application",
    ):
        if message.text == "+":
            message_author_telegram_id = message.from_.id
            user = await app.store.telegram_accessor.get_user_by_telegram_id(
                telegram_id=message_author_telegram_id
            )
            if not user:
                user = await app.store.telegram_accessor.create_user_by_tg_id(
                    telegram_id=message_author_telegram_id, from_=message.from_
                )
            await app.store.telegram_accessor.connect_user_to_chat(
                chat.telegram_id, user.telegram_id
            )
            existing_player = (
                await app.store.game_accessor.get_player_by_chat_and_user_id(
                    current_game.id, user.id
                )
            )
            if existing_player:
                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat.telegram_id,
                    text=f"{user.telegram_id}, ваше участие уже подтверждено",
                )
            else:
                _ = await app.store.game_accessor.create_player_by_chat_user_id(
                    game_id=current_game.id,
                    user_custom_id=user.id,
                    state=PlayerProcessor.PlayerStates.Gaming.value,
                    cur_balance=current_game.start_player_balance,
                )
                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat.telegram_id,
                    text=f"Пользователь {user.telegram_id} подтвердил участие",
                )

    @staticmethod
    async def game_going_processor(
        chat_id: int,
        app: "Application",
    ):
        pass

    @staticmethod
    async def game_finished_processor(
        chat_id: int,
        app: "Application",
    ):
        pass

    processors = {
        GameStates.WaitingForConfirmation: waiting_for_confirmation_processor,
        GameStates.GameGoing: game_going_processor,
        GameStates.GameFinished: game_finished_processor,
    }


class GameFSM:
    @staticmethod
    async def get_state(chat_id: int):
        pass

    @staticmethod
    async def set_state(app: "Application", game_id: int, state: str):
        await app.store.game_accessor.set_game_state(
            game_id=game_id, state=state
        )

import asyncio
import typing

from app.FSM.game.state import GameFSM
from app.FSM.player.state import PlayerFSM
from app.handlers.decorators import game_message_handler
from app.store.database.models import Game, TgChat

if typing.TYPE_CHECKING:
    from app.web.app import Application


from app.store.tg_api.dataclasses import CallbackQuery, Message
from app.utils.timer import timer


class GameProcessor:
    _timers = {}

    @staticmethod
    async def set_timer(
        app: "Application", chat: TgChat, game: Game, timeout: int = 20
    ):
        if game.id in GameProcessor._timers:
            GameProcessor._timers[game.id].cancel()

        async def _game_timer():
            try:
                await timer(timeout, app, chat)
                if game.state == GameFSM.GameStates.WaitingForConfirmation:
                    players = await app.game_accessor.get_game_players(game.id)
                    player_list = "\n".join(
                        [f"• {player.first_name}" for player in players]
                    )
                    await app.store.tg_api.tg_client.send_message(
                        chat_id=chat.telegram_id,
                        text=f"Текущие игроки:\n{player_list}",
                    )
                    if len(player_list) < 1:
                        await app.store.tg_api.tg_client.send_message(
                            chat_id=chat.telegram_id,
                            text="Недостаточно игроков для игры",
                        )

                        await app.game_accessor.finish_game_in_chat(chat.id)
                    else:
                        await app.game_accessor.set_game_state(
                            game.id, state=GameFSM.GameStates.GameGoing
                        )
                        await app.game_accessor.create_trading_session(
                            game.id, 1
                        )
                        await app.store.tg_api.tg_client.send_message(
                            chat_id=chat.telegram_id,
                            text="Сессия 1 начата!",
                        )
            except asyncio.CancelledError:
                pass
            finally:
                GameProcessor._timers.pop(game.id, None)

        task = asyncio.create_task(_game_timer())
        GameProcessor._timers[game.id] = task

    @staticmethod
    async def cancel_timer(game_id: int):
        if game_id in GameProcessor._timers:
            GameProcessor._timers[game_id].cancel()
            GameProcessor._timers.pop(game_id)

    @game_message_handler(
        callback_data="confirm",
        game_state=GameFSM.GameStates.WaitingForConfirmation,
    )
    async def handle_conifrm_participation(
        self,
        chat: TgChat,
        current_game: Game,
        callback_query: CallbackQuery,
        app: "Application",
    ):
        message_author_telegram_id = callback_query.message.from_.id
        user = await app.telegram_accessor.get_user_by_telegram_id(
            telegram_id=message_author_telegram_id
        )
        if not user:
            user = await app.telegram_accessor.create_user_by_tg_id(
                telegram_id=message_author_telegram_id,
                first_name=callback_query.from_.first_name,
                last_name=callback_query.from_.last_name,
                username=callback_query.from_.username,
            )
        await app.telegram_accessor.connect_user_to_chat(
            chat.telegram_id, user.telegram_id
        )
        existing_player = (
            await app.game_accessor.get_player_by_chat_and_user_id(
                current_game.id, user.id
            )
        )
        if existing_player:
            if existing_player.state == PlayerFSM.PlayerStates.Gaming.value:
                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat.telegram_id,
                    text=f"{user.first_name}, ваше участие уже подтверждено",
                )
            else:
                await app.state_manager.player_fsm.set_state(
                    existing_player.id,
                    state=PlayerFSM.PlayerStates.Gaming,
                )
                await app.store.tg_api.tg_client.send_message(
                    chat_id=chat.telegram_id,
                    text=f"Пользователь {user.first_name} подтвердил участие",
                )
        else:
            await app.game_accessor.create_player_by_game_user_id(
                game_id=current_game.id,
                user_custom_id=user.id,
                state=PlayerFSM.PlayerStates.Gaming.value,
                cur_balance=current_game.start_player_balance,
            )
            await app.store.tg_api.tg_client.send_message(
                chat_id=chat.telegram_id,
                text=f"Пользователь {user.first_name} подтвердил участие",
            )

    @game_message_handler(
        callback_data="cancel",
        game_state=GameFSM.GameStates.WaitingForConfirmation,
    )
    async def handle_cancel_participation(
        self,
        chat: TgChat,
        current_game: Game,
        callback_query: CallbackQuery,
        app: "Application",
    ):
        message_author_telegram_id = callback_query.message.from_.id
        user = await app.telegram_accessor.get_user_by_telegram_id(
            telegram_id=message_author_telegram_id
        )
        player = await app.game_accessor.get_active_player_by_game_and_user_id(
            current_game.id, user.id
        )

        if player:
            await app.state_manager.player_fsm.set_state(
                player.id, state=PlayerFSM.PlayerStates.NotGaming
            )
            await app.store.tg_api.tg_client.send_message(
                chat_id=chat.telegram_id,
                text=f"Пользователь {user.first_name} отменил участие",
            )

    @classmethod
    async def process_message(
        cls,
        chat: TgChat,
        current_game: Game,
        update: Message | CallbackQuery,
        app: "Application",
    ) -> typing.NoReturn:
        if hasattr(update, "data"):
            message = Message(
                message_id=update.message.message_id,
                from_=update.from_,
                chat=update.message.chat,
                text=None,
                data=update.data,
            )
        else:
            message = update

        for method in cls.__dict__.values():
            if hasattr(method, "_game_handler_meta"):
                meta = method._game_handler_meta
                callback_match = (
                    meta["callback_data"] is None
                    or getattr(message, "data", None) == meta["callback_data"]
                )
                game_state_match = (
                    meta["game_state"] is None
                    or current_game.state == meta["game_state"]
                )
                if game_state_match and callback_match:
                    return await method(cls(), chat, current_game, update, app)

        await app.store.tg_api.tg_client.send_message(
            chat_id=chat.telegram_id,
            text="Неизвестная команда",
        )
        return None

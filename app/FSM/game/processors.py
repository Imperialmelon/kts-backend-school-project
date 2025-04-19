import asyncio
import typing

from app.FSM.game.state import GameFSM
from app.FSM.player.state import PlayerFSM
from app.handlers.decorators import game_message_handler
from app.store.database.models import Game, TgChat
from app.store.tg_api.dataclasses import CallbackQuery, Message
from app.utils.timer import timer

if typing.TYPE_CHECKING:
    from app.web.app import Application
from app.FSM.game.messager import GameMessager


class GameProcessor:
    _timers = {}

    @staticmethod
    async def handle_timer_end(app: "Application", chat: TgChat, game: Game):
        if game.state == GameFSM.GameStates.WAITING_FOR_CONFIRMATION:
            players = await app.game_accessor.get_game_players(game.id)
            player_list = "\n".join(
                [f"• {player.first_name}" for player in players]
            )

            if player_list:
                await GameMessager.players_list_message(
                    app, chat.telegram_id, player_list
                )

            if len(players) < 1:
                await GameMessager.not_enough_players_message(
                    app, chat.telegram_id
                )
                await app.game_accessor.finish_game_in_chat(chat.id)
            else:
                await app.game_accessor.set_game_state(
                    game.id, state=GameFSM.GameStates.GAME_GOING
                )
                trading_session = (
                    await app.game_accessor.create_trading_session(game.id, 1)
                )
                await GameMessager.session_start_informer(
                    app, chat.telegram_id, 1
                )

                for player in players:
                    await GameMessager.send_options_keyboard(
                        app, chat.telegram_id, player.id, trading_session.id
                    )

                await app.game_accessor.connect_assets_to_session(
                    trading_session.id
                )

    @game_message_handler(
        callback_data="confirm",
        game_state=GameFSM.GameStates.WAITING_FOR_CONFIRMATION,
    )
    async def handle_confirm_participation(
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
            await app.game_accessor.get_player_by_game_and_user_id(
                current_game.id, user.id
            )
        )

        if existing_player:
            if existing_player.state == PlayerFSM.PlayerStates.Gaming.value:
                await GameMessager.player_already_participating_message(
                    app, chat.telegram_id, user.first_name
                )

                return

            await app.state_manager.player_fsm.set_state(
                existing_player.id,
                state=PlayerFSM.PlayerStates.Gaming,
            )
        else:
            await app.game_accessor.create_player_by_game_user_id(
                game_id=current_game.id,
                user_custom_id=user.id,
                state=PlayerFSM.PlayerStates.Gaming.value,
                cur_balance=current_game.start_player_balance,
            )
        await GameMessager.successfull_participation_message(
            app, chat.telegram_id, user.first_name
        )

    @game_message_handler(
        callback_data="cancel",
        game_state=GameFSM.GameStates.WAITING_FOR_CONFIRMATION,
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
                player.id, state=PlayerFSM.PlayerStates.NOT_GAMING
            )
            await GameMessager.cancel_participation_message(
                app, chat.telegram_id, user.first_name
            )

    @game_message_handler(
        callback_data_startswith="assets_available_",
        game_state=GameFSM.GameStates.GAME_GOING,
    )
    async def handle_show_available_assets(
        self,
        chat: TgChat,
        current_game: Game,
        callback_query: CallbackQuery,
        app: "Application",
    ):
        session_id = int(callback_query.data.split("_")[2])
        assets = await app.game_accessor.get_available_assets(session_id)

        if not assets:
            await GameMessager.no_available_assets_message(
                app, chat.telegram_id
            )

            return

        await GameMessager.send_available_stocks_keyboard(
            app, chat.telegram_id, session_id, assets
        )

    @game_message_handler(
        callback_data_startswith="assets_my_",
        game_state=GameFSM.GameStates.GAME_GOING,
    )
    async def handle_show_user_assets(
        self,
        chat: TgChat,
        current_game: Game,
        callback_query: CallbackQuery,
        app: "Application",
    ):
        user_id = int(callback_query.data.split("_")[2])
        user_game = await app.game_accessor.get_player_by_game_and_user_id(
            current_game.id, user_id
        )

        if not user_game:
            await GameMessager.no_player_found_message(app, chat.telegram_id)

            return

        assets = await app.game_accessor.get_user_assets(user_game.id)

        if not assets:
            await GameMessager.player_has_no_assets_message(
                app, chat.telegram_id
            )

            return
        await GameMessager.player_assets_message(app, chat.telegram_id, assets)

    @game_message_handler(
        callback_data_startswith="buy_asset_",
        game_state=GameFSM.GameStates.GAME_GOING,
    )
    async def buy_stock(
        self,
        chat: TgChat,
        current_game: Game,
        callback_query: CallbackQuery,
        app: "Application",
    ):
        asset_id = int(callback_query.data.split("_")[2])
        asset = await app.game_accessor.get_asset_by_id(asset_id)
        await GameMessager.successful_purchase_message(
            app, chat.telegram_id, asset.title, callback_query.from_.first_name
        )

    @staticmethod
    async def set_timer(
        app: "Application", chat: TgChat, game: Game, timeout: int = 20
    ):
        if game.id in GameProcessor._timers:
            GameProcessor._timers[game.id].cancel()

        async def _game_timer():
            try:
                await timer(timeout, app, chat)
                await GameProcessor.handle_timer_end(app, chat, game)
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

    @classmethod
    async def process_message(
        cls,
        chat: TgChat,
        current_game: Game,
        update: Message | CallbackQuery,
        app: "Application",
    ) -> None:
        if not isinstance(update, CallbackQuery):
            await GameMessager.unknwon_command_message(chat.telegram_id)
            return None

        message = Message(
            message_id=update.message.message_id,
            from_=update.from_,
            chat=update.message.chat,
            text=None,
            data=update.data,
        )

        for method in cls.__dict__.values():
            if hasattr(method, "_game_handler_meta"):
                meta = method._game_handler_meta

                callback_match = (
                    meta["callback_data"] is not None
                    and message.data == meta["callback_data"]
                )

                callback_start_match = meta[
                    "callback_data_startswith"
                ] is not None and message.data.startswith(
                    meta["callback_data_startswith"]
                )

                game_state_match = (
                    meta["game_state"] is None
                    or current_game.state == meta["game_state"]
                )

                if game_state_match and (
                    callback_match or callback_start_match
                ):
                    return await method(cls(), chat, current_game, update, app)

        await GameMessager.unknwon_command_message(chat.telegram_id)

        return None

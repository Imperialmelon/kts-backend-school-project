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
from app.FSM.game.messager import GameMessenger


class GameProcessor:
    _timers = {}

    @staticmethod
    async def handle_timer_end(app: "Application", chat: TgChat, game: Game):
        if game.state == GameFSM.GameStates.WAITING_FOR_CONFIRMATION:
            players = await app.game_accessor.get_game_players(game.id)

            if players:
                await GameMessenger.players_list_message(
                    app, chat.telegram_id, players
                )

            if len(players) < 1:
                await GameMessenger.not_enough_players_message(
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
                await GameMessenger.session_start_informer(
                    app, chat.telegram_id, 1, game.id
                )

                for player in players:
                    await GameMessenger.send_options_keyboard(
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
        message_author_telegram_id = callback_query.from_.id
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
            if existing_player.state == PlayerFSM.PlayerStates.GAMING.value:
                await GameMessenger.player_already_participating_message(
                    app, chat.telegram_id, user.first_name
                )

                return

            await app.state_manager.player_fsm.set_state(
                existing_player.id,
                state=PlayerFSM.PlayerStates.GAMING,
            )
        else:
            await app.game_accessor.create_player_by_game_user_id(
                game_id=current_game.id,
                user_custom_id=user.id,
                state=PlayerFSM.PlayerStates.GAMING.value,
                cur_balance=current_game.start_player_balance,
            )
        await GameMessenger.successful_participation_message(
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
        message_author_telegram_id = callback_query.from_.id
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
            await GameMessenger.cancel_participation_message(
                app, chat.telegram_id, user.first_name
            )

    @game_message_handler(
        callback_data_startswith="assets_available_",
        game_state=GameFSM.GameStates.GAME_GOING,
        player_state=PlayerFSM.PlayerStates.GAMING,
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
            await GameMessenger.no_available_assets_message(
                app, chat.telegram_id
            )

            return

        await GameMessenger.send_available_stocks_keyboard(
            app, chat.telegram_id, session_id, assets
        )

    @game_message_handler(
        callback_data_startswith="assets_my_",
        game_state=GameFSM.GameStates.GAME_GOING,
        player_state=PlayerFSM.PlayerStates.GAMING,
    )
    async def handle_show_user_assets(
        self,
        chat: TgChat,
        current_game: Game,
        callback_query: CallbackQuery,
        app: "Application",
    ):
        sender = await app.telegram_accessor.get_user_by_telegram_id(
            callback_query.from_.id
        )
        user_id = int(callback_query.data.split("_")[2])
        if sender.id != user_id:
            await GameMessenger.not_your_assets_message(app, chat.telegram_id)

            return
        user_game = await app.game_accessor.get_player_by_game_and_user_id(
            current_game.id, user_id
        )

        if not user_game:
            await GameMessenger.no_player_found_message(app, chat.telegram_id)

            return

        assets = await app.game_accessor.get_user_assets(user_game.id)
        current_session = await app.game_accessor.get_current_game_session(
            current_game.id
        )

        if not assets:
            await GameMessenger.player_has_no_assets_message(
                app, chat.telegram_id
            )

            return
        await GameMessenger.player_assets_message(
            app, chat.telegram_id, assets, current_session.id, sender.id
        )

    @game_message_handler(
        callback_data_startswith="asset_info_",
        game_state=GameFSM.GameStates.GAME_GOING,
        player_state=PlayerFSM.PlayerStates.GAMING,
    )
    async def handle_asset_info(
        self,
        chat: TgChat,
        current_game: Game,
        callback_query: CallbackQuery,
        app: "Application",
    ):
        asset_id = int(callback_query.data.split("_")[2])
        session_id = int(callback_query.data.split("_")[3])

        asset = await app.game_accessor.get_asset_by_id(asset_id)
        price = await app.game_accessor.get_asset_price(asset_id, session_id)
        user = await app.telegram_accessor.get_chat_by_telegram_id(
            callback_query.from_.id
        )

        await GameMessenger.selling_menu_message(
            app, chat.telegram_id, asset, session_id, user.id, price
        )

    @game_message_handler(
        callback_data_startswith="buy_asset_",
        game_state=GameFSM.GameStates.GAME_GOING,
        player_state=PlayerFSM.PlayerStates.GAMING,
    )
    async def buy_stock(
        self,
        chat: TgChat,
        current_game: Game,
        callback_query: CallbackQuery,
        app: "Application",
    ) -> None:
        player = (
            await app.game_accessor.get_active_player_by_game_and_user_tg_id(
                current_game.id, callback_query.from_.id
            )
        )
        

        asset_id = int(callback_query.data.split("_")[2])
        session_id = int(callback_query.data.split("_")[3])
        asset_price = await app.game_accessor.get_asset_price(
            asset_id, session_id
        )
        asset = await app.game_accessor.get_asset_by_id(asset_id)
        if player.cur_balance < asset_price:
            await GameMessenger.insufficient_funds_message(app, chat.telegram_id, player.id)
            return
        players_assets = await app.game_accessor.get_user_assets(player.id)
        asset_exists = False
        for existing_asset, _ in players_assets:
            if existing_asset.id == asset_id:
                asset_exists = True
                break

        await app.game_accessor.asset_purchase(
            player.id, asset_id, asset_price, asset_exists
        )
        await GameMessenger.successful_purchase_message(
            app, chat.telegram_id, asset.title, callback_query.from_.first_name
        )

    @game_message_handler(
        callback_data_startswith="sell_asset_",
        game_state=GameFSM.GameStates.GAME_GOING,
        player_state=PlayerFSM.PlayerStates.GAMING,
    )
    async def sell_stock(
        self,
        chat: TgChat,
        current_game: Game,
        callback_query: CallbackQuery,
        app: "Application",
    ) -> None:
        try:
            alias = app.telegram_accessor.get_user_by_telegram_id
            user = await alias(callback_query.from_.id)
            player = await app.game_accessor.get_active_player_by_game_and_user_tg_id(
                current_game.id, user.telegram_id
            )
            
            asset_id = int(callback_query.data.split("_")[2])
            session_id = int(callback_query.data.split("_")[3])
            asset_price = await app.game_accessor.get_asset_price(
                asset_id, session_id
            )
            asset = await app.game_accessor.get_asset_by_id(asset_id)
            print(player.id, asset_id, asset_price)
            await app.game_accessor.asset_sale(player.id, asset_id, asset_price)
            print(player.id, asset_id, asset_price)
            await GameMessenger.successful_sale_message(
                app,
                chat.telegram_id,
                asset.title,
                callback_query.from_.first_name,
            )
        except ValueError:
            await GameMessenger.no_active_for_sale_message(
                app, chat.telegram_id
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
            await GameMessenger.unknown_command_message(app, chat.telegram_id)
            return None

        message = Message(
            message_id=update.message.message_id,
            from_=update.from_.id,
            chat=update.message.chat,
            text=None,
            data=update.data,
        )

        sender = (
            await app.game_accessor.get_active_player_by_game_and_user_tg_id(
                current_game.id, message.from_
            )
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

                requires_player_state_check = meta["player_state"] is not None

                if requires_player_state_check and not sender:
                    continue

                player_state_match = True
                if requires_player_state_check:
                    player_state_match = (
                        meta["player_state"] is None
                        or sender.state == meta["player_state"]
                    )

                if (
                    game_state_match
                    and (not requires_player_state_check or player_state_match)
                    and (callback_match or callback_start_match)
                ):
                    return await method(cls(), chat, current_game, update, app)

        await GameMessenger.unknown_command_message(app, chat.telegram_id)
        return None

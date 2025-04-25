import asyncio
import typing

from app.consts import SESSION_TIMER
from app.FSM.game.state import GameFSM
from app.FSM.player.state import PlayerFSM
from app.handlers.decorators import chat_message_handler, game_message_handler
from app.store.database.models import Game, TgChat
from app.store.tg_api.dataclasses import CallbackQuery, Message
from app.utils.timer import timer

if typing.TYPE_CHECKING:
    from app.web.app import Application
from app.FSM.game.messager import GameMessenger


class GameProcessor:
    _timers = {}

    @staticmethod
    async def confirmation_timer_end_handler(
        app: "Application", chat: TgChat, game: Game
    ):
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
            game = await app.game_accessor.get_game_by_id(game.id)

            trading_session = await app.game_accessor.create_trading_session(
                game.id, 1
            )

            player_associations = (
                await app.game_accessor.get_game_active_players(game.id)
            )

            players_list = "\n".join(
                f"• {user.first_name}: {player.cur_balance:.0f}"
                for player, user in player_associations
            )

            await GameMessenger.session_start_informer(
                app, chat.telegram_id, players_list, player_associations, 1
            )
            await GameMessenger.session_timer_start(
                app, chat.telegram_id, SESSION_TIMER
            )

            await app.game_accessor.connect_assets_to_session(
                trading_session.id
            )

            assets = await app.game_accessor.get_available_assets(
                trading_session.id
            )

            if not assets:
                await GameMessenger.no_available_assets_message(
                    app, chat.telegram_id
                )

                return

            await GameMessenger.send_available_stocks_keyboard(
                app, chat.telegram_id, trading_session.id, assets
            )

            await GameProcessor.set_timer(
                app, chat, game, timeout=SESSION_TIMER
            )

    @staticmethod
    async def session_timer_end_handler(
        app: "Application", chat: TgChat, game: Game
    ):
        current_session = await app.game_accessor.get_current_game_session(
            game.id
        )

        if not current_session:
            return

        await app.game_accessor.finish_session(current_session.id)

        players = await app.game_accessor.get_game_active_players(game.id)
        top_players = [player[0] for player in players]
        top_players = sorted(top_players, key=lambda p: p.cur_balance)
        await GameMessenger.session_end_message(
            app, chat.telegram_id, top_players, current_session.session_num
        )

        if current_session.session_num >= game.session_limit:
            players = [player[0] for player in players]
            winner = max(players, key=lambda p: p.cur_balance)
            winner_user = await app.tg_accessor.get_user_by_custom_id(
                winner.user_id
            )
            await app.game_accessor.set_winner(winner_user.id, game.id)

            await GameMessenger.game_over_message(
                app, chat.telegram_id, winner_user.first_name
            )
            await app.game_accessor.finish_game_in_chat(chat.id)
            return

        players = [player[0] for player in players]
        if len(players) >= 2 and current_session.session_num != 1:
            min_balance_player = min(players, key=lambda p: p.cur_balance)
            loser = await app.tg_accessor.get_user_by_custom_id(
                min_balance_player.user_id
            )
            await app.state_manager.player_fsm.set_state(
                min_balance_player.id,
                state=PlayerFSM.PlayerStates.NOT_GAMING,
            )
            await GameMessenger.player_eliminated_message(
                app, chat.telegram_id, loser.first_name
            )

        active_players = await app.game_accessor.get_game_players(game.id)

        if len(active_players) < 2:
            players = await app.game_accessor.get_game_active_players(game.id)
            players = [player[0] for player in players]
            winner = max(players, key=lambda p: p.cur_balance)
            winner_user = await app.tg_accessor.get_user_by_custom_id(
                winner.user_id
            )
            await app.game_accessor.set_winner(winner_user.id, game.id)

            await GameMessenger.game_over_message(
                app, chat.telegram_id, winner_user.first_name
            )
            await app.game_accessor.finish_game_in_chat(chat.id)
            return

        new_session_num = current_session.session_num + 1
        trading_session = await app.game_accessor.create_trading_session(
            game.id, new_session_num
        )

        await app.game_accessor.connect_assets_to_session(trading_session.id)

        player_associations = await app.game_accessor.get_game_active_players(
            game.id
        )

        players_list = "\n".join(
            f"• {user.first_name}: {player.cur_balance:.0f}"
            for player, user in player_associations
        )

        await GameMessenger.session_start_informer(
            app,
            chat.telegram_id,
            players_list,
            player_associations,
            new_session_num,
        )
        await GameMessenger.session_timer_start(
            app, chat.telegram_id, SESSION_TIMER
        )
        assets = await app.game_accessor.get_available_assets(
            trading_session.id
        )
        await GameMessenger.send_available_stocks_keyboard(
            app, chat.telegram_id, trading_session.id, assets
        )

        await GameProcessor.set_timer(app, chat, game, timeout=SESSION_TIMER)

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
        user = await app.tg_accessor.get_user_by_telegram_id(
            telegram_id=message_author_telegram_id
        )

        if not user:
            user = await app.tg_accessor.create_user_by_tg_id(
                telegram_id=message_author_telegram_id,
                first_name=callback_query.from_.first_name,
                last_name=callback_query.from_.last_name,
                username=callback_query.from_.username,
            )

        await app.tg_accessor.connect_user_to_chat(
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
            app, chat.telegram_id, user.first_name, callback_query
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
        user = await app.tg_accessor.get_user_by_telegram_id(
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

    @chat_message_handler(
        text="/my_assets",
        game_state=GameFSM.GameStates.GAME_GOING,
        player_state=PlayerFSM.PlayerStates.GAMING,
    )
    async def handle_show_user_assets(
        self,
        chat: TgChat,
        current_game: Game,
        message: Message,
        app: "Application",
    ):
        sender = await app.tg_accessor.get_user_by_telegram_id(message.from_.id)
        user_game = await app.game_accessor.get_player_by_game_and_user_id(
            current_game.id, sender.id
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
            app,
            chat.telegram_id,
            assets,
            current_session.id,
            sender.id,
            user_game.cur_balance,
        )

    @game_message_handler(
        callback_data_startswith="assets_available:",
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
        session_id = int(callback_query.data.split(":")[-1])
        current_session = await app.game_accessor.get_current_game_session(
            current_game.id
        )
        if current_session.id != session_id:
            await GameMessenger.session_already_finished_message(
                app, chat.telegram_id
            )
            return
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
        callback_data_startswith="asset_info:",
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
        asset_id, session_id = map(
            int, (callback_query.data.split(":")[-1].split("-"))
        )

        current_session = await app.game_accessor.get_current_game_session(
            current_game.id
        )
        if current_session.id != session_id:
            await GameMessenger.session_already_finished_message(
                app, chat.telegram_id
            )
            return
        asset = await app.game_accessor.get_asset_by_id(asset_id)
        price = await app.game_accessor.get_asset_price(asset_id, session_id)

        await GameMessenger.selling_menu_message(
            app, chat.telegram_id, asset, session_id, price
        )

    @game_message_handler(
        callback_data_startswith="buy_asset:",
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
        if not player:
            return

        asset_id, session_id = map(
            int, (callback_query.data.split(":")[-1].split("-"))
        )
        current_session = await app.game_accessor.get_current_game_session(
            current_game.id
        )
        if current_session.id != session_id:
            await GameMessenger.session_already_finished_message(
                app, chat.telegram_id
            )
            return
        asset_price = await app.game_accessor.get_asset_price(
            asset_id, session_id
        )
        asset = await app.game_accessor.get_asset_by_id(asset_id)
        if player.cur_balance < asset_price:
            await app.tg_client.answer_callback_query(
                callback_query.id,
                text="Недостаточно средств для покупки",
                show_alert=True,
            )

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
        await app.tg_client.answer_callback_query(
            callback_query.id,
            text=f"Вы приобрели {asset.title} за {asset_price}",
            show_alert=True,
        )

    @game_message_handler(
        callback_data_startswith="sell_asset:",
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
            user = await app.tg_accessor.get_user_by_telegram_id(
                callback_query.from_.id
            )
            alias = app.game_accessor.get_active_player_by_game_and_user_tg_id
            player = await alias(current_game.id, user.telegram_id)

            asset_id, session_id = map(
                int, (callback_query.data.split(":")[-1].split("-"))
            )
            asset_price = await app.game_accessor.get_asset_price(
                asset_id, session_id
            )
            asset = await app.game_accessor.get_asset_by_id(asset_id)
            await app.game_accessor.asset_sale(player.id, asset_id, asset_price)
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
                if game.state == GameFSM.GameStates.WAITING_FOR_CONFIRMATION:
                    await GameProcessor.confirmation_timer_end_handler(
                        app, chat, game
                    )
                else:
                    await GameProcessor.session_timer_end_handler(
                        app, chat, game
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

    @classmethod
    async def process_message_non_callbackquery(
        cls,
        chat: TgChat,
        current_game: Game,
        update: Message,
        app: "Application",
    ) -> None:
        alias = app.game_accessor.get_active_player_by_game_and_user_tg_id
        sender = await alias(current_game.id, update.from_.id)
        if sender:
            for method in cls.__dict__.values():
                if hasattr(method, "_handler_meta"):
                    meta = method._handler_meta

                    text_match = (
                        meta["text"] is None or update.text == meta["text"]
                    )
                    game_state_match = (
                        meta["game_state"] is None
                        or current_game.state == meta["game_state"]
                    )

                    state_match = (
                        meta["text"] is None
                        or sender.state == meta["player_state"]
                    )

                    if text_match and state_match and game_state_match:
                        return await method(
                            cls(), chat, current_game, update, app
                        )

            await GameMessenger.unknown_command_message(app, chat.telegram_id)
        return None

    @classmethod
    async def process_message(
        cls,
        chat: TgChat,
        current_game: Game,
        update: Message | CallbackQuery,
        app: "Application",
    ) -> None:
        if not isinstance(update, CallbackQuery):
            await cls.process_message_non_callbackquery(
                chat, current_game, update, app
            )

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

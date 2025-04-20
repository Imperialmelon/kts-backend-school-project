from typing import NoReturn

from sqlalchemy import Sequence, func, select, update

from app.base.base_accessor import BaseAccessor
from app.consts import SESSION_LIMIT, START_PLAYER_BALANCE
from app.FSM.chat.state import ChatFSM
from app.FSM.game.state import GameFSM
from app.FSM.player.state import PlayerFSM
from app.store.database.models import (
    Asset,
    AssetPriceInSession,
    Game,
    TgChat,
    TgUser,
    TradingSession,
    UserInGame,
    UserInGameAsset,
)


class GameAccessor(BaseAccessor):
    async def create_game_in_chat(self, chat_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            game = Game(
                chat_id=chat_id,
                state=GameFSM.GameStates.WAITING_FOR_CONFIRMATION.value,
                session_limit=SESSION_LIMIT,
                start_player_balance=START_PLAYER_BALANCE,
            )
            session.add(game)
        return game

    async def finish_game_in_chat(self, chat_id: int) -> Game | None:
        async with self.app.database.session.begin() as session:
            game = await session.scalar(
                update(Game)
                .where(
                    (Game.chat_id == chat_id)
                    & (Game.state != GameFSM.GameStates.GAME_FINISHED.value)
                )
                .values(
                    state=GameFSM.GameStates.GAME_FINISHED.value,
                    finished_at=func.now(),
                )
                .returning(Game)
            )

            if not game:
                return None
            await session.execute(
                update(TgChat)
                .where(TgChat.id == chat_id)
                .values(state=ChatFSM.ChatStates.WAITING_FOR_GAME)
            )

            await session.execute(
                update(UserInGame)
                .where(UserInGame.game_id == game.id)
                .values(state=PlayerFSM.PlayerStates.NOT_GAMING.value)
            )

            await session.execute(
                update(TradingSession)
                .where(
                    (TradingSession.game_id == game.id)
                    & (TradingSession.finished_at.is_(None))
                )
                .values(finished_at=func.now(), is_finished=True)
            )

            return game

    async def get_active_game_by_chat_id(self, chat_id: int) -> Game | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(Game).where(
                    (Game.chat_id == chat_id)
                    & (Game.state != GameFSM.GameStates.GAME_FINISHED.value)
                )
            )

    async def create_player_by_game_user_id(
        self, game_id: int, user_custom_id: int, state: str, cur_balance: int
    ) -> UserInGame:
        async with self.app.database.session.begin() as session:
            player = UserInGame(
                user_id=user_custom_id,
                game_id=game_id,
                state=state,
                cur_balance=cur_balance,
            )
            session.add(player)
        return player

    async def get_active_player_by_game_and_user_id(
        self, game_id: int, user_custom_id: int
    ) -> UserInGame | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(UserInGame).where(
                    (UserInGame.user_id == user_custom_id)
                    & (UserInGame.game_id == game_id)
                    & (
                        UserInGame.state
                        != PlayerFSM.PlayerStates.NOT_GAMING.value
                    )
                )
            )

    async def get_active_player_by_game_and_user_tg_id(
        self, game_id: int, tg_id: int
    ) -> UserInGame | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(UserInGame)
                .join(TgUser, TgUser.id == UserInGame.user_id)
                .where(
                    (TgUser.telegram_id == tg_id)
                    & (UserInGame.game_id == game_id)
                    & (
                        UserInGame.state
                        != PlayerFSM.PlayerStates.NOT_GAMING.value
                    )
                )
            )

    async def get_player_by_game_and_user_id(
        self, game_id: int, user_custom_id: int
    ) -> UserInGame | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(UserInGame).where(
                    (UserInGame.user_id == user_custom_id)
                    & (UserInGame.game_id == game_id)
                )
            )

    async def set_game_state(
        self, game_id: int, state: GameFSM.GameStates
    ) -> NoReturn:
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(Game).where(Game.id == game_id).values(state=state)
            )

    async def get_game_state(self, game_id: int) -> str:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(Game.state)
                .where(Game.id == game_id)
                .order_by(Game.started_at.desc())
            )

    async def set_player_state(
        self, player_id: int, state: PlayerFSM.PlayerStates
    ) -> NoReturn:
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(UserInGame)
                .where(UserInGame.id == player_id)
                .values(state=state)
            )

    async def get_game_players(self, game_id: int) -> Sequence[UserInGame]:
        async with self.app.database.session() as session:
            players = await session.scalars(
                select(TgUser)
                .join(UserInGame, UserInGame.user_id == TgUser.id)
                .where(
                    (UserInGame.game_id == game_id)
                    & (UserInGame.state == PlayerFSM.PlayerStates.Gaming.value)
                )
            )
        return players.all()

    async def create_trading_session(
        self, game_id: int, session_num: int
    ) -> TradingSession:
        async with self.app.database.session.begin() as session:
            trading_session = TradingSession(
                game_id=game_id,
                session_num=session_num,
            )
            session.add(trading_session)
        return trading_session

    async def get_current_game_session(self, game_id) -> TradingSession | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(TradingSession)
                .where(
                    (TradingSession.game_id == game_id)
                    & (TradingSession.finished_at.is_(None))
                )
                .order_by(TradingSession.started_at.desc())
                .limit(1)
            )

    async def finish_session(self, session_id: int) -> NoReturn:
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(TradingSession)
                .where(TradingSession.id == session_id)
                .values(finished_at=func.now(), is_finished=True)
            )

    async def get_available_assets(self, session_id: int) -> Sequence[Asset]:
        async with self.app.database.session() as session:
            assets = await session.scalars(
                select(Asset)
                .join(
                    AssetPriceInSession,
                    AssetPriceInSession.asset_id == Asset.id,
                )
                .where(AssetPriceInSession.session_id == session_id)
            )
        return assets.all()

    async def get_user_assets(
        self, user_game_id: int
    ) -> list[tuple[Asset, int]]:
        async with self.app.database.session() as session:
            assets = await session.execute(
                select(Asset, UserInGameAsset.quantity)
                .join(UserInGameAsset, UserInGameAsset.asset_id == Asset.id)
                .where(UserInGameAsset.user_game_id == user_game_id)
            )
        return assets.all()

    async def get_asset_price(self, asset_id: int, session_id: int) -> int:
        async with self.app.database.session() as session:
            price = await session.scalar(
                select(AssetPriceInSession.price).where(
                    (AssetPriceInSession.asset_id == asset_id)
                    & (AssetPriceInSession.session_id == session_id)
                )
            )
        return price or 0

    async def set_price_for_asset_in_session(
        self, asset_id: int, session_id: int, price: int
    ) -> NoReturn:
        async with self.app.database.session.begin() as session:
            price_in_session = AssetPriceInSession(
                asset_id=asset_id,
                session_id=session_id,
                price=price,
            )
            session.add(price_in_session)

    async def connect_assets_to_session(
        self, session_id: int, price: int = 1000
    ) -> NoReturn:
        async with self.app.database.session.begin() as session:
            assets = await session.scalars(select(Asset))
            assets = assets.all()
            for asset in assets:
                price_in_session = AssetPriceInSession(
                    asset_id=asset.id,
                    session_id=session_id,
                    price=price,
                )
                session.add(price_in_session)

    async def get_asset_by_id(self, asset_id: int) -> Asset | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(Asset).where(Asset.id == asset_id)
            )

    async def get_game_active_players(
        self, game_id: int
    ) -> Sequence[tuple[UserInGame, TgUser]]:
        async with self.app.database.session.begin() as session:
            result = await session.execute(
                select(UserInGame, TgUser)
                .join(TgUser, UserInGame.user_id == TgUser.id)
                .where(
                    (UserInGame.game_id == game_id)
                    & (UserInGame.state == PlayerFSM.PlayerStates.Gaming.value)
                )
            )
        return result.all()

    async def asset_purchase(
        self,
        player_id: int,
        asset_id: int,
        asset_price: int,
        asset_exists: bool,
    ) -> NoReturn:
        async with self.app.database.session.begin() as session:
            if asset_exists:
                await session.execute(
                    update(UserInGameAsset)
                    .where(
                        (UserInGameAsset.user_game_id == player_id)
                        & (UserInGameAsset.asset_id == asset_id)
                    )
                    .values(quantity=UserInGameAsset.quantity + 1)
                )
            else:
                new_asset = UserInGameAsset(
                    user_game_id=player_id, asset_id=asset_id, quantity=1
                )
                session.add(new_asset)

        await session.execute(
            update(UserInGame)
            .where(UserInGame.id == player_id)
            .values(cur_balance=UserInGame.cur_balance - asset_price)
        )

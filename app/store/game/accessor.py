from typing import NoReturn

from sqlalchemy import Sequence, func, select, update

from app.base.base_accessor import BaseAccessor
from app.consts import SESSION_LIMIT, START_PLAYER_BALANCE
from app.FSM.chat.state import ChatFSM
from app.FSM.game.state import GameFSM
from app.FSM.player.state import PlayerFSM
from app.store.database.models import (
    Game,
    TgChat,
    TgUser,
    TradingSession,
    UserInGame,
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
            game = await session.execute(
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
            game = game.scalar_one_or_none()

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

    async def get_active_game_by_chat_id(self, chat_id: int) -> Game:
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
            game = await session.execute(
                select(Game)
                .where(Game.id == game_id)
                .order_by(Game.started_at.desc())
            )
        return game.scalar_one().state

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
            result = await session.execute(
                select(TgUser)
                .join(UserInGame, UserInGame.user_id == TgUser.id)
                .where(
                    (UserInGame.game_id == game_id)
                    & (UserInGame.state == PlayerFSM.PlayerStates.Gaming.value)
                )
            )
        return result.scalars().all()

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

    async def get_current_game_session(self, game_id) -> TradingSession:
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

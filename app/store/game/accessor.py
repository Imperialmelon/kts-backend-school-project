from typing import NoReturn

from sqlalchemy import func, select, update

from app.base.base_accessor import BaseAccessor
from app.FSM.chat.state import ChatFSM
from app.FSM.game.state import GameFSM
from app.FSM.player.state import PlayerFSM
from app.store.database.models import Game, TgChat, TgUser, UserInGame


class GameAccessor(BaseAccessor):
    async def create_game_in_chat(self, chat_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            game = Game(
                chat_id=chat_id,
                state=GameFSM.GameStates.WaitingForConfirmation.value,
                session_limit=3,
                start_player_balance=10000,
            )
            session.add(game)
        return game

    async def finish_game_in_chat(self, chat_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(Game)
                .where(
                    (Game.chat_id == chat_id)
                    & (Game.state != GameFSM.GameStates.GameFinished.value)
                )
                .values(
                    state=GameFSM.GameStates.GameFinished.value,
                    finished_at=func.now(),
                )
            )

            game = await session.execute(
                select(Game)
                .where(
                    (Game.chat_id == chat_id)
                    & (Game.state == GameFSM.GameStates.GameFinished.value)
                )
                .order_by(Game.started_at.desc())
                .limit(1)
            )
            await session.execute(
                update(TgChat)
                .where(TgChat.id == chat_id)
                .values(state=ChatFSM.ChatStates.WaitingForGame)
            )
        game = game.scalar_one_or_none()
        if game:
            await session.execute(
                update(UserInGame)
                .where(UserInGame.game_id == game.id)
                .values(state=PlayerFSM.PlayerStates.NotGaming.value)
            )

        return game

    async def get_active_game_by_chat_id(self, chat_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            game = await session.execute(
                select(Game).where(
                    (Game.chat_id == chat_id)
                    & (Game.state != GameFSM.GameStates.GameFinished.value)
                )
            )
        return game.scalar_one_or_none()

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
    ) -> UserInGame:
        async with self.app.database.session.begin() as session:
            existing_player = await session.execute(
                select(UserInGame).where(
                    (UserInGame.user_id == user_custom_id)
                    & (UserInGame.game_id == game_id)
                    & (
                        UserInGame.state
                        != PlayerFSM.PlayerStates.NotGaming.value
                    )
                )
            )
        return existing_player.scalar_one_or_none()

    async def get_player_by_chat_and_user_id(
        self, game_id: int, user_custom_id: int
    ) -> UserInGame:
        async with self.app.database.session.begin() as session:
            existing_player = await session.execute(
                select(UserInGame).where(
                    (UserInGame.user_id == user_custom_id)
                    & (UserInGame.game_id == game_id)
                )
            )
        return existing_player.scalar_one_or_none()

    async def set_game_state(
        self, game_id: int, state: GameFSM.GameStates
    ) -> NoReturn:
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(Game).where(Game.id == game_id).values(state=state)
            )

    async def get_game_state(self, game_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            game = await session.execute(
                select(Game)
                .where(Game.id == game_id)
                .order_by(Game.started_at.desc())
            )
        return game.scalar_one_or_none().state

    async def set_player_state(
        self, player_id: int, state: PlayerFSM.PlayerStates
    ) -> NoReturn:
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(UserInGame)
                .where(UserInGame.id == player_id)
                .values(state=state)
            )

    async def get_game_players(self, game_id: int) -> list[UserInGame]:
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

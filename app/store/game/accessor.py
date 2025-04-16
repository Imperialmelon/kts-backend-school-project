from sqlalchemy import func, select, update

from app.base.base_accessor import BaseAccessor
from app.FSM.game.state import GameProcessor
from app.FSM.player.state import PlayerProcessor
from app.store.database.models import Game, UserInGame


class GameAccessor(BaseAccessor):
    async def create_game_in_chat(self, chat_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            game = Game(
                chat_id=chat_id,
                state=GameProcessor.GameStates.WaitingForConfirmation.value,
                session_limit=3,
                start_player_balance=10000,
            )
            session.add(game)
        return game

    async def finish_game_in_chat(self, chat_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            game = await self.get_active_game_by_chat_id(chat_id)

            if game:
                game.state = GameProcessor.GameStates.GameFinished.value
                game.finished_at = func.now()
                session.add(game)
                players = await session.execute(
                    select(UserInGame).where(UserInGame.game_id == game.id)
                )
                players = players.scalars().all()
                for player in players:
                    player.state = PlayerProcessor.PlayerStates.NotGaming.value

        return game

    async def get_active_game_by_chat_id(self, chat_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            game = await session.execute(
                select(Game)
                .where(
                    (Game.chat_id == chat_id)
                    & (
                        Game.state
                        != GameProcessor.GameStates.GameFinished.value
                    )
                    & (Game.finished_at.is_(None))
                )
                .order_by(Game.started_at.desc())
            )
        return game.scalar_one_or_none()

    async def create_player_by_chat_user_id(
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

    async def set_game_state(self, game_id: int, state: str):
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(Game).where(Game.id == game_id).values(state=state)
            )

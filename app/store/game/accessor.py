from sqlalchemy import text, select, insert

from app.store.database.models import *
from app.base.base_accessor import BaseAccessor
from app.FSM.game.state import GameProcessor

class GameAccessor(BaseAccessor):
    async def create_game_in_chat(self, chat_id: int) -> Game:
        async with self.app.database.session() as session:
            async with session.begin():
                game = Game(chat_id=chat_id, state = GameProcessor.GameStates.WaitingForConfirmation.value, session_limit = 3, start_player_balance = 10000)
                session.add(game)
                await session.flush()
                await session.refresh(game)
                print(1)
        return game
    
    async def finish_game_in_chat(self, chat_id: int) -> Game:
        async with self.app.database.session() as session:
            async with session.begin():
                game = await session.execute(
                    select(Game)
                    .where(
                        (Game.chat_id == chat_id) & 
                        (Game.state != GameProcessor.GameStates.GameFinished.value) &
                        (Game.finished_at == None)
                    )
                    .order_by(Game.started_at.desc())
                )
                game = game.scalar_one_or_none()
                
                if game:
                    game.state = GameProcessor.GameStates.GameFinished.value
                    game.finished_at = func.now()
                    await session.flush()
                
        return game
    

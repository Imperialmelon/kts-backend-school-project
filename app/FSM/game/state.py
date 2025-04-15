from enum import StrEnum
import typing

from sqlalchemy import update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)



if typing.TYPE_CHECKING:
    from app.web.app import Application

from app.store.database.models import Game

class GameProcessor:
    class GameStates(StrEnum):
        WaitingForConfirmation = "waiting_for_conf"
        GameGoing = "session"
        GameFinished = 'finished'
    
    @staticmethod
    async def waiting_for_confirmation_processor(chat_id: int,
        session: async_sessionmaker[AsyncSession],
        app : "Application",):
        pass

    @staticmethod
    async def game_going_processor(chat_id: int,
        session: async_sessionmaker[AsyncSession],
        app : "Application",):
        pass

    @staticmethod
    async def game_finished_processor(chat_id: int,
        session: async_sessionmaker[AsyncSession],
        app : "Application",):
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
    async def set_state(session: AsyncSession, game_id: int, state: str):
        await session.execute(
            update(Game)
            .where(Game.id == game_id)
            .values(state=state)
        )
        await session.commit()

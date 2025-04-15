from enum import StrEnum
import typing

from sqlalchemy import update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

from app.store.database.models import TgChat

class ChatProcessor:
    class GameStates(StrEnum):
        WaitingForConfirmation = "waiting_for_conf"
        SessionGoing = "session"
        Finished = 'finished'
    
    @staticmethod
    async def waiting_for_confirmation_procesor(chat_id: int,
        session: async_sessionmaker[AsyncSession],
        app : Application,):
        pass

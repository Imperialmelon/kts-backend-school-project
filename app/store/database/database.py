from typing import TYPE_CHECKING, Any
import os
from sqlalchemy import text

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import URL, inspect

from app.store.database.models import BaseModel

if TYPE_CHECKING:
    from app.web.app import Application



class Database:
    def __init__(self, app: "Application") -> None:
        self.app = app

        self.engine: AsyncEngine | None = None
        self._db: type[DeclarativeBase] = BaseModel
        self.session: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        self.engine = create_async_engine(
            URL.create(
            drivername="postgresql+asyncpg",
                username=self.app.config.database.user,
                password=self.app.config.database.password,
                host=self.app.config.database.host,
                port=self.app.config.database.port,
                database=self.app.config.database.database,
            ), echo=True)
        self.session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit = False)
        return

    async def disconnect(self, *args: Any, **kwargs: Any) -> None:
        await self.engine.dispose()
        return 
from typing import NoReturn

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.base.base_accessor import BaseAccessor
from app.FSM.chat.state import ChatFSM
from app.store.database.models import TgChat, TgUser, UserInChat


class TelegramAccessor(BaseAccessor):
    async def get_chat_by_telegram_id(self, chat_id: int) -> TgChat | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(TgChat).where(TgChat.telegram_id == chat_id)
            )

    async def get_chat_by_custom_id(self, chat_id: int) -> TgChat | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(TgChat).where(TgChat.id == chat_id)
            )

    async def create_chat_by_tg_id(self, chat_id: int) -> TgChat | None:
        async with self.app.database.session.begin() as session:
            chat = TgChat(telegram_id=chat_id)
            session.add(chat)
        return chat

    async def get_user_by_custom_id(self, id: int) -> TgUser | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(select(TgUser).where(TgUser.id == id))

    async def get_user_by_telegram_id(self, telegram_id: int) -> TgUser | None:
        async with self.app.database.session.begin() as session:
            return await session.scalar(
                select(TgUser).where(TgUser.telegram_id == telegram_id)
            )

    async def create_user_by_tg_id(
        self,
        telegram_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
    ) -> TgUser:
        async with self.app.database.session.begin() as session:
            user = TgUser(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            session.add(user)

        return user

    async def connect_user_to_chat(
        self, chat_telegram_id: int, user_telegram_id: int
    ) -> tuple[TgUser, TgChat]:
        async with self.app.database.session.begin() as session:
            user = await session.execute(
                select(TgUser).where(TgUser.telegram_id == user_telegram_id)
            )
            user = user.scalar_one_or_none()
            chat = await session.execute(
                select(TgChat).where(TgChat.telegram_id == chat_telegram_id)
            )
            chat = chat.scalar_one_or_none()
            stmt = (
                insert(UserInChat)
                .values(user_id=user.id, chat_id=chat.id)
                .on_conflict_do_nothing(index_elements=["user_id", "chat_id"])
            )

            await session.execute(stmt)

        return user, chat

    async def set_chat_state(
        self, chat_id: int, state: ChatFSM.ChatStates
    ) -> NoReturn:
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(TgChat)
                .where(TgChat.telegram_id == chat_id)
                .values(state=state)
            )

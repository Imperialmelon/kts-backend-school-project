from sqlalchemy import select, update

from app.base.base_accessor import BaseAccessor
from app.store.database.models import TgChat, TgUser, UserInChat
from app.store.tg_api.dataclasses import MessageFrom


class TelegramAccessor(BaseAccessor):
    async def get_chat_by_telegram_id(self, chat_id: int) -> TgChat:
        async with self.app.database.session.begin() as session:
            chat = await session.execute(
                select(TgChat).where(TgChat.telegram_id == chat_id)
            )
        return chat.scalar_one_or_none()

    async def get_chat_by_custom_id(self, chat_id: int) -> TgChat:
        async with self.app.database.session.begin() as session:
            chat = await session.execute(
                select(TgChat).where(TgChat.id == chat_id)
            )
        return chat.scalar_one_or_none()

    async def create_chat_by_tg_id(self, chat_id: int):
        async with self.app.database.session.begin() as session:
            chat = TgChat(telegram_id=chat_id)
            session.add(chat)
        return chat

    async def get_user_by_custom_id(self, id: int) -> TgUser:
        async with self.app.database.session.begin() as session:
            if id:
                user = await session.execute(
                    select(TgUser).where(TgUser.id == id)
                )
        return user.scalar_one_or_none()

    async def get_user_by_telegram_id(self, telegram_id: int) -> TgUser:
        async with self.app.database.session.begin() as session:
            user = await session.execute(
                select(TgUser).where(TgUser.telegram_id == telegram_id)
            )

        return user.scalar_one_or_none()

    async def create_user_by_tg_id(
        self, telegram_id: int, from_: MessageFrom | None = None
    ) -> TgUser:
        first_name = from_.first_name
        last_name = from_.last_name if from_.last_name else None
        username = from_.username if from_.username else None
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
    ):
        user = await self.get_user_by_telegram_id(user_telegram_id)
        chat = await self.get_chat_by_telegram_id(chat_telegram_id)

        async with self.app.database.session.begin() as session:
            existing_relation = await session.execute(
                select(UserInChat).where(
                    (UserInChat.user_id == user.id)
                    & (UserInChat.chat_id == chat.id)
                )
            )
            existing_relation = existing_relation.scalar_one_or_none()

            if not existing_relation:
                new_relation = UserInChat(
                    user_id=user.id,
                    chat_id=chat.id,
                )
                session.add(new_relation)
        return user, chat

    async def set_chat_state(self, chat_id: int, state: str):
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(TgChat)
                .where(TgChat.telegram_id == chat_id)
                .values(state=state)
            )

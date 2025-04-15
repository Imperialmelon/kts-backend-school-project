from sqlalchemy import text, select, insert

from app.store.database.models import *
from app.base.base_accessor import BaseAccessor

class TelegramAccessor(BaseAccessor):
    async def get_chat_by_telegram_id(self, chat_id : int) ->TgChat:
        async with self.app.database.session() as session:
            async with session.begin():
                chat = await session.execute(
                    select(TgChat).where(TgChat.telegram_id == chat_id)
                )
                chat = chat.scalar_one_or_none()
        return chat

        

    async def get_chat_by_custom_id(self, chat_id : int) ->TgChat:
        async with self.app.database.session() as session:
            async with session.begin():
                chat = await session.execute(
                    select(TgChat).where(TgChat.id == chat_id)
                )
                chat = chat.scalar_one_or_none()
        return chat
    async def create_chat_by_telegram_id(self, chat_id : int):
        async with self.app.database.session() as session:
            async with session.begin():
                chat = TgChat(telegram_id=chat_id)
                session.add(chat)
                await session.flush()
                await session.refresh(chat)
        return chat
    
    async def get_user_by_custom_id (self, id : int) -> TgUser:
        async with self.app.database.session() as session:
            async with session.begin():
                if id:
                    user = await session.execute(
                            select(TgUser).where(TgUser.id==id)
                        )
        user = user.scalar_one_or_none()
        return user
                

    
    async def get_user_by_telegram_id (self, telegram_id : int) -> TgUser:
        async with self.app.database.session() as session:
            async with session.begin():
                user = await session.execute(
                            select(TgUser).where(TgUser.telegram_id==telegram_id)
                        )
                        
        user = user.scalar_one_or_none()
                # if not user:
                #     user = await self.create_user_by_telegram_id(telegram_id)
        return user
    async def create_user_by_telegram_id(self, telegram_id : int) -> TgUser:
        async with self.app.database.session() as session:
            async with session.begin():
                user = TgUser(telegram_id=telegram_id)
                session.add(user)
                await session.flush()
                await session.refresh(user)
                print('created user')
        return user
    

    async def _connect_user_to_chat(self, chat_telegram_id : int, user_telegram_id : int):
        user = await self.get_user_by_telegram_id(user_telegram_id)
        chat = await self.get_chat_by_telegram_id(chat_telegram_id)

        async with self.app.database.session() as session:
            async with session.begin():
                existing_relation = await session.execute(
                select(UserInChat).where(
                    (UserInChat.user_id == user.id) and 
                    (UserInChat.chat_id == chat.id)
                )
            )
            existing_relation = existing_relation.scalar_one_or_none()

            if not existing_relation:
                new_relation = UserInChat(
                    user_id=user.id,
                    chat_id=chat.id,
                )
                session.add(new_relation)
                await session.flush()
        return user, chat
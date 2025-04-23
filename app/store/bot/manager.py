import typing
from logging import Logger, getLogger

from app.store.tg_api.dataclasses import CallbackQuery, Message, UpdateObj

if typing.TYPE_CHECKING:
    from app.web.app import Application

from app.FSM.chat.processors import ChatProcessor
from app.FSM.game.processors import GameProcessor


class BotManager:
    def __init__(self, app: "Application"):
        self.app: "Application" = app
        self.logger: Logger = getLogger("handler")

    @property
    def tg_accessor(self):
        return self.app.store.telegram_accessor

    @property
    def game_accessor(self):
        return self.app.store.game_accessor

    @property
    def tg_client(self):
        return self.app.store.tg_api.tg_client

    @property
    def admin_accessor(self):
        return self.app.store.admin_accessor

    async def handle_updates(self, updates: list[UpdateObj]):
        for update in updates.result:
            if update.message is not None:
                await self._process_message(update)
            elif update.edited_message is not None:
                await self.tg_client.send_message(
                    chat_id=update.edited_message.chat.id,
                    text=f"{update.edited_message.text}",
                )
            elif update.callback_query is not None:
                await self._process_callback(callback=update.callback_query)

    async def _process_message(self, update: UpdateObj):
        message = update.message
        chat_id = update.message.chat.id

        chat = await self.tg_accessor.get_chat_by_telegram_id(chat_id)
        if not chat:
            chat = await self.tg_accessor.create_chat_by_tg_id(chat_id)

        await self._state_processor(message=message, app=self.app)

    async def _process_callback(self, callback: CallbackQuery):
        chat = await self.tg_accessor.get_chat_by_telegram_id(
            callback.message.chat.id
        )
        current_game = await self.game_accessor.get_active_game_by_chat_id(
            chat.id
        )

        if current_game:
            await GameProcessor.process_message(
                chat, current_game, callback, self.app
            )
        else:
            await self.tg_client.answer_callback_query(
                callback.id, text="Игра не найдена"
            )

    async def _state_processor(
        self,
        message: Message,
        app: "Application",
    ):
        await ChatProcessor.process_message(message, app)

import asyncio
import typing

from app.store.database.models import TgChat

if typing.TYPE_CHECKING:
    from app.web.app import Application


async def timer(timeout: int, app: "Application", chat: TgChat):
    await asyncio.sleep(timeout)
    await app.store.tg_api.tg_client.send_message(
        chat_id=chat.telegram_id,
        text="Время вышло",
    )

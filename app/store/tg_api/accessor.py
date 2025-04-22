import typing

from app.base.base_accessor import BaseAccessor
from app.clients.tg import TgClient
from app.store.tg_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application


class TgApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", token: str, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.token = token
        self.tg_client: TgClient | None = None
        self.poller: Poller | None = None
        self.offset: int | None = None

    async def connect(self, app: "Application") -> None:
        self.tg_client = TgClient(self.token)
        await self.tg_client.connect()
        await self.setup_commands()
        self.offset = 0
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        self.poller.start()

    async def disconnect(self, app: "Application") -> None:
        if self.poller:
            await self.poller.stop()
        if self.tg_client:
            await self.tg_client.close()

    async def poll(self):
        updates = await self.tg_client.get_updates(
            offset=self.offset, timeout=25
        )
        for update in updates.result:
            self.offset = update.update_id + 1
        await self.app.store.bots_manager.handle_updates(updates)

    async def setup_commands(self):
        commands = [
            {"command": "/start_game", "description": "Начать новую игру"},
            {"command": "/stop_game", "description": "Остановить текущую игру"},
        ]

        return await self.tg_client.set_commands(commands)

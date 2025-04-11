import random
import typing
import os
from urllib.parse import urlencode, urljoin

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.tg_api.dataclasses import *
from app.clients.tg import TgClient
from app.store.tg_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application



class TgApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", token: str,  *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.tg_client = TgClient(token)
        self.poller: Poller | None = None
        self.offset: int | None = None

    async def connect(self, app: "Application") -> None:
        self.offset = 0
        self.poller = Poller(app.store)
        print('here')
        self.logger.info("start polling")
        self.poller.start()

    async def disconnect(self, app: "Application") -> None:
        if self.poller:
            await self.poller.stop()

    async def poll(self):
        updates = await self.tg_client.get_updates_in_objects(offset=self.offset, timeout=25)
        print(updates)
        for update in updates.result:
            self.offset = update.update_id + 1
        await self.app.store.bots_manager.handle_updates(updates)
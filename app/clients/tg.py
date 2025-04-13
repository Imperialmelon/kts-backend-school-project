import aiohttp

from app.clients.methods import TgMethods
from app.store.tg_api.dataclasses import (
    GetDataResponse,
    GetUpdatesResponse,
    SendMessageResponse,
)


class TgClient:
    def __init__(self, token: str):
        self.token = token
        self.session: aiohttp.ClientSession | None = None

    async def connect(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def _ensure_connection(self):
        if not self.session or self.session.closed:
            raise Exception(
                "Session is closed. Call connect() to create a new one."
            )

    def _build_query(self, method: TgMethods) -> str:
        return f"https://api.telegram.org/bot{self.token}/{method.value}"

    async def get_me(self) -> GetDataResponse:
        self._ensure_connection()
        url = self._build_query(TgMethods.GET_ME)
        async with self.session.get(url) as resp:
            jsn = await resp.json()
        return GetDataResponse.Schema().load(jsn)

    async def get_updates(
        self, offset: int | None = None, timeout: int = 0
    ) -> GetUpdatesResponse:
        self._ensure_connection()
        url = self._build_query(TgMethods.GET_UPDATES)
        params = {}
        if offset:
            params["offset"] = offset
        if timeout:
            params["timeout"] = timeout
        async with self.session.get(url, params=params) as resp:
            jsn = await resp.json()
        return GetUpdatesResponse.Schema().load(jsn)

    async def send_message(
        self, chat_id: int, text: str
    ) -> SendMessageResponse:
        self._ensure_connection()
        url = self._build_query(TgMethods.SEND_MESSAGE)
        payload = {"chat_id": chat_id, "text": text}
        async with self.session.post(url, json=payload) as resp:
            res_dict = await resp.json()
            return SendMessageResponse.Schema().load(res_dict)

from functools import wraps

from aiohttp.web import HTTPUnauthorized
from aiohttp_session import get_session


def login_required(handler):
    @wraps(handler)
    async def wrapper(self):
        session = await get_session(self.request)
        if "admin_email" not in session:
            raise HTTPUnauthorized(reason="Unauthorized")
        admin = await self.store.admin_accessor.get_by_email(
            email=session["admin_email"]
        )
        if not admin:
            raise HTTPUnauthorized(reason="Invalid credentials")
        self.request["admin"] = admin
        return await handler(self)

    return wrapper

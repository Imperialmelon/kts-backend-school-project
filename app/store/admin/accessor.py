import hashlib
import typing

from app.base.base_accessor import BaseAccessor
from app.store.admin.dataclasses import Admin

if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application") -> None:
        await self.create_admin(
            email=self.app.config.admin.email,
            password=self.app.config.admin.password,
        )

    async def get_by_email(self, email: str) -> Admin | None:
        if self.app.database.admin.email == email:
            return self.app.database.admin
        return None

    async def create_admin(self, email: str, password: str) -> Admin:
        admin = Admin(
            id=1,
            email=email,
            password=hashlib.sha256(password.encode()).hexdigest(),
        )
        self.app.database.admin = admin
        return admin

import hashlib
import typing

from aiohttp.web import json_response as aiohttp_json_response
from aiohttp.web_response import Response

if typing.TYPE_CHECKING:
    from app.store.admin.dataclasses import Admin


def json_response(data: dict | None = None, status: str = "ok") -> Response:
    return aiohttp_json_response(
        data={
            "status": status,
            "data": data or {},
        }
    )


def error_json_response(
    http_status: int,
    status: str = "error",
    message: str | None = None,
    data: dict | None = None,
):
    return aiohttp_json_response(
        status=http_status,
        data={
            "status": status,
            "message": str(message),
            "data": data or {},
        },
    )


def check_admin_credentials(admin: "Admin", password: str) -> bool:
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return admin.password == hashed_password

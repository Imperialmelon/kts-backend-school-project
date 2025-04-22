import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application
from app.admin.views import AdminLoginView


def setup_routes(app: "Application"):
    app.router.add_view("/admin.login", AdminLoginView)

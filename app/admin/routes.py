import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application
from app.admin.views import (
    AdminLoginView,
    AdminLogoutView,
    CheckGamesView,
    CreateAssetView,
    TopPlayersView,
)


def setup_routes(app: "Application"):
    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.logout", AdminLogoutView)
    app.router.add_view("/admin.chat_games", CheckGamesView)
    app.router.add_view("/admin.top_players", TopPlayersView)
    app.router.add_view("/admin.create_asset", CreateAssetView)

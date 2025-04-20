from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)

from app.FSM import FSMManager, setup_fsm_manager
from app.store import Store, setup_store
from app.store.database.database import Database
from app.web.config import Config, setup_config
from app.web.logger import setup_logging
from app.web.mw import setup_middlewares


class Application(AiohttpApplication):
    config: Config | None = None
    store: Store | None = None
    database: Database | None = None
    state_manager: FSMManager | None = None

    @property
    def game_accessor(self):
        return self.store.game_accessor

    @property
    def telegram_accessor(self):
        return self.store.telegram_accessor

    @property
    def tg_client(self):
        return self.store.tg_api.tg_client


class Request(AiohttpRequest):
    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self) -> Database:
        return self.request.app.database

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})


app = Application()


def setup_app(config_path: str) -> Application:
    setup_logging(app)
    setup_config(app, config_path)
    setup_middlewares(app)
    setup_fsm_manager(app)
    setup_store(app)
    return app

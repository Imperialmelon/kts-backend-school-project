import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class BotConfig:
    token: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5429
    user: str = "postgres"
    password: str = "postgres"
    database: str = "postgres"


@dataclass
class Config:
    admin: AdminConfig
    bot: BotConfig | None = None
    database: DatabaseConfig | None = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        bot=BotConfig(**raw_config["bot"]),
        database=DatabaseConfig(**raw_config["database"]),
        admin=AdminConfig(**raw_config["admin"]),
    )

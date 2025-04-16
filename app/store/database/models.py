from sqlalchemy import (
    BOOLEAN,
    TIMESTAMP,
    BigInteger,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseModel(DeclarativeBase):
    pass


class TgUser(BaseModel):
    __tablename__ = "telegram_user"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    chats: Mapped[list["TgChat"]] = relationship(
        "TgChat", secondary="user_chat", back_populates="users"
    )
    game_associations: Mapped[list["UserInGame"]] = relationship(
        "UserInGame", back_populates="user"
    )
    games: Mapped[list["Game"]] = relationship("Game", secondary="user_game")
    games_won: Mapped[list["Game"]] = relationship(
        "Game", back_populates="winner"
    )


class TgChat(BaseModel):
    __tablename__ = "telegram_chat"
    id: Mapped[int] = mapped_column(
        Integer, autoincrement=True, primary_key=True
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    state: Mapped[str] = mapped_column(String, default="no game")

    users: Mapped[list["TgUser"]] = relationship(
        "TgUser", secondary="user_chat", back_populates="chats"
    )
    games: Mapped[list["Game"]] = relationship("Game", back_populates="chat")


class UserInChat(BaseModel):
    __tablename__ = "user_chat"
    id: Mapped[int] = mapped_column(
        Integer, autoincrement=True, primary_key=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("telegram_user.id"))
    chat_id: Mapped[int] = mapped_column(ForeignKey("telegram_chat.id"))

    __table_args__ = (
        UniqueConstraint("user_id", "chat_id", name="user_chat_unique_id_pair"),
    )


class UserInGame(BaseModel):
    __tablename__ = "user_game"
    id: Mapped[int] = mapped_column(
        Integer, autoincrement=True, primary_key=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("telegram_user.id"))
    game_id: Mapped[int] = mapped_column(ForeignKey("game.id"))
    state: Mapped[str] = mapped_column(String, default="not gaming")
    cur_balance: Mapped[int] = mapped_column(Numeric, nullable=False)

    user: Mapped["TgUser"] = relationship(
        "TgUser", back_populates="game_associations"
    )
    game: Mapped["Game"] = relationship(
        "Game", back_populates="player_associations"
    )
    assets: Mapped[list["Asset"]] = relationship(
        "Asset", secondary="user_in_game_asset", back_populates="user_games"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="user_game_unique_id_pair"),
    )


class Game(BaseModel):
    __tablename__ = "game"
    id: Mapped[int] = mapped_column(
        Integer, autoincrement=True, primary_key=True
    )
    started_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )
    finished_at: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP, nullable=True
    )
    state: Mapped[str] = mapped_column(String, nullable=False)
    start_player_balance: Mapped[int] = mapped_column(Numeric, nullable=False)
    session_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("telegram_user.id"), nullable=True
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("telegram_chat.id"), nullable=False
    )

    player_associations: Mapped[list["UserInGame"]] = relationship(
        "UserInGame", back_populates="game", foreign_keys="[UserInGame.game_id]"
    )
    chat: Mapped["TgChat"] = relationship("TgChat", back_populates="games")
    winner: Mapped["TgUser | None"] = relationship(
        "TgUser", back_populates="games_won", foreign_keys=[winner_id]
    )
    trading_sessions: Mapped[list["TradingSession"]] = relationship(
        "TradingSession", back_populates="game"
    )


class TradingSession(BaseModel):
    __tablename__ = "trading_session"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    game_id: Mapped[int] = mapped_column(ForeignKey("game.id"))
    started_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )
    finished_at: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP, nullable=True
    )
    is_finished: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    session_num: Mapped[int] = mapped_column(Integer, nullable=False)

    game: Mapped["Game"] = relationship(
        "Game", back_populates="trading_sessions"
    )
    asset_prices: Mapped[list["AssetPriceInSession"]] = relationship(
        "AssetPriceInSession", back_populates="session"
    )


class Asset(BaseModel):
    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)

    user_games: Mapped[list["UserInGame"]] = relationship(
        "UserInGame", secondary="user_in_game_asset", back_populates="assets"
    )
    prices: Mapped[list["AssetPriceInSession"]] = relationship(
        "AssetPriceInSession", back_populates="asset"
    )


class UserInGameAsset(BaseModel):
    __tablename__ = "user_in_game_asset"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_game_id: Mapped[int] = mapped_column(ForeignKey("user_game.id"))
    asset_id: Mapped[int] = mapped_column(ForeignKey("asset.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint(
            "user_game_id", "asset_id", name="user_in_game_asset_unique_id_pair"
        ),
    )


class AssetPriceInSession(BaseModel):
    __tablename__ = "asset_price_in_session"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    asset_id: Mapped[int] = mapped_column(ForeignKey("asset.id"))
    session_id: Mapped[int] = mapped_column(ForeignKey("trading_session.id"))
    price: Mapped[int] = mapped_column(Numeric, nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="prices")
    session: Mapped["TradingSession"] = relationship(
        "TradingSession", back_populates="asset_prices"
    )

    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "session_id",
            name="asset_price_in_session_unique_id_pair",
        ),
    )

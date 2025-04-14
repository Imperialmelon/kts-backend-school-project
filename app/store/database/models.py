from sqlalchemy import (
    BOOLEAN,
    TIMESTAMP,
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class BaseModel(DeclarativeBase):
    pass


class TgUser(BaseModel):
    __tablename__ = "telegram_user"
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True)
    telegram_id = Column(BigInteger)
    chats = relationship(
        "TgChat", secondary="user_chat", back_populates="users"
    )

    game_associations = relationship("UserInGame", back_populates="user")
    games = relationship("Game", secondary="user_game", viewonly=True)
    games_won = relationship("Game", back_populates="winner")


class TgChat(BaseModel):
    __tablename__ = "telegram_chat"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    state = Column(String, nullable=False, default="no game")
    users = relationship(
        "TgUser", secondary="user_chat", back_populates="chats"
    )
    games = relationship("Game", back_populates="chat")


class UserInChat(BaseModel):
    __tablename__ = "user_chat"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("telegram_user.id"))
    chat_id = Column(ForeignKey("telegram_chat.id"))
    state = Column(String, nullable=False)
    cur_balance = Column(Numeric, nullable=False)


class UserInGame(BaseModel):
    __tablename__ = "user_game"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("telegram_user.id"))
    game_id = Column(ForeignKey("game.id"))
    state = Column(String, nullable=True)
    user = relationship("TgUser", back_populates="game_associations")
    game = relationship("Game", back_populates="player_associations")
    assets = relationship(
        "Asset", secondary="user_in_game_asset", back_populates="user_games"
    )


class Game(BaseModel):
    __tablename__ = "game"
    id = Column(Integer, primary_key=True)
    started_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    finished_at = Column(TIMESTAMP, nullable=True)
    state = Column(String, nullable=False)
    start_player_balance = Column(Numeric, nullable=False)
    session_limit = Column(Integer, nullable=False)
    winner_id = Column(ForeignKey("telegram_user.id"), nullable=True)
    chat_id = Column(ForeignKey("telegram_chat.id"), nullable=False)

    player_associations = relationship(
        "UserInGame", back_populates="game", foreign_keys="[UserInGame.game_id]"
    )
    chat = relationship("TgChat", back_populates="games")
    winner = relationship(
        "TgUser", back_populates="games_won", foreign_keys=[winner_id]
    )
    trading_sessions = relationship("TradingSession", back_populates="game")


class TradingSession(BaseModel):
    __tablename__ = "trading_session"
    id = Column(Integer, primary_key=True)
    game_id = Column(ForeignKey("game.id"))
    started_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    finished_at = Column(TIMESTAMP, nullable=True)
    is_finished = Column(BOOLEAN, default=False)
    session_num = Column(Integer, nullable=False)
    game = relationship("Game", back_populates="trading_sessions")
    asset_prices = relationship("AssetPriceInSession", back_populates="session")


class Asset(BaseModel):
    __tablename__ = "asset"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    user_games = relationship(
        "UserInGame", secondary="user_in_game_asset", back_populates="assets"
    )
    prices = relationship("AssetPriceInSession", back_populates="asset")


class UserInGameAsset(BaseModel):
    __tablename__ = "user_in_game_asset"
    id = Column(Integer, primary_key=True)
    user_game_id = Column(ForeignKey("user_game.id"))
    asset_id = Column(ForeignKey("asset.id"))
    quantity = Column(Integer, default=0)


class AssetPriceInSession(BaseModel):
    __tablename__ = "asset_price_in_session"
    id = Column(Integer, primary_key=True)
    asset_id = Column(ForeignKey("asset.id"))
    session_id = Column(ForeignKey("trading_session.id"))
    price = Column(Numeric, nullable=False)
    asset = relationship("Asset", back_populates="prices")
    session = relationship("TradingSession", back_populates="asset_prices")

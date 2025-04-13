from dataclasses import field
from typing import ClassVar

from marshmallow import EXCLUDE, Schema
from marshmallow_dataclass import dataclass


@dataclass
class Chat:
    id: int
    type: str
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    title: str | None = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class MessageFrom:
    id: int
    first_name: str
    username: str
    last_name: str | None = None
    chat: Chat | None = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class Message:
    message_id: int
    from_: MessageFrom = field(metadata={"data_key": "from"})
    chat: Chat
    text: str | None = None
    data: str | None = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class UpdateObj:
    update_id: int
    message: Message | None = None
    edited_message: Message | None = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class GetUpdatesResponse:
    ok: bool
    result: list[UpdateObj]

    Schema: ClassVar[type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class SendMessageResponse:
    ok: bool
    result: Message

    Schema: ClassVar[type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class BotDataSchema:
    id: int
    is_bot: bool
    first_name: str
    username: str
    can_join_groups: bool
    can_read_all_group_messages: bool
    supports_inline_queries: bool
    can_connect_to_business: bool
    has_main_web_app: bool


@dataclass
class GetDataResponse:
    ok: bool
    result: BotDataSchema
    Schema: ClassVar[type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE

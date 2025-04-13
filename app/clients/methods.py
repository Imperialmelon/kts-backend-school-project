from enum import Enum


class TgMethods(Enum):
    GET_ME = "getMe"
    GET_UPDATES = "getUpdates"
    SEND_MESSAGE = "sendMessage"

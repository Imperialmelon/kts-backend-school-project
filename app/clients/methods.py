from enum import StrEnum


class TgMethods(StrEnum):
    GET_ME = "getMe"
    GET_UPDATES = "getUpdates"
    SEND_MESSAGE = "sendMessage"
    ANSWER_CALLBACK_QUERY = "answerCallbackQuery"

from enum import StrEnum


class ChatProcessor:
    class ChatStates(StrEnum):
        NotGaming = "not gaming"
        GameIsGoing = "game"

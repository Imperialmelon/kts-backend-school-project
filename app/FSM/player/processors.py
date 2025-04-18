from enum import StrEnum


class PlayerProcessor:
    class PlayerStates(StrEnum):
        NotGaming = "not gaming"
        Gaming = "game"

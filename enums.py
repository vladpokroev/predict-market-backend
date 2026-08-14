from enum import IntEnum, StrEnum


class Direction(StrEnum):
    UP = "up"
    DOWN = "down"

class BetStatus(StrEnum):
    ACTIVE = "active"
    WIN = "win"
    LOSE = "lose"


class ErrorCode(IntEnum):
    COIN_NOT_FOUND = 1001
    PRICE_SERVICE_ERROR = 1002
    BET_NOT_FOUND = 1003
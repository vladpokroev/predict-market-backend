from pydantic import BaseModel, Field, field_validator

from enums import Direction


class PriceResponse(BaseModel):
    coin: str
    price: float


class ActiveBetResultResponse(BaseModel):
    status: str
    message: str

class ResolvedBetResultResponse(BaseModel):
    coin: str
    direction: Direction
    entry_price: float
    exit_price: float
    status: str

class BetRequest(BaseModel):
    coin: str = Field(min_length=1)
    amount: float = Field(gt=0)
    direction: Direction
    duration: int = Field(gt=0)

    @field_validator("coin", mode="before")
    @classmethod
    def normalize_coin(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

class BetResponse(BaseModel):
    message: str
    coin: str
    entry_price: float
    direction: Direction
    expires_at: float


class BetListResponse(BaseModel):
    coin: str
    amount: float
    direction: Direction
    entry_price: float
    status: str
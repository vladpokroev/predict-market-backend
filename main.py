import time
from enum import StrEnum

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from settings import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root() -> dict:
    return {"messageeee": "Привет, это мой API"}

def fetch_price(coin: str) -> float | None:
    url = (
        f"{settings.binance_base_url}/api/v3/ticker/price"
        f"?symbol={coin}USDT"
    )
    try:
        response = httpx.get(url)
    except httpx.RequestError:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    price = data.get("price")
    if price is None:
        return None

    return float(price)

@app.get("/price/{coin}")
def get_price(coin: str) -> dict:
    price = fetch_price(coin)
    if price is None:
        return {"error": f"Не удалось получить цену для {coin}"}
    return {"coin": coin, "price": price}

class Direction(StrEnum):
    UP = "up"
    DOWN = "down"


class Bet:
    def __init__(
        self,
        coin: str,
        amount: float,
        direction: Direction,
        entry_price: float,
        duration: int,
    ) -> None:
        self.coin = coin
        self.amount = amount
        self.direction = direction
        self.entry_price = entry_price
        self.expires_at = time.time() + duration
        self.status = "active"

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def resolve(self, exit_price: float) -> str:
        if self.direction == Direction.UP:
            won = exit_price > self.entry_price
        else:
            won = exit_price < self.entry_price

        if won:
            self.status = "win"
        else:
            self.status = "lose"

        return self.status

bets: list[Bet] = []


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


@app.post("/bet")
def create_bet(request: BetRequest) -> dict:
    entry_price = fetch_price(request.coin)
    if entry_price is None:
        return {"error": f"Не удалось получить цену для {request.coin}"}

    bet = Bet(
        coin=request.coin,
        amount=request.amount,
        direction=request.direction,
        entry_price=entry_price,
        duration=request.duration,
    )
    bets.append(bet)

    return {
        "message": "Ставка создана",
        "coin": bet.coin,
        "entry_price": bet.entry_price,
        "direction": bet.direction,
        "expires_at": bet.expires_at,
    }


@app.get("/bets")
def get_bets() -> list[dict]:
    result = []
    for bet in bets:
        result.append({
            "coin": bet.coin,
            "amount": bet.amount,
            "direction": bet.direction,
            "entry_price": bet.entry_price,
            "status": bet.status,
        })
    return result

@app.get("/bet/{bet_id}/result")
def get_result(bet_id: int) -> dict:
    if bet_id < 0 or bet_id >= len(bets):
        return {"error": "Ставка не найдена"}

    bet = bets[bet_id]

    if not bet.is_expired():
        return {"status": "active", "message": "Ставка ещё не завершена"}

    exit_price = fetch_price(bet.coin)
    if exit_price is None:
        return {"error": "Не удалось получить цену для подсчёта результата"}

    result = bet.resolve(exit_price)

    return {
        "coin": bet.coin,
        "direction": bet.direction,
        "entry_price": bet.entry_price,
        "exit_price": exit_price,
        "status": result,
    }
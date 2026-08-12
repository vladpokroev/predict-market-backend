import time
from collections.abc import Iterator
from contextlib import contextmanager

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from enums import Direction, ErrorCode
from schema import (
    ActiveBetResultResponse,
    BetListResponse,
    BetRequest,
    BetResponse,
    PriceResponse,
    ResolvedBetResultResponse,
)
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

class CoinNotFoundError(Exception):
    pass


class PriceServiceError(Exception):
    pass

@contextmanager
def handle_price_errors() -> Iterator[None]:
    try:
        yield

    except CoinNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.COIN_NOT_FOUND,
                "message": f"Coin {exc} not found",
            },
        ) from exc

    except PriceServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": ErrorCode.PRICE_SERVICE_ERROR,
                "message": str(exc),
            },
        ) from exc

def fetch_price(coin: str) -> float:
    coin = coin.strip().upper()

    url = (
        f"{settings.binance_base_url}/api/v3/ticker/price"
        f"?symbol={coin}USDT"
    )

    try:
        response = httpx.get(url)
    except httpx.RequestError as exc:
        raise PriceServiceError("Failed to connect to Binance") from exc

    if response.status_code == 400:
        raise CoinNotFoundError(coin)

    if response.status_code != 200:
        raise PriceServiceError(
            f"Binance returned status {response.status_code}"
        )

    data = response.json()
    price = data.get("price")

    if price is None:
        raise PriceServiceError("Binance did not return a price")

    return float(price)




@app.get("/price/{coin}", response_model=PriceResponse)
def get_price(coin: str) -> dict:
    coin = coin.strip().upper()

    with handle_price_errors():
        price = fetch_price(coin)

    return {"coin": coin, "price": price}


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



@app.post(
    "/bet",
    response_model=BetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bet(request: BetRequest) -> dict:
    with handle_price_errors():
        entry_price = fetch_price(request.coin)

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

@app.get("/bets", response_model=list[BetListResponse])
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

@app.get(
    "/bet/{bet_id}/result",
    response_model=ActiveBetResultResponse | ResolvedBetResultResponse,
)
def get_result(bet_id: int) -> dict:
    if bet_id < 0 or bet_id >= len(bets):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.BET_NOT_FOUND,
                "message": "Bet not found",
            },
        )

    bet = bets[bet_id]

    if not bet.is_expired():
        return {
            "status": "active",
            "message": "Ставка ещё не завершена",
        }

    with handle_price_errors():
        exit_price = fetch_price(bet.coin)

    result = bet.resolve(exit_price)

    return {
        "coin": bet.coin,
        "direction": bet.direction,
        "entry_price": bet.entry_price,
        "exit_price": exit_price,
        "status": result,
    }
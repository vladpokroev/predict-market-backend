# Predict Market — Backend

API для ставок на изменение курса криптовалют. Пользователь делает ставку на рост или падение цены монеты, через заданное время сервер сравнивает цену и определяет результат.

## Технологии

- Python
- FastAPI — веб-фреймворк для API
- httpx — HTTP-запросы к бирже Binance
- uvicorn — ASGI-сервер

## Установка

```bash
pip3 install fastapi uvicorn httpx
```

## Запуск

```bash
uvicorn main:app --reload
```

Сервер запустится на `http://127.0.0.1:8000`.
Документация API (Swagger): `http://127.0.0.1:8000/docs`

## Эндпоинты

- `GET /price/{coin}` — текущая цена монеты (например `/price/BTC`)
- `POST /bet` — создать ставку
- `GET /bets` — история ставок
- `GET /bet/{bet_id}/result` — результат ставки по её ID
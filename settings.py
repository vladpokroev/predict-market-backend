from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    binance_base_url: str
    frontend_origin: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

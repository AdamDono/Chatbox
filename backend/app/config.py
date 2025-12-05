from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Trading Bot"
    MT5_LOGIN: int = 0
    MT5_PASSWORD: str = ""
    MT5_SERVER: str = "Deriv-Server"
    
    DAILY_PROFIT_TARGET_PCT: float = 10.0
    MAX_DAILY_LOSS_PCT: float = 5.0
    STARTING_CAPITAL: float = 100.0
    
    MOCK_MODE: bool = True

    class Config:
        env_file = ".env"

settings = Settings()

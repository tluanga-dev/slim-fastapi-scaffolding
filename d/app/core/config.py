from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "SlimFastAPI"
    SQLALCHEMY_DATABASE_URI: str = "sqlite+aiosqlite:///./app.db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
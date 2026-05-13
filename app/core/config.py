from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DB
    DATABASE_URL: str

    # SMTP
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    MAIL_FROM: str
    MAIL_TO: str

    # 크롤링
    TARGET_URL: str

    # LLM
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
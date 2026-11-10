from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv
load_dotenv() 
class Settings(BaseSettings):

    # Application
    APP_NAME: str = "GapFinder AI"
    DEBUG: bool = True
    DEMO_MODE: bool = True
    DEMO_EMAIL: str = "demo@gapfinder.ai"
    DEMO_PASSWORD: str = "GapFinderDemo2026!"

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Groq
    GROQ_API_KEY: str

    # LLM
    LLM_MODEL: str = "openai/gpt-oss-120b"

    # Embedding model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Local storage
    UPLOAD_DIR: str = "storage/uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
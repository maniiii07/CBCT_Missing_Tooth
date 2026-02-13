from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # OpenAI API Key (for GPT-4o and GPT-5.2)
    OPENAI_API_KEY: str
    
    # Google Gemini API Key
    GOOGLE_API_KEY: str
    
    # Anthropic API Key
    ANTHROPIC_API_KEY: str
    
    # Model names
    GPT4O_MODEL: str
    GPT52_MODEL: str
    GEMINI_MODEL: str
    ANTHROPIC_MODEL: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

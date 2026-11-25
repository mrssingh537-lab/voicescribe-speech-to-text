from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # Provider & Model
    TRANSCRIPTION_MODE: str = "local"  # "local" or "api"
    WHISPER_MODEL: str = "turbo"  # Whisper Large-v3 Turbo
    DEVICE: str = "auto"          # "auto", "cuda", or "cpu"
    
    # API-based Transcription Provider
    TRANSCRIPTION_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    TRANSCRIPTION_API_URL: str = "https://api.openai.com/v1/audio/transcriptions"
    TRANSCRIPTION_API_MODEL: str = "whisper-1"
    TRANSCRIPTION_RESPONSE_FORMAT: Optional[str] = None
    
    # File Limits
    MAX_UPLOAD_SIZE_MB: int = 500
    
    # Optional Hugging Face Token for pyannote.audio
    HF_TOKEN: Optional[str] = None
    
    # Storage & Database
    DATABASE_URL: str = "sqlite:///./storage/voicescribe.db"
    STORAGE_DIR: Path = Path("./storage")
    UPLOAD_DIR: Path = Path("./storage/uploads")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def effective_api_key(self) -> Optional[str]:
        key = (self.TRANSCRIPTION_API_KEY or self.OPENAI_API_KEY or "").strip()
        return key if key else None


settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

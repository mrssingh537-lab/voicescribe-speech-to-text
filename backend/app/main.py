import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine, init_db
from app.routers import health, transcribe, history, settings as settings_router
from app.services.job_manager import job_manager
from app.services.providers.local_whisper import LocalWhisperProvider
from app.services.providers.api_whisper import ApiTranscriptionProvider

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("voicescribe")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize SQLite Database Tables
    logger.info("[VoiceScribe] Initializing database tables...")
    init_db()

    # 2. Instantiate Providers
    logger.info(f"[VoiceScribe] Initializing Providers (Default Mode: {settings.TRANSCRIPTION_MODE})...")
    local_provider = LocalWhisperProvider(
        model_name=settings.WHISPER_MODEL,
        device_override=settings.DEVICE
    )
    api_provider = ApiTranscriptionProvider(
        api_key=settings.effective_api_key,
        endpoint_url=settings.TRANSCRIPTION_API_URL,
        model_name=settings.TRANSCRIPTION_API_MODEL,
        response_format=settings.TRANSCRIPTION_RESPONSE_FORMAT
    )
    job_manager.set_provider(local_provider)
    job_manager.set_api_provider(api_provider)

    logger.info(
        f"[VoiceScribe] Providers configured: "
        f"Local Whisper ('{settings.WHISPER_MODEL}'), "
        f"API Provider (key_set={bool(settings.effective_api_key)}, endpoint='{settings.TRANSCRIPTION_API_URL}')"
    )

    # 3. Load local model in background task so server can immediately report health/progress
    async def load_model_async():
        loop = asyncio.get_running_loop()
        try:
            logger.info("[VoiceScribe] Pre-loading Whisper Large-v3 Turbo model into memory...")
            await loop.run_in_executor(None, local_provider.load_model)
            logger.info(
                f"[VoiceScribe] Whisper model '{local_provider.model_name}' successfully loaded "
                f"on {local_provider.device.upper()} (float{'16' if local_provider.fp16 else '32'}). Ready for jobs."
            )
        except Exception as e:
            logger.error(f"[VoiceScribe] Error pre-loading Whisper model: {e}", exc_info=True)

    asyncio.create_task(load_model_async())

    yield

    logger.info("[VoiceScribe] Server shutting down...")


app = FastAPI(
    title="VoiceScribe API",
    description="Local Speech-to-Text Conversion System powered by Whisper Large-v3 Turbo and Deep Learning.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(health.router)
app.include_router(transcribe.router)
app.include_router(history.router)
app.include_router(settings_router.router)


@app.get("/")
def root():
    return {
        "app": "VoiceScribe",
        "description": "Local Speech-to-Text Transcription Engine",
        "model": settings.WHISPER_MODEL,
        "mode": settings.TRANSCRIPTION_MODE,
        "status": "online"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)

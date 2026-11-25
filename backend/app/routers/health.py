from fastapi import APIRouter
from app.config import settings
from app.schemas import HealthResponse
from app.services.job_manager import job_manager

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    local_ready = False
    device = "unknown"
    model_name = settings.WHISPER_MODEL

    if job_manager.local_provider:
        local_info = job_manager.local_provider.get_info()
        local_ready = local_info.get("ready", False)
        device = local_info.get("device", "unknown")
        model_name = local_info.get("model_name", settings.WHISPER_MODEL)

    api_ready = False
    if job_manager.api_provider:
        api_ready = job_manager.api_provider.is_ready()

    # The active provider readiness determines if the system is ready to transcribe immediately
    is_active_ready = api_ready if settings.TRANSCRIPTION_MODE == "api" else local_ready

    return HealthResponse(
        status="ok",
        model_ready=is_active_ready,
        device=device,
        model_name=settings.TRANSCRIPTION_API_MODEL if settings.TRANSCRIPTION_MODE == "api" else model_name,
        transcription_mode=settings.TRANSCRIPTION_MODE,
        hf_diarization_available=bool(settings.HF_TOKEN),
        api_ready=api_ready,
        local_ready=local_ready,
        active_provider=settings.TRANSCRIPTION_MODE
    )

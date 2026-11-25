import os
import shutil
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status
from app.config import settings
from app.schemas import JobResponse, JobStatusResponse
from app.services.job_manager import job_manager
from app.services.audio_utils import is_audio_file, is_video_file

logger = logging.getLogger("voicescribe.routers.transcribe")
router = APIRouter(prefix="/api", tags=["transcribe"])

ALLOWED_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".wma", ".webm"}
ALLOWED_VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"}


@router.post("/transcribe", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_transcription(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_type: str = Form("audio"),
    diarize: bool = Form(False),
    language: str = Form("auto"),
    desired_language: str = Form("auto"),
    provider: Optional[str] = Form(None)
):
    """
    Submits an audio, video, or browser recording file for speech-to-text transcription.
    Supports local Whisper inference or cloud API provider.
    Returns a unique job_id for polling.
    """
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()

    # Validate file extension
    valid_ext = False
    if source_type in ("audio", "recording") and (ext in ALLOWED_AUDIO_EXTS or not ext):
        valid_ext = True
    elif source_type == "video" and (ext in ALLOWED_VIDEO_EXTS):
        valid_ext = True
    elif ext in ALLOWED_AUDIO_EXTS or ext in ALLOWED_VIDEO_EXTS:
        valid_ext = True

    if not valid_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed audio: .wav, .mp3, .m4a, .aac, .flac, .ogg. Video: .mp4, .mkv, .mov, .avi, .webm"
        )

    # Create job entry
    job_id = job_manager.create_job(
        filename=filename,
        source_type=source_type,
        diarize=diarize,
        language=language,
        desired_language=desired_language,
        provider=provider
    )

    # Secure file path
    safe_filename = f"{job_id}_{os.path.basename(filename)}"
    destination_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    # Stream file to disk and validate size
    bytes_written = 0
    max_bytes = settings.max_upload_bytes

    try:
        with open(destination_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        if os.path.exists(destination_path):
            os.remove(destination_path)
        raise
    except Exception as e:
        if os.path.exists(destination_path):
            os.remove(destination_path)
        logger.error(f"Failed to save upload {filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )

    # Schedule background processing
    background_tasks.add_task(
        job_manager.process_job,
        job_id=job_id,
        temp_input_path=destination_path,
        filename=filename,
        source_type=source_type,
        diarize=diarize,
        language=language,
        desired_language=desired_language,
        provider=provider
    )

    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Transcription job accepted and queued."
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """
    Checks the status and progress of a transcription job.
    """
    job_info = job_manager.get_job(job_id)
    if not job_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )
    return job_info

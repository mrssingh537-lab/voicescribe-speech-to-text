import os
import uuid
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.config import settings
from app.database import SessionLocal
from app.models import Transcript
from app.schemas import JobStatusResponse, TranscriptResponse, SegmentSchema
from app.services.audio_utils import standardize_audio, is_video_file
from app.services.diarization import diarization_service
from app.services.providers.base import TranscriptionProvider
from app.services.providers.local_whisper import LocalWhisperProvider
from app.services.providers.api_whisper import ApiTranscriptionProvider
from app.services.translator import is_translation_needed, translate_transcript

logger = logging.getLogger("voicescribe.job_manager")


class JobManager:
    """
    Manages asynchronous transcription jobs with concurrency locking,
    sequential queueing, progress stage updates, and SQLite persistence.
    Supports switching between local Whisper model and Cloud API provider.
    """

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self.provider: Optional[TranscriptionProvider] = None
        self.local_provider: Optional[TranscriptionProvider] = None
        self.api_provider: Optional[TranscriptionProvider] = None

    def set_provider(self, provider: TranscriptionProvider):
        """Sets the default / local provider."""
        self.provider = provider
        self.local_provider = provider

    def set_api_provider(self, provider: TranscriptionProvider):
        """Sets the cloud API transcription provider."""
        self.api_provider = provider

    def get_provider(self, mode: Optional[str] = None) -> Optional[TranscriptionProvider]:
        """Resolves active provider based on mode or global settings."""
        selected_mode = (mode or settings.TRANSCRIPTION_MODE or "local").lower().strip()
        if selected_mode == "api":
            return self.api_provider
        return self.local_provider or self.provider

    def create_job(
        self,
        filename: str,
        source_type: str,
        diarize: bool,
        language: str,
        desired_language: str = "auto",
        provider: Optional[str] = None
    ) -> str:
        job_id = str(uuid.uuid4())
        chosen_provider = (provider or settings.TRANSCRIPTION_MODE or "local").lower().strip()
        active_prov = self.get_provider(chosen_provider)
        if chosen_provider == "api":
            model_ident = getattr(active_prov, "model_name", settings.TRANSCRIPTION_API_MODEL)
        else:
            raw_model = getattr(active_prov, "model_name", settings.WHISPER_MODEL)
            model_ident = "Whisper Large-v3 Turbo" if raw_model == "turbo" else f"Whisper ({raw_model})"

        self._jobs[job_id] = {
            "job_id": job_id,
            "filename": filename,
            "source_type": source_type,
            "diarize": diarize,
            "language": language,
            "desired_language": desired_language,
            "provider": chosen_provider,
            "model_name": model_ident,
            "status": "pending",
            "stage": "uploading",
            "progress": 5,
            "result": None,
            "error": None,
            "created_at": datetime.utcnow()
        }
        return job_id

    def get_job(self, job_id: str) -> Optional[JobStatusResponse]:
        data = self._jobs.get(job_id)
        if not data:
            return None
        return JobStatusResponse(
            job_id=data["job_id"],
            status=data["status"],
            stage=data["stage"],
            progress=data["progress"],
            provider=data.get("provider"),
            model_name=data.get("model_name"),
            result=data.get("result"),
            error=data.get("error")
        )

    def update_job(self, job_id: str, **kwargs):
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)

    async def process_job(
        self,
        job_id: str,
        temp_input_path: str,
        filename: str,
        source_type: str,
        diarize: bool,
        language: str,
        desired_language: str = "auto",
        provider: Optional[str] = None
    ):
        """
        Background task worker running with a strict concurrency lock so only
        one transcription job uses inference resources at a time.
        """
        standardized_wav = None
        chosen_mode = (
            provider
            or self._jobs.get(job_id, {}).get("provider")
            or settings.TRANSCRIPTION_MODE
            or "local"
        ).lower().strip()

        logger.info(
            f"[JobManager] Job {job_id} queued for processing "
            f"(mode={chosen_mode}, desired_language={desired_language})."
        )

        async with self._lock:
            try:
                self.update_job(job_id, status="processing", stage="extracting", progress=20)
                logger.info(f"[JobManager] Job {job_id} processing: extracting audio...")

                standardized_wav = os.path.join(
                    settings.UPLOAD_DIR,
                    f"std_{job_id}_{os.path.splitext(filename)[0]}.wav"
                )

                # Run audio extraction and standardization in thread pool
                loop = asyncio.get_running_loop()
                audio_info = await loop.run_in_executor(
                    None,
                    standardize_audio,
                    temp_input_path,
                    standardized_wav
                )
                duration = audio_info["duration"]

                # Resolve provider based on requested/configured mode
                active_provider = self.get_provider(chosen_mode)
                if not active_provider:
                    raise RuntimeError(f"No transcription provider available for mode '{chosen_mode}'.")

                if not active_provider.is_ready():
                    if chosen_mode == "api":
                        raise RuntimeError(
                            "Cloud API Transcription provider is not configured. "
                            "Please set TRANSCRIPTION_API_KEY in backend/.env or in Settings."
                        )
                    else:
                        raise RuntimeError("Local Whisper model is not initialized or ready.")

                mode_label = "Cloud API" if chosen_mode == "api" else "Local Whisper"
                if chosen_mode == "api":
                    model_ident = getattr(active_provider, "model_name", settings.TRANSCRIPTION_API_MODEL)
                else:
                    raw_model = getattr(active_provider, "model_name", settings.WHISPER_MODEL)
                    model_ident = "Whisper Large-v3 Turbo" if raw_model == "turbo" else f"Whisper ({raw_model})"
                self.update_job(job_id, provider=chosen_mode, model_name=model_ident, stage="transcribing", progress=45)
                logger.info(f"[JobManager] Job {job_id} processing: transcribing with {mode_label} ({model_ident})...")

                whisper_result = await loop.run_in_executor(
                    None,
                    active_provider.transcribe,
                    standardized_wav,
                    language,
                    desired_language,
                    False  # word_timestamps
                )

                segments = whisper_result.segments
                detected_language = whisper_result.language
                full_text = whisper_result.text

                # Normalize detected language if unknown / auto
                if detected_language in ("unknown", "auto", None, ""):
                    if language and language != "auto":
                        detected_language = language
                    elif full_text and all(ord(c) < 128 for c in full_text[:200]):
                        detected_language = "en"

                # Stage: Diarization (if requested)
                if diarize:
                    self.update_job(job_id, stage="diarizing", progress=80)
                    logger.info(f"[JobManager] Job {job_id} processing: identifying speakers...")
                    segments = await loop.run_in_executor(
                        None,
                        diarization_service.diarize_segments,
                        standardized_wav,
                        segments
                    )

                # Stage: Translation (if desired output language is specified and different)
                if is_translation_needed(detected_language, desired_language):
                    self.update_job(job_id, stage="translating", progress=85)
                    logger.info(
                        f"[JobManager] Job {job_id} translating from '{detected_language}' "
                        f"to desired language '{desired_language}'..."
                    )
                    try:
                        segments, full_text = await loop.run_in_executor(
                            None,
                            translate_transcript,
                            segments,
                            full_text,
                            detected_language,
                            desired_language
                        )
                        logger.info(f"[JobManager] Job {job_id} translation completed successfully.")
                    except Exception as te:
                        logger.warning(
                            f"[JobManager] Job {job_id} translation failed: {te}. "
                            f"Continuing with original transcription.",
                            exc_info=True
                        )

                # Format segments for DB and response
                formatted_segments = []
                for idx, seg in enumerate(segments, 1):
                    formatted_segments.append({
                        "id": idx,
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text,
                        "speaker": seg.speaker
                    })

                # Save transcript into SQLite database
                self.update_job(job_id, stage="saving", progress=95)
                db = SessionLocal()
                try:
                    db_transcript = Transcript(
                        filename=filename,
                        source_type=source_type,
                        is_diarized=diarize,
                        language=detected_language,
                        desired_language=desired_language,
                        duration=duration,
                        text=full_text,
                        segments_json=json.dumps(formatted_segments),
                        model_name=whisper_result.model_name
                    )
                    db.add(db_transcript)
                    db.commit()
                    db.refresh(db_transcript)
                    created_at = db_transcript.created_at
                    transcript_id = db_transcript.id
                finally:
                    db.close()

                result_response = TranscriptResponse(
                    id=transcript_id,
                    filename=filename,
                    source_type=source_type,
                    is_diarized=diarize,
                    language=detected_language,
                    desired_language=desired_language,
                    duration=duration,
                    text=full_text,
                    segments=[SegmentSchema(**s) for s in formatted_segments],
                    created_at=created_at,
                    model_name=whisper_result.model_name
                )

                self.update_job(
                    job_id,
                    status="completed",
                    stage="done",
                    progress=100,
                    result=result_response
                )
                logger.info(f"[JobManager] Job {job_id} completed successfully (Transcript ID: {transcript_id}).")

            except Exception as e:
                logger.error(f"[JobManager] Job {job_id} failed: {e}", exc_info=True)
                self.update_job(
                    job_id,
                    status="failed",
                    stage="failed",
                    progress=100,
                    error=str(e)
                )
            finally:
                # Cleanup temporary files
                for fpath in [temp_input_path, standardized_wav]:
                    if fpath and os.path.exists(fpath):
                        try:
                            os.remove(fpath)
                            logger.debug(f"[JobManager] Cleaned up temporary file: {fpath}")
                        except OSError as ce:
                            logger.warning(f"[JobManager] Could not remove temp file {fpath}: {ce}")


job_manager = JobManager()

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SegmentSchema(BaseModel):
    id: Optional[int] = None
    start: float
    end: float
    text: str
    speaker: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TranscriptResponse(BaseModel):
    id: int
    filename: str
    source_type: str
    is_diarized: bool
    language: str
    desired_language: Optional[str] = "auto"
    duration: float
    text: str
    segments: List[SegmentSchema] = []
    created_at: datetime
    model_name: Optional[str] = "Whisper Turbo (Local)"

    model_config = ConfigDict(from_attributes=True)


class TranscriptListItem(BaseModel):
    id: int
    filename: str
    source_type: str
    is_diarized: bool
    language: str
    desired_language: Optional[str] = "auto"
    duration: float
    text_preview: str
    created_at: datetime
    model_name: Optional[str] = "Whisper Turbo (Local)"

    model_config = ConfigDict(from_attributes=True)


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    stage: str   # "uploading", "extracting", "transcribing", "diarizing", "done"
    progress: int  # 0 to 100
    provider: Optional[str] = None
    model_name: Optional[str] = None
    result: Optional[TranscriptResponse] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_ready: bool
    device: str
    model_name: str
    transcription_mode: str
    hf_diarization_available: bool
    api_ready: bool = False
    local_ready: bool = False
    active_provider: str = "local"


class SettingsResponse(BaseModel):
    transcription_mode: str
    api_key_configured: bool
    api_key_masked: str
    api_url: str
    api_model: str
    response_format: Optional[str] = None
    local_model: str
    device: str
    local_ready: bool
    api_ready: bool


class SettingsUpdateRequest(BaseModel):
    transcription_mode: Optional[str] = None  # "local" or "api"
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    api_model: Optional[str] = None
    response_format: Optional[str] = None


class ApiTestResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None
